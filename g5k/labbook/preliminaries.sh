#!/bin/bash

# preliminaries.sh: Preliminary measures script for STREAM benchmark
#
# -----------------------------------------------------------------------------
#
# Runs preliminary experiments: measure a single datapoint for various powercap
# settings.
# In particular, we do not take care of minimizing any bias due to the order in
# which benchmarks are run, or due to the machine, or …
#
# -----------------------------------------------------------------------------
#
# authors: Raphaël Bleuse <raphael.bleuse@inria.fr>
# date: 2020-11-20
# version: 0.1

export LC_ALL=C  # ensure we are working with known locales
set -e -u -f -o pipefail # safer shell script


# parameters  -----------------------------------------------------------------

declare -r BENCHMARK='stream_c'
declare -r ITERATION_COUNT='10_000'
declare -r PROBLEM_SIZE='33_554_432'

declare -a POWERCAPS
mapfile -t POWERCAPS < <(seq 30 10 150 | shuf)  # seq <min> <step> <max>


# configuration  --------------------------------------------------------------

declare -r LOGDIR='/tmp'  # all relative paths are relative to $LOGDIR
declare -r DATADIR='/tmp/experiments-data'

declare -r PARAMS_FILE='parameters.yaml'


# files to snapshot before running the experiment
declare -ra PRERUN_SNAPSHOT_FILES=(
	"${PARAMS_FILE}"
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
	nrm.log
)

# helper functions  -----------------------------------------------------------

function dump_parameters {
	declare -r timestamp="${1}"
	declare -r benchmark="${2}"
	declare -r powercap="${3}"
	declare -r extra="${*:4}"

	cat <<- EOF > "${LOGDIR}/${PARAMS_FILE}"
		timestamp: ${timestamp}
		benchmark: ${benchmark}
		powercap: ${powercap}
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
	for powercap in "${POWERCAPS[@]}"; do
		timestamp="$(date --iso-8601=seconds)"
		archive="${DATADIR}/preliminaries_${BENCHMARK}_${timestamp}.tar"

		# record run parameters
		dump_parameters "${timestamp}" "${BENCHMARK}" "${powercap}" "--iterationCount=${ITERATION_COUNT} --problemSize=${PROBLEM_SIZE}"

		# create empty archive
		tar --create --file="${archive}" --files-from=/dev/null

		# snapshot pre-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${PRERUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'pre'

		# run benchmark
		/opt/xplaunch static-gain --powercap="${powercap}" -- \
			"${BENCHMARK}" --iterationCount="${ITERATION_COUNT}" --problemSize="${PROBLEM_SIZE}"

		# retrieve benchmark logs and snapshot post-run state
		tar --append --file="${archive}" --directory="${LOGDIR}" -- "${POSTRUN_SNAPSHOT_FILES[@]}"
		snapshot_system_state "${archive}" 'post'

		# compress archive
		xz --compress "${archive}"
	done
}


# run  ------------------------------------------------------------------------

# ensure output directory exists
mkdir --parents "${DATADIR}"

# do the work
run
