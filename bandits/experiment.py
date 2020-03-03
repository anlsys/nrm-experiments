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


def do_workload(host, daemonCfg, workload):
    host.start_daemon(daemonCfg)
    print("Starting the workload")
    host.run_workload(workload)
    history = defaultdict(list)
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
                if "Downstream" in sensorID:
                    sensorID="sensor-Downstream"
                x = content["sensorValue"]
                print(".", end="")
                history["sensor-" + sensorID].append((t, x))
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
                        history["loss"].append((t, meta["innerDecision"]["loss"]))
                for content in contents:
                    actuatorID = content["actuatorID"] + "(action)"
                    x = content["actuatorValue"]
                    history[actuatorID].append((t, x))
                    for arm in controller["bandit"]["lagrange"]["lagrangeConstraint"][
                        "weights"
                    ]:
                        history[
                            str(arm["action"]) + "-probability"
                        ].append((t, arm["probability"]["getProbability"]))
                        history[
                            str(arm["action"]) + "-cumulativeLoss"
                        ].append((t, arm["cumulativeLoss"]["getCumulativeLoss"]))
                    print(controller["armstats"])
                    for arm,stats in controller["armstats"]:
                        pulls=stats[0]
                        avgLoss=stats[1]
                        history[ "pulls-"+str(arm)].append((t,pulls))
                        history[ "avgLoss-"+str(arm)].append((t,avgLoss))


            host.check_daemon()
        print("")
    except:
        e = sys.exc_info()[0]
        print(e)
        return history
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
