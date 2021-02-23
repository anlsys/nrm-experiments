#!/usr/bin/env nix-shell
#!nix-shell expe.nix -i python
# coding: utf-8

import sys
import time
import nrm.tooling as nrm

manifest = {}
daemonCfg = {
    # "verbose": "Info",
    "raplCfg": None
}


def do_workload(daemonCfg, manifest):
    with nrm.nrmd(daemonCfg) as d:
        d.run(
            cmd="bash", args=["-c", "./wrapper.sh"], manifest=manifest, sliceID="candle"
        )
        while not d.all_finished():
            msg = d.upstream_recv()
            print(msg)


if __name__ == "__main__":
    do_workload(daemonCfg, manifest)
