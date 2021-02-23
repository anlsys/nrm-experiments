#/usr/bin/env bash
set -m
while true
echo $BASHPID > pid
do
  export CUDA_VISIBLE_DEVICES=0
  echo "running workload on CPU"
  python ~/Benchmarks/Pilot1/NT3/nt3_baseline_keras2.py --epochs 1 &
  PID=$!
  function f {
    echo 'Signal received: killing $PID'
    kill -s SIGINT $PID
  }
  trap f USR1
  wait $PID
  export CUDA_VISIBLE_DEVICES=1
  echo "running workload on GPU"
  python ~/Benchmarks/Pilot1/NT3/nt3_baseline_keras2.py --epochs 1 &
  PID=$!
  function f {
    echo 'Signal received: killing $PID'
    kill -s SIGINT $PID
  }
  trap f USR1
  wait $PID
done
