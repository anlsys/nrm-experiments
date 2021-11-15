#!/bin/sh
# make sure we stop on errors, and log everything
set -e
set -x
set -u

DELIMITER="################################################################################\n"
delim2() { echo -e "\n$DELIMITER$DELIMITER"; }
delim() { echo -e "\n$DELIMITER"; }
record_file()  {
	echo "$1 CONTENTS" >> $LOGFILE
	delim2 >> $LOGFILE
	cat $1 >> $LOGFILE
	delim2 >> $LOGFILE
}


DATE=`date +%Y%m%d.%H%M%S`
LOGDIR="results-$DATE"
LOGFILE="$LOGDIR/$DATE.log"
mkdir -p $LOGDIR
echo "Start: $DATE" >> $LOGFILE

# remember this script in the log
record_file $0

# remember our nix infrastructure
record_file ./default.nix
record_file ./shell.nix
for f in nix/*.nix; do
	record_file $f
done

# Gather some info on the system
uname -a >> $LOGFILE
cat /proc/cmdline >> $LOGFILE
lscpu >> $LOGFILE

delim >> $LOGFILE

# runtime info
env >> $LOGFILE
ulimit -n 4096
ulimit -a >> $LOGFILE

delim2 >> $LOGFILE

# generate the right command config
cmd_manifest=$LOGDIR/cmd_manifest.json
cat <<ENDFILE > $cmd_manifest
{
    "name": "default",
    "app": {
	"perfwrapper": {
	    "perfLimit": 100000,
	    "perfFreq": {"hertz": 10},
	    "perfEvent" : "instructions"
	}
    }
}
ENDFILE

# mesure several static power caps
for pcap in 70 80 90 100 110; do

	# generate the right daemon config
	pcap_uw=$((70 * 1000000))
	nrmd_conf=$LOGDIR/nrmd_$pcap.json
	nrmd_log=$LOGDIR/nrmd_$pcap.log
	cat << ENDFILE > $nrmd_conf
{
    "verbose": "Info",
    "logfile": "$nrmd_log",
    "controlCfg": "ControlOff",
    "raplCfg": {
        "referencePower": {
            "microwatts": 250000000
        },
        "raplActions": [
            {
                "microwatts": $pcap_uw
            }
        ],
        "raplPath": "/sys/devices/virtual/powercap/intel-rapl"
    },
    "passiveSensorFrequency": {
        "hertz": 1
    }
}
ENDFILE
	
	# launch nrmd, we don't need output as it's logged already
	nrmd $nrmd_conf &>/dev/null &
	nrmd_pid=$!

	# actually actuate the power cap
	nrm actuate "RaplKey (PackageID 0)" $pcap
	nrm actuate "RaplKey (PackageID 1)" $pcap

	# listen to measurements from nrmd
	nrm listen-all & > $LOGDIR/$pcap.log

	# launch the benchmark and wait for exit
	nrm run --manifest $cmd_manifest -- ls -al 2>&1 >> $LOGFILE

	# kill the daemon
	kill -9 $nrmd_pid	
done

DONEDATE=`date +%Y%m%d.%H%M%S`
echo "Done: $DONEDATE" >> $LOGFILE
