#!/usr/bin/env nix-shell
#!nix-shell expe.nix -i python
# coding: utf-8

import sys
import time
import nrm.tooling as nrm

actuatorID = "candleActuator"

manifest = {
    "app": {
        "actuators": [
            {
                "actuatorID": actuatorID,
                "actuator": {
                    "actuatorBinary": "bash",
                    "actuatorArguments": ["-c", "kill -SIGUSR1 $(cat ./pid)"],
                    "actions": [1],
                    "referenceAction": 1,
                },
            }
        ]
    }
}

daemonCfg = {
    # "verbose": "Info",
    "raplCfg": None
}

#
##################         ##############            ########                       #######
# candle (nt3_*) # <-exec- # wrapper.sh # <-sigUSR1- # nrmd # <--run with manifest- # nrm #
##################         ##############            ########                       #######
#                                                        ^ daemon.actuate()
#                                                        | # upstream API
#                                                        v daemon.upstream_recv()
#                                                    #################
#                                                    # experiment.py # <- the smart one
#                                                    #################
#

def do_workload(daemonCfg, manifest):
    with nrm.nrmd(daemonCfg) as d:
        d.run(
            cmd="bash", args=["-c", "./wrapper.sh"], manifest=manifest, sliceID="candle"
        )
        while not d.all_finished():
            msg = d.upstream_recv()
            print("SLEEP")
            time.sleep(10)
            print("ACTUATE")
            d.actuate(Action(actuatorID, 1))
            print("ACTUATED")
            print(msg)

if __name__ == "__main__":
    do_workload(daemonCfg, manifest)
