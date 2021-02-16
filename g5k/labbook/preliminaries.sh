#!/bin/bash

# preliminaries.sh: Preliminary measures script for STREAM benchmark
#
# -----------------------------------------------------------------------------
#
# Runs preliminary experiments: measure a single datapoint for various
# experiment plans.
# In particular, we do not take care of minimizing any bias due to the order in
# which benchmarks are run, or due to the machine, or …
#
# -----------------------------------------------------------------------------
#
# authors: Raphaël Bleuse <raphael.bleuse@inria.fr>
# date: 2021-02-16
# version: 0.4

export LC_ALL=C  # ensure we are working with known locales
set -e -u -f -o pipefail # safer shell script

declare -r PROGRAM=${0##*/}


# parameters  -----------------------------------------------------------------

# xpctl subcommand for each supported runner
declare -rA RUNNERS=(
	[controller]="controller --controller-configuration"
	[identification]="identification --experiment-plan"
)

declare -r BENCHMARK='stream_c'
declare -r ITERATION_COUNT='10_000'
declare -r PROBLEM_SIZE='33_554_432'


# configuration  --------------------------------------------------------------

declare -r LOGDIR='/tmp'  # all relative paths are relative to $LOGDIR
declare -r DATADIR='/tmp/experiments-data'

declare -r PARAMS_FILE='parameters.yaml'
declare -r TOPOLOGY_FILE='topology.xml'


# files to snapshot before running the experiment
declare -ra PRERUN_SNAPSHOT_FILES=(
	"${PARAMS_FILE}"
	"${TOPOLOGY_FILE}"
)

# pseudo-files from /proc to record
declare -ra SYSTEM_STATE_SNAPSHOT_FILES=(
	/proc/cpuinfo
	/proc/iomem
	/proc/loadavg
	/proc/meminfo
	/proc/modules
	/proc/stat
	/proc/sys/kernel/hostname
	/proc/uptime
	/proc/version
	/proc/vmstat
	/proc/zoneinfo
)

# common (i.e., shared by runners) files to snapshot once the experiment is done
declare -a POSTRUN_SNAPSHOT_FILES=(
	# outputs
	dump_pubMeasurements.csv
	dump_pubProgress.csv
	nrm.log
	time-metrics.csv
)

# runner-specific files to snapshot once the experiment is done
declare -rA RUNNERS_POSTRUN_SNAPSHOT_FILES=(
	[controller]="controller-runner.log"
	[identification]="identification-runner.log"
)

# helper functions  -----------------------------------------------------------

function dump_parameters {
	declare -r timestamp="${1}"
	declare -r runner="${2}"
	declare -r cfg="${3}"
	declare -r benchmark="${4}"
	declare -r extra="${*:5}"

	cat <<- EOF > "${LOGDIR}/${PARAMS_FILE}"
		timestamp: ${timestamp}
		runner: ${runner}
		config-file: ${cfg##*/}
		benchmark: ${benchmark}
		extra: ${extra}
	EOF
}


function snapshot_system_state {
	archive="${1}"
	subdir="${2}"

	# create unique namespace to work with
	wd=$(mktemp --directory)
	mkdir "${wd}/${subdir}"

	# snapshot
	for pseudofile in "${SYSTEM_STATE_SNAPSHOT_FILES[@]}"; do
		saveas="$(basename "${pseudofile}")"
		cat "${pseudofile}" > "${wd}/${subdir}/${saveas}"
	done

	# archive
	tar --append --file="${archive}" --directory="${wd}" --transform='s,^,sysstate/,' -- "${subdir}"

	# clean unique namespace
	rm --recursive --force -- "${wd}"
}


function run {
	declare -r runner="${1}"
	declare -r input="${2}"

	# extract xpctl subcommand
	read -r -a runner_cmd <<< "${RUNNERS[${runner}]}"
	readonly runner_cmd

	# append list of runner-specific files to snapshot to POSTRUN_SNAPSHOT_FILES
	read -r -a extra_snapshot_files <<< "${RUNNERS_POSTRUN_SNAPSHOT_FILES[${runner}]}"
	POSTRUN_SNAPSHOT_FILES+=("${extra_snapshot_files[@]}")
	unset -v extra_snapshot_files
	readonly POSTRUN_SNAPSHOT_FILES

	# extract list of configurations to execute
	declare -a configs
	if [[ -d "${input}" ]]; then
		mapfile -t configs < <(find "${input}" -maxdepth 1 -type f | shuf)
	elif [[ -f "${input}" && -r "${input}" ]]; then
		configs=("${input}")
	else
		usage
		>&2 cat <<-EOF

		Error: invalid INPUT argument
		EOF
		exit 64  # EX_USAGE (cf. sysexits.h)
	fi
	readonly configs

	# run each configuration
	for cfg in "${configs[@]}"; do
		timestamp="$(date --iso-8601=seconds)"
		archive="${DATADIR}/preliminaries_${BENCHMARK}_${timestamp}.tar"

		# record run parameters
		dump_parameters "${timestamp}" "${runner}" "${cfg}" "${BENCHMARK}" "--iterationCount=${ITERATION_COUNT} --problemSize=${PROBLEM_SIZE}"

		# record machine topology
		lstopo --output-format xml --whole-system --force "${LOGDIR}/${TOPOLOGY_FILE}"

		# create empty archive
		tar --create --file="${archive}" --files-from=/dev/null

		# record configuration file
		tar --append --file="${archive}" --transform='s,^.*/,,' -- "${cfg}"

		# snapshot pre-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${PRERUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'pre'

		# run benchmark
		if xpctl "${runner_cmd[@]}" "${cfg}" -- \
			"${BENCHMARK}" --iterationCount="${ITERATION_COUNT}" --problemSize="${PROBLEM_SIZE}"
		then
			# identify execution as successful
			touch "${LOGDIR}/SUCCESS"
			tar --append --file="${archive}" --directory="${LOGDIR}" -- SUCCESS
		else
			# identify execution as failed
			touch "${LOGDIR}/FAIL"
			tar --append --file="${archive}" --directory="${LOGDIR}" -- FAIL
		fi

		# retrieve benchmark logs and snapshot post-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${POSTRUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'post'

		# compress archive
		xz --compress "${archive}"
	done
}


function usage() {
	>&2 cat <<-EOF
	Usage: ${PROGRAM} RUNNER INPUT

	Parameters:
	  RUNNER       xpctl runner (controller, identification)
	  INPUT        Either:
	                 - a single configuration file (readable file)
	                 - a directory containing multiple configuration files
	EOF
}

# run  ------------------------------------------------------------------------

# ensure output directory exists
mkdir --parents "${DATADIR}"

# check number of provided arguments
if [[ $# -lt 2 ]]; then
	usage
	>&2 cat <<-EOF

	Error: missing argument
	EOF
	exit 64  # EX_USAGE (cf. sysexits.h)
fi

# check RUNNER is supported
if [[ ! "${RUNNERS[${1}]-}" ]]; then
	usage
	>&2 cat <<-EOF

	Error: unknown runner "${1}"
	EOF
	exit 64  # EX_USAGE (cf. sysexits.h)
fi

# do the work
run "${1}" "$2"
