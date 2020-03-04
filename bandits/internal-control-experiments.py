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

# experimentSamplingSize = 1
experimentSamplingRange = range(1, 2)
powerCapRanges = [
        [
            nrm.Action("RaplKey (PackageID 0)", p0),
            nrm.Action("RaplKey (PackageID 1)", p1)
            ]
        for p0,p1 in [(70,70),(210,70),(70,210),(210,210)]
        ]
# powerCapRanges = [150, 80]
staticPower = 200000000
referenceMeasurementRoundInterval = 10

daemonCfgs = {}

for i in experimentSamplingRange:
    for caps in powerCapRanges,:
        daemonCfgs[(i, "pcap" + str(caps))] = (caps,{
            "controlCfg": {"fixedPower": {"fromuW": 1000000}}
        })
    daemonCfgs[(i, "controlOn")] = (None,{
        "controlCfg": {
            "staticPower": {"fromuW": staticPower},
            "referenceMeasurementRoundInterval": referenceMeasurementRoundInterval,
            "learnCfg": {"lagrangeConstraint": 1},
            "speedThreshold": 1.1,
            "minimumControlInterval": {"fromuS": 1000000},
        },
        "raplCfg": {
            "raplActions": [{"fromuW": 1000000 * p} for p in powerCapRanges],
            "raplFrequency": {"fromHz": 1},
            "raplPath": "/sys/devices/virtual/powercap/intel-rapl",
        },
        "verbose" : "Info"
    })

stream = experiment.perfwrapped("stream_c", [])

lammps = experiment.perfwrapped(
    "mpiexec",
    ["-n", "24", "amg", "-problem", "2", "-n", "90", "90", "90", "-P", "2", "12", "1"],
)


host = nrm.Local()
results = {}
for key, expe in daemonCfgs.items():
    baseAction, cfg = expe
    results[key] = experiment.do_workload(host, baseAction, cfg, stream)

import pickle

result_df = pd.concat(
    [experiment.history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("internal-control-experiments.csv")
