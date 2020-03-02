#!/usr/bin/env python
# coding: utf-8

import json
import time
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy.integrate as integrate
from functools import reduce

import nrm.tooling as nrm
import experiment

experimentSamplingSize = 3
powerCapRanges = [60,70,80,90,100,110,130 ,150, 180, 210]
staticPower = 200000000
referenceMeasurementRoundInterval = 10

daemonCfgs = {}

for i in range(0, experimentSamplingSize):
    for cap in powerCapRanges:
        daemonCfgs[(i, "pcap" + str(cap))] = {
            "controlCfg": {"fixedPower": {"fromuW": cap * 1000000}}
        }
    daemonCfgs[(i, "controlOn")] = {
            "controlCfg": {
                "staticPower": {"fromuW": staticPower},
                "referenceMeasurementRoundInterval": referenceMeasurementRoundInterval,
                "learnCfg": {"lagrangeConstraint": 1},
                "speedThreshold": 0.9,
                "minimumControlInterval": {"fromuS": 1000000},
            },
            "raplCfg": {
                "raplActions": [{"fromuW": 1000000 * p} for p in powerCapRanges],
                "raplFrequency": {"fromHz": 1},
                "raplPath": "/sys/devices/virtual/powercap/intel-rapl",
            }
        }


def perfwrapped(cmd, args):
    return [
        {
            "cmd": cmd,
            "args": args,
            "sliceID": "toto",
            "manifest": {
                "app": {
                    "slice": {"cpus": 1, "mems": 1},
                    "perfwrapper": {
                        "perfLimit": {"fromOps": 100000},
                        "perfFreq": {"fromHz": 1},
                    },
                },
                "name": "perfwrap",
            },
        }
    ]


stream = perfwrapped("stream_c", [])

lammps = perfwrapped(
    "mpiexec",
    ["-n", "24", "amg", "-problem", "2", "-n", "90", "90", "90", "-P", "2", "12", "1"],
)


host = nrm.Local()
results = {}
for key, cfg in daemonCfgs.items():
    results[key] = experiment.do_workload(host, cfg, stream)

import pickle
f = open("dict.pkl","wb")
pickle.dump(results,f)
f.close()

result_df = pd.concat(
    [experiment.history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("dev/hnrm-experiments/bandits/internal-control-experiments.csv")

