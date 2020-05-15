#!/usr/bin/env python
# coding: utf-8

import sys
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


def armShorthandDescription(arm):
    return "/".join([str(a["actuatorValue"]) for a in arm])


def ActionsShorthandDescription(arm):
    return "/".join([str(a.actuatorValue) for a in arm])


def do_workload(host, baseActions, daemonCfg, workload, actuations=[]):
    host.start_daemon(daemonCfg)
    print("Starting the workload")
    host.run_workload(workload)
    history = defaultdict(list)
    getCPD = True
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
                if baseActions:
                    host.workload_action(baseActions)
            for content in msg["pubMeasurements"][1]:
                t = content["time"]
                sensorID = content["sensorID"]
                if "Downstream" in sensorID:
                    sensorID = "sensor-Downstream"
                x = content["sensorValue"]
                history["sensor-" + sensorID].append((t, x))
            print(".", end="")
        if "pubCPD" in msg:
            print("R")
        if "pubAction" in msg:
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
                    counter = 0
                    for value in meta["innerDecision"]["reportNormalizedObjectives"]:
                        print(value)
                        history["reportNormalizedObjectives(weight)-" + str(counter)].append((t, value[0]))
                        history["reportNormalizedObjectives(value)-" + str(counter)].append((t, value[1]))
                        counter = counter + 1
                    counter = 0
                    for value in meta["innerDecision"]["reportEvaluatedConstraints"]:
                        print(value)
                        interval = value[2]['i']
                        history["reportEvaluatedConstraints(threshold)-" + str(counter)].append((t, value[0]))
                        history["reportEvaluatedConstraints(value)-" + str(counter)].append((t, value[1]))
                        history["reportEvaluatedConstraints(inf)-" + str(counter)].append((t, interval[0]))
                        history["reportEvaluatedConstraints(sup)-" + str(counter)].append((t, interval[1]))
                        counter = counter + 1
                    counter = 0
                    for value in meta["innerDecision"]["reportEvaluatedObjectives"]:
                        interval = value[2]['i']
                        history["reportEvaluatedObjectives(weight)-" + str(counter)].append((t, value[0]))
                        history["reportEvaluatedObjectives(measurement)-" + str(counter)].append((t, value[1]))
                        history["reportEvaluatedObjectives(inf)-" + str(counter)].append((t, interval[0]))
                        history["reportEvaluatedObjectives(sup)-" + str(counter)].append((t, interval[1]))
                        counter = counter + 1
                    history["hco"].append((t, meta["innerDecision"]["loss"]))
                bandit = controller["bandit"]
                if "lagrange" in bandit.keys():
                    for arm in bandit["lagrange"]["lagrange"]["weights"]:
                        history[
                            armShorthandDescription(arm["action"]) + "-probability"
                        ].append((t, arm["probability"]["getProbability"]))
                        history[
                            armShorthandDescription(arm["action"]) + "-cumulativeLoss"
                        ].append((t, arm["cumulativeLoss"]["getCumulativeLoss"]))
            for content in contents:
                actuatorID = content["actuatorID"] + "(action)"
                x = content["actuatorValue"]
                history[actuatorID].append((t, x))
            for arm, stats in controller["armstats"]:
                pulls = stats[0]
                avgLoss = stats[1]
                avgObj = stats[2][0]
                avgCst = stats[3][0]
                for name, value in stats[4]:
                    if "Downstream" in name:
                        name = "Downstream"
                    history["avgMeasurement-" + name + "-" + armShorthandDescription(arm)].append(
                        (t, value)
                    )
                for name, value in stats[5]:
                    if "Downstream" in name:
                        name = "Downstream"
                    history["avgRef-" + name + "-" + armShorthandDescription(arm)].append(
                        (t, value)
                    )
                history["pulls-" + armShorthandDescription(arm)].append((t, pulls))
                history["avgLoss-" + armShorthandDescription(arm)].append((t, avgLoss))
                history["avgObj-" + armShorthandDescription(arm)].append((t, avgObj))
                history["avgCst-" + armShorthandDescription(arm)].append((t, avgCst))
        host.check_daemon()
    print("")
    host.stop_daemon()
    return history


def history_to_dataframe(key, history):
    iteration, name = key

    def mkdf(columnName, measurements):
        dataframe = pd.DataFrame(measurements)
        dataframe.columns = ["time", "value"]
        dataframe["variable"] = columnName
        return dataframe

    data_frames = [
        mkdf(columnName, measurements) for (columnName, measurements) in history.items()
    ]
    df = pd.concat(data_frames).assign(iteration=iteration).assign(name=name)

    df["time"] = df.time - df.time.min()
    return df
