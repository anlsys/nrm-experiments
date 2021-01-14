#!/bin/bash

# extra-tools.sh: extra software useful when preparing experiments
#
# authors: Raphaël Bleuse <raphael.bleuse@inria.fr>
# date: 2021-01-11
# version: 0.1

export LC_ALL=C  # ensure we are working with known locales
set -e -u -f -o pipefail # safer shell script


declare -ra EXTRA_APT_PKGS=(
	cpufrequtils
	htop
	hwloc
	python3-pip
	python3-wheel
)
declare -ra EXTRA_PY_PKGS=(
	's-tui==1.0.2'  # prefer over Debian-packaged version (it show RAPL packages info)
)


apt-get update
apt-get --assume-yes --show-progress install "${EXTRA_APT_PKGS[@]}"
python3 -m pip install --system --upgrade ${EXTRA_PY_PKGS[@]}""
