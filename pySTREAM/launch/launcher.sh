#!/bin/bash

######## Only modify this variable to switch between benchmarks ###########
bench=copy
############################################################################

pyPATH=../$bench/
nrmd_conf=nrmd_conf.json
pcap=150
LOGDIR=.
cmd_manifest=manifest.json
LOGFILE=logs.log

nrmd $nrmd_conf &>/dev/null &
nrmd_pid=$!

# actually actuate the power cap
nrm actuate "RaplKey (PackageID 0)" $pcap
nrm actuate "RaplKey (PackageID 1)" $pcap

# listen to measurements from nrmd
nrm listen-all & > $LOGDIR/$pcap.log

# launch the benchmark and wait for exit
#nrm run --manifest $cmd_manifest -- ls -al 2>&1 >> $LOGFILE
nrm run --manifest $cmd_manifest -- python $pyPATH/main.py 2>&1 >> $LOGFILE

# kill the daemon
kill -9 $nrmd_pid

