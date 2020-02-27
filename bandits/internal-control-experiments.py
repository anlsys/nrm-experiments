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

experimentSamplingSize = 2
powerCapRanges = [60, 75, 60, 100, 110, 120, 150, 180, 210]
staticPower = 200000000
referenceMeasurementRoundInterval = 10

daemonCfgs = {}

for i in range(0, experimentSamplingSize):
    for cap in powerCapRanges:
        daemonCfgs[(i, "pcap" + str(cap))] = {
            "controlCfg": {"fixedPower": {"fromuW": cap * 1000000}}
        }
    daemonCfgs[(i, "controlOn")] =
        {
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
            },
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


def do_workload(host, daemonCfg, workload):
    host.start_daemon(daemonCfg)
    print("Starting the workload")
    host.run_workload(workload)
    history = defaultdict(list)
    # print(host.get_state())
    getCPD = True
    try:
        while host.check_daemon() and not host.workload_finished():
            measurement_message = host.workload_recv()
            msg = json.loads(measurement_message)
            if "pubMeasurements" in msg:
                if getCPD:
                    getCPD = False
                    time.sleep(3)
                    cpd = host.get_cpd()
                    print(cpd)
                    cpd = dict(cpd)
                    print("Sensor identifier list:")
                    for sensorID in [sensor[0] for sensor in cpd["sensors"]]:
                        print("- %s" % sensorID)
                    print("Actuator identifier list:")
                    for sensorID in [sensor[0] for sensor in cpd["actuators"]]:
                        print("- %s" % sensorID)
                content = msg["pubMeasurements"][1][0]
                t = content["time"]
                sensorID = content["sensorID"]
                x = content["sensorValue"]
                print(
                    ".",
                    end=""
                    # "Measurement: originating at time %s for sensor %s of value %s"
                    #% (content["time"], content["sensorID"], content["sensorValue"])
                )
                history["sensor-" + sensorID].append((t, x))
            if "pubCPD" in msg:
                print("R")
            if "pubAction" in msg:
                # print(host.get_state())
                # print(msg)
                t, contents, meta, controller = msg["pubAction"]
                if "bandit" in controller.keys():
                    for key in meta.keys():
                        history["actionType"].append((t, key))
                    if "referenceMeasurementDecision" in meta.keys():
                        print("(ref)", end="")
                    elif "initialDecision" in meta.keys():
                        print("(init)", end="")
                    elif "innerDecision" in meta.keys():
                        print("(inner)", end="")
                        counter = 0
                        for value in meta["innerDecision"]["constraints"]:
                            history["constraint-" + str(counter)].append(
                                (t, value["fromConstraintValue"])
                            )
                            counter = counter + 1
                        counter = 0
                        for value in meta["innerDecision"]["objectives"]:
                            history["objective-" + str(counter)].append(
                                (t, value["fromObjectiveValue"])
                            )
                            counter = counter + 1
                        history["loss"].append((t, meta["innerDecision"]["loss"]))
                for content in contents:
                    actuatorID = content["actuatorID"] + "(action)"
                    x = content["actuatorValue"]
                    history[actuatorID].append((t, x))
                    for arm in controller["bandit"]["lagrange"]["lagrangeConstraint"][
                        "weights"
                    ]:
                        value = arm["action"][0]["actuatorValue"]
                        history[str(value / 1000000) + "-probability"].append(
                            (t, arm["probability"]["getProbability"])
                        )
                        history[str(value / 1000000) + "-cumulativeLoss"].append(
                            (t, arm["cumulativeLoss"]["getCumulativeLoss"])
                        )
                # print(
                # "Action: originating at time %s for actuator %s of value %s"
                #% (t,actuatorID,x)
                # )
            host.check_daemon()
        print("")
    except:
        return history
    host.stop_daemon()
    return history


host = nrm.Local()
results = {}
for key, cfg in daemonCfgs.items():
    results[key] = do_workload(host, cfg, stream)


def history_to_dataframe(key, history):
    iteration, name = key

    def mkdf(columnName, measurements):
        dataframe = pd.DataFrame(
            data=[(pd.Timestamp(t, unit="us"), m) for t, m in measurements]
        )
        dataframe.columns = ["time", columnName]
        return dataframe

    data_frames = [
        mkdf(columnName, measurements) for (columnName, measurements) in history.items()
    ]
    merged = reduce(
        lambda left, right: pd.merge(left, right, on=["time"], how="outer"), data_frames
    )
    df = merged.melt(id_vars=["time"]).assign(iteration=iteration).assign(name=name)
    df["time"] = df.time - df.time.min()
    return df


result_df = pd.concat(
    [history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("notebooks/internal-control-experiments.csv")
