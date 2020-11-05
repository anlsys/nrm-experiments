#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import time

import nrm.tooling as nrm


# helper functions  ###########################################################

def noop(*args, **kwargs):
    pass


def enforce_powercap(daemon, powercap):
    # this relies only on the configuration of the daemon, so we do not need to
    # wait for the application to start
    cpd = daemon.get_cpd()
    import pprint; pprint.pprint(vars(cpd), stream=sys.stderr)  # XXX: logs

    # get all RAPL actuator (XXX: should filter on tag rather than name)
    import pprint; pprint.pprint(cpd.actuators())
    rapl_actuators = filter(lambda a: a.actuatorID.startswith('RaplKey'), cpd.actuators())

    # for each RAPL actuator, create an action that sets the powercap to powercap
    set_pcap_actions = [nrm.Action(actuator[0], powercap) for actuator in rapl_actuators]
    import pprint; pprint.pprint(set_pcap_actions, stream=sys.stderr)  # XXX: logs

    daemon.actuate(set_pcap_actions)


def launch_application(daemon_cfg, workload_cfg, *, setup=noop, teardown=noop, sleep_duration=0.5):
    with nrm.nrmd(daemon_cfg) as daemon:
        # extra daemon configuration before starting workload
        setup(daemon)

        # launch workload, and wait for the end of the execution
        daemon.run(**workload_cfg)
        while not daemon.all_finished():
            # msg = daemon.upstream_recv()
            time.sleep(sleep_duration)


        # extra work once the workload execution is over
        teardown(daemon)


# main script  ################################################################

def cli(args=None):

    def _powercap(string):
        try:
            pcap = int(string)
        except ValueError as err:
            msg = f'unable to parse as an integer: "{string}"'
            raise argparse.ArgumentTypeError(msg) from err
        if pcap <= 0:
            msg = f'invalid powercap: "{pcap}"'
            raise argparse.ArgumentTypeError(msg)
        return pcap

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'powercap',
        type=_powercap,
        help='RAPL maximum power (in watts)',
    )

    options, cmd = parser.parse_known_args(args)
    return options, cmd


def run(options, cmd):
    # daemon configuration (static gain analysis: single powercap value)
    daemon_cfg = {
        'raplCfg': {
            'raplActions': [
                {'microwatts': 1_000_000 * options.powercap},
            ],
        },
        'verbose': 'Debug',
        # 'verbose': 'Info',
    }

    # workload configuration (i.e., app description + manifest)
    workload_cfg = {
        'cmd': cmd[0],
        'args': cmd[1:],
        'sliceID': 'sliceID',  # XXX: bug in pynrm/hnrm if missing or None (should be generated?)
        'manifest': {  # XXX: pynrm/hnrm crashes if missing
            # 'app': {
            #     'slice': {
            #         'cpus': 1,
            #         'mems': 1,
            #     },
            #     'perfwrapper': {
            #         'perfLimit': {'fromOps': 100_000},
            #         'perfFreq': {'fromHz': 1},
            #     },
            # },
        },
    }
    # NB: if we want to keep the output of the launched command when run in
    # detached mode (which is the case with the Python API), we can wrap the call
    # in a shell
    #     {
    #         'cmd': 'sh',
    #         'args': ['-c', f'{command} >stdout 2>stderr'],
    #     }

    launch_application(
        daemon_cfg,
        workload_cfg,
        setup=lambda daemon: enforce_powercap(daemon, options.powercap),
    )


if __name__ == '__main__':
    options, cmd = cli()
    run(options, cmd)
