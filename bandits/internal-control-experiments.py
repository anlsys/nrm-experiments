#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import random
import nrm.tooling as nrm
import experiment

# experimentSamplingSize = 1
experimentSamplingRange = range(0, 4)
powerCapRanges = [70, 250]
actionLists = [
    [nrm.Action("RaplKey (PackageID 0)", p0), nrm.Action("RaplKey (PackageID 1)", p1)]
    for p0, p1 in [(250, 250), (250, 70), (70, 250), (70, 70)]
]
# powerCapRanges = [150, 80]
staticPower = 200000000
referenceMeasurementRoundInterval = 10

raplCfg = {
    "raplActions": [{"fromuW": 1000000 * p} for p in powerCapRanges],
    "raplFrequency": {"fromHz": 1},
    "raplPath": "/sys/devices/virtual/powercap/intel-rapl",
}

daemonCfgs = {}

for i in experimentSamplingRange:
    for actions in actionLists:
        daemonCfgs[(i, "pcap" + experiment.ActionsShorthandDescription(actions))] = (
            actions,
            {
                "controlCfg": {"fixedPower": {"fromuW": 1000000}},
                "raplCfg": raplCfg,
                "verbose": "Info",
            },
        )
    daemonCfgs[(i, "controlOn")] = (
        None,
        {
            "controlCfg": {
                "staticPower": {"fromuW": staticPower},
                "referenceMeasurementRoundInterval": referenceMeasurementRoundInterval,
                "learnCfg": {"lagrange": 1},
                "speedThreshold": 0.9,
                "minimumControlInterval": {"fromuS": 5000000},
            },
            "raplCfg": raplCfg,
            "verbose": "Info",
        },
    )
    daemonCfgs[(i, "randomUniform")] = (
        None,
        {
            "controlCfg": {
                "staticPower": {"fromuW": staticPower},
                "referenceMeasurementRoundInterval": referenceMeasurementRoundInterval,
                "learnCfg": {"random": None},
                "speedThreshold": 0.9,
                "minimumControlInterval": {"fromuS": 5000000},
            },
            "raplCfg": raplCfg,
            "verbose": "Info",
        },
    )


stream = experiment.perfwrapped("stream_c", [])

lammps = experiment.perfwrapped(
    "mpiexec",
    ["-n", "24", "amg", "-problem", "2", "-n", "90", "90", "90", "-P", "2", "12", "1"],
)


host = nrm.Local()
results = {}

keys = list(daemonCfgs.keys())
print(keys)
random.shuffle(keys)
print(keys)

for key in keys:
    baseActions, cfg = daemonCfgs[key]
    results[key] = experiment.do_workload(host, baseActions, cfg, stream)

import pickle

result_df = pd.concat(
    [experiment.history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("internal-control-experiments.csv")
