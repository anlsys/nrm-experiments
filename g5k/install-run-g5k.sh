#!/bin/bash

export LC_ALL=C  # ensure we are working with known locales
set -e -u -f -o pipefail # safer shell script


# ----- CONFIGURATION -----

declare -r -a PACKAGES=(
curl
git
sudo
time
)

declare -r NIX_USER='exp-runner'
declare -r NIX_MAXJOBS=6

declare -r HNRM_GIT_REPOSITORY_URL='https://xgitlab.cels.anl.gov/argo/hnrm.git'
declare -r HNRM_GIT_BRANCH='master'
declare -r HNRM_BASEDIR="/opt/hnrm"

declare -r -a NRMD_CAPABILITIES=(
CAP_DAC_OVERRIDE  # rapl (/sys/devices/virtual/powercap/*)
)

# ----- FUNCTIONS -----

# -- helpers --

_ensure_uid() {
	# ensure we run as ${1} user
	if [ ! "$(id --user)" -eq "$(id --user "${1}" 2>/dev/null)" ] ; then
		>&2 echo "expected to run as '${1}' user"
		exit 1
	fi
}

_log() {
	TERM_WARN=$(tput bold ; tput setaf 1)
	TERM_RESET=$(tput sgr0)

	echo >&2 "${TERM_WARN}${1}${TERM_RESET}"
}


# -- [STEP] environment installation --

ensure_rapl() {
	# ensure RAPL is active on the node
	if ! { lsmod | grep --quiet -- intel_rapl ; } ; then
		>&2 echo 'Unable to find RAPL.'
		exit 2
	fi
}

install_dependencies() {
	apt install --yes "${PACKAGES[@]}"
}

install_nix() {
	# create a user for Nix (Nix cannot be installed as root)
	adduser --quiet --disabled-password --gecos "${NIX_USER}" "${NIX_USER}"
	adduser "${NIX_USER}" sudo

	# allow use of sudo without password
	echo '%sudo   ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/hnrm
	chmod 0440 /etc/sudoers.d/hnrm
	visudo --check --quiet

	# install Nix with the created user
	runuser "${NIX_USER}" --login --command 'sh <(curl https://nixos.org/nix/install) --no-daemon'
}

configure_nix() {
	nixcores=$(($(nproc) / NIX_MAXJOBS))
	mkdir --parents /etc/nix
	cat > /etc/nix/nix.conf <<-CONF
		cores = ${nixcores}
		max-jobs = ${NIX_MAXJOBS}
	CONF
}

create_hnrm_basedir() {
	mkdir "${HNRM_BASEDIR}"
	chown "${NIX_USER}:${NIX_USER}" "${HNRM_BASEDIR}"
}

envinstall() {
	_log envinstall

	_ensure_uid root
	ensure_rapl

	install_dependencies
	install_nix
	configure_nix
	create_hnrm_basedir
}


# -- [STEP] hnrm installation --

install_hnrm() {
	# check hnrm README for installation procedure
	git clone \
		--recurse-submodules \
		--branch="${HNRM_GIT_BRANCH}" -- \
		"${HNRM_GIT_REPOSITORY_URL}" "${HNRM_BASEDIR}"

	# trigger build of Nix environment
	cd "${HNRM_BASEDIR}"
	command time --verbose nix-shell --run 'exit'
}

hnrminstall() {
	_log hnrminstall

	_ensure_uid "${NIX_USER}"
	command -v nix >/dev/null 2>&1  # ensure Nix is activated

	install_hnrm
}


# -- [STEP] post installation (patch hnrm binaries, set capabilities, …) --

set_capabilities() {
	# give Python interpreter required capabilities
	pythoninterpreter="$(runuser "${NIX_USER}" --login <<-CMD
		cd "${HNRM_BASEDIR}"
		nix-shell --run 'realpath "\$(command -v python)"' 2>/dev/null
	CMD
	)"
	chown root:root "${pythoninterpreter}"
	setcap "$(IFS=',' ; echo "${NRMD_CAPABILITIES[*]}+eip")" "${pythoninterpreter}"
}

postinstall() {
	_log postinstall

	_ensure_uid root

	set_capabilities
}


# -- [STEP] hnrm run --

run_jupyter() {
	nix-shell --run 'jupyter-notebook --no-browser --ip="0.0.0.0"'
}

hnrmrun() {
	_log hnrmrun

	_ensure_uid "${NIX_USER}"
	command -v nix >/dev/null 2>&1  # ensure Nix is activated

	cd "${HNRM_BASEDIR}"
	run_jupyter
}


# ----- SCRIPT -----

# The script calls itself recursively, and progresses through 4 steps (where
# steps with a star run as root (e.g., *envinstall):
#
# *envinstall > hnrminstall > *postinstall > hnrmrun
#
# - envinstall
#     run as root, it installs all dependencies (mainly Nix)
# - hnrminstall
#     run as the nix-user, it installs hnrm
# - postinstall
#     run as root, it patches installed binaries, set capabilities, …
# - hnrmrun
#     run as nix-user, it runs hnrm
#
# ----------
#
# To run the script:
#   - install in a directory accessible by both root and nix-user (typically /opt)
#   - call the script without any argument as root

PROGRAM="$(realpath "${0}")"
step="${1:-envinstall}"

case "${step}" in
	envinstall)
		envinstall
		runuser "${NIX_USER}" --login --command "${PROGRAM} hnrminstall"
		postinstall
		runuser "${NIX_USER}" --login --command "${PROGRAM} hnrmrun"
		;;
	hnrminstall)
		hnrminstall
		;;
	hnrmrun)
		hnrmrun
		;;
	*)
		>&2 echo "unknown step '${step}"
		exit 1
		;;
esac
