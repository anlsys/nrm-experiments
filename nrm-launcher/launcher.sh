#!/usr/bin/env bash

######## Only modify this variable to switch between benchmarks ###########
dir=~/Argonne/nrm-experiments/mpi
bench=copy
############################################################################

nrmd_conf=nrmd_conf.json
pcap=85
LOGDIR=.
cmd_manifest=manifest.json
LOGFILE=logs.log

echo "nrmd nrmd_conf.json"
#nrmd $nrmd_conf &>/dev/null &
nrmd $nrmd_conf  &
echo "Done"
nrmd_pid=$!

echo "Actuate"
# actually actuate the power cap
nrm actuate "RaplKey (PackageID 0)" $pcap
#nrm actuate "RaplKey (PackageID 1)" $pcap
echo "Done"

# listen to measurements from nrmd
nrm listen-all & > $LOGDIR/$pcap.log

# launch the benchmark and wait for exit
nrm run --manifest $cmd_manifest -- ones-stream-$bench 100 10 2>&1 >> $LOGFILE
#nrm run --manifest $cmd_manifest -- mpirun -np 2 $dir/a.out 2>&1 >> $LOGFILE

# kill the daemon
kill -9 $nrmd_pid

