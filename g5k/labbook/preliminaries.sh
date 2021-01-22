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
# date: 2021-01-22
# version: 0.2

export LC_ALL=C  # ensure we are working with known locales
set -e -u -f -o pipefail # safer shell script

declare -r PROGRAM=${0##*/}


# parameters  -----------------------------------------------------------------

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

# files to snapshot once the experiment is done
declare -ra POSTRUN_SNAPSHOT_FILES=(
	# outputs
	dump_pubMeasurements.csv
	dump_pubProgress.csv
	identification-runner.log
	nrm.log
)

# helper functions  -----------------------------------------------------------

function dump_parameters {
	declare -r timestamp="${1}"
	declare -r benchmark="${2}"
	declare -r plan="${3}"
	declare -r extra="${*:4}"

	cat <<- EOF > "${LOGDIR}/${PARAMS_FILE}"
		timestamp: ${timestamp}
		benchmark: ${benchmark}
		experiment-plan: ${plan##*/}
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
	# canonicalize path to experiment plans
	local input
	input="$(readlink --canonicalize-existing "${1}")"
	readonly input

	# extract experiment plans to run
	declare -a experiment_plans
	if [[ -d "${input}" ]]; then
		mapfile -t experiment_plans < <(find "${input}" -maxdepth 1 -type f | shuf)
	elif [[ -f "${input}" && -r "${input}" ]]; then
		experiment_plans=("${input}")
	else
		usage
		>&2 cat <<-EOF

		Error: invalid INPUT argument
		EOF
		exit 64  # EX_USAGE (cf. sysexits.h)
	fi
	readonly experiment_plans

	# run experiment plans
	for plan in "${experiment_plans[@]}"; do
		timestamp="$(date --iso-8601=seconds)"
		archive="${DATADIR}/preliminaries_${BENCHMARK}_${timestamp}.tar"

		# record run parameters
		dump_parameters "${timestamp}" "${BENCHMARK}" "${plan}" "--iterationCount=${ITERATION_COUNT} --problemSize=${PROBLEM_SIZE}"

		# record machine topology
		lstopo --output-format xml --whole-system --force "${LOGDIR}/${TOPOLOGY_FILE}"

		# create empty archive
		tar --create --file="${archive}" --files-from=/dev/null

		# snapshot pre-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${PRERUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'pre'

		# run benchmark
		xpctl identification --experiment-plan="${plan}" -- \
			"${BENCHMARK}" --iterationCount="${ITERATION_COUNT}" --problemSize="${PROBLEM_SIZE}"

		# retrieve benchmark logs and snapshot post-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${POSTRUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'post'

		# compress archive
		xz --compress "${archive}"
	done
}


function usage() {
	>&2 cat <<-EOF
	Usage: ${PROGRAM} INPUT

	Parameters:
	  INPUT        Either:
	                 - a single experiment plan (readable file)
	                 - directory containing multiple experiment plans
	EOF
}

# run  ------------------------------------------------------------------------

# ensure output directory exists
mkdir --parents "${DATADIR}"

# check provided arugments
if [[ $# -lt 1 ]]; then
	usage
	>&2 cat <<-EOF

	Error: missing INPUT argument
	EOF
	exit 64  # EX_USAGE (cf. sysexits.h)
fi

# do the work
run "$1"
