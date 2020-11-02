#!/usr/bin/env nix-shell
#!nix-shell expe.nix -i python
# coding: utf-8

import pandas as pd
import random
import nrm.tooling as nrm
import experiment

experimentSamplingRange = range(0, 4)
# experimentSamplingRange = range(0, 6)
powerCapRanges = [100, 250]
admissible = [(250, 250), (100, 100)]
actionLists = [
    [nrm.Action("RaplKey (PackageID 0)", p0), nrm.Action("RaplKey (PackageID 1)", p1)]
    for p0, p1 in admissible
]


def mkA(tuplepower):
    p0, p1 = tuplepower
    return [
        {"actuatorValueID": "RaplKey (PackageID 0)", "actuatorValue": p0},
        {"actuatorValueID": "RaplKey (PackageID 1)", "actuatorValue": p1},
    ]


hintActionList = {
    "neHead": mkA(admissible[0]),
    "neTail": [mkA(x) for x in admissible[1:]],
}

staticPower = 200000000
referenceMeasurementRoundInterval = 20

raplCfg = {
    "raplActions": [{"microwatts": 1000000 * p} for p in powerCapRanges],
    "referencePower": {"microwatts": 2500000},
    "raplPath": "/sys/devices/virtual/powercap/intel-rapl",
}

daemonCfgs = {}

for i in experimentSamplingRange:
    # for actions in actionLists:
    #     daemonCfgs[
    #       (i, "pcap" + experiment.ActionsShorthandDescription(actions))] = (
    #         actions,
    #         {
    #             "controlCfg": {"fixedPower": {"microwatts": 1000000}},
    #             "raplCfg": raplCfg,
    #             "verbose": "Info",
    #         },
    #     )
    daemonCfgs[(i, "controlOn")] = (
        None,
        {
            "controlCfg": {
                "hint": hintActionList,
                "learnCfg": {"horizon": 300},
                "minimumControlInterval": {"microseconds": 10000000},
                "minimumWaitInterval": {"microseconds": 3000000},
                "referenceMeasurementRoundInterval": referenceMeasurementRoundInterval,
                "speedThreshold": 1.11,
                "staticPower": {"microwatts": staticPower},
            },
            "raplCfg": raplCfg,
            "verbose": "Info",
        },
    )
    # daemonCfgs[(i, "randomUniform")] = (
    #     None,
    #     {
    #         "controlCfg": {
    #             "staticPower": {"microwatts": staticPower},
    #             "referenceMeasurementRoundInterval":
    #               referenceMeasurementRoundInterval,
    #             "learnCfg": {"random": None},
    #             "speedThreshold": 1.11,
    #             "minimumControlInterval": {"microseconds": 10000000},
    #             "hint": {"only": hintActionList},
    #         },
    #         "raplCfg": raplCfg,
    #         "verbose": "Debug",
    #     },
    # )


stream = experiment.perfwrapped("stream_c", [])

nas = experiment.perfwrapped("nice", ["-n", "16", "ep.D.x"])

lammps = experiment.perfwrapped(
    "mpiexec",
    ["-n", "24", "amg", "-problem", "2", "-n", "90", "90", "90", "-P", "2", "12", "1"],
)


results = {}

keys = list(daemonCfgs.keys())
print(keys)
random.shuffle(keys)
print(keys)

for key in keys:
    baseActions, cfg = daemonCfgs[key]
    print(cfg)
    results[key] = experiment.do_workload(baseActions, cfg, nas)

import pickle

result_df = pd.concat(
    [experiment.history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("internal-control-experiments.csv")
