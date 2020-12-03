#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import contextlib
import csv
import sys
import time
import uuid

import nrm.tooling as nrm


CPD_SENSORS_MAXTRY = 5  # maximum number of tries to get extra sensors definitions

LIBNRM_INSTRUMENTED_BENCHMARKS = {  # benchmark requiring libnrm instrumentation
    'stream_c',
    'amg'
}


# CSV export  #################################################################

DUMPED_MSG_TYPES = {
    'pubMeasurements',
    'pubProgress',
}

CSV_FIELDS = {
    'common': (
        'msg.timestamp',
        'msg.id',
        'msg.type',
    ),
    'pubMeasurements': (
        'sensor.timestamp',  # time
        'sensor.id',         # sensorID
        'sensor.value',      # sensorValue
    ),
    'pubProgress': (
        'sensor.cmd',    # cmdID
        'sensor.task',   # taskID
        'sensor.rank',   # rankID
        'sensor.pid',    # processID
        'sensor.tid',    # threadID
        'sensor.value',
    ),
}
assert DUMPED_MSG_TYPES.issubset(CSV_FIELDS)


def initialize_csvwriters(stack: contextlib.ExitStack):
    csvfiles = {
        msg_type: stack.enter_context(open(f'/tmp/dump_{msg_type}.csv', 'w'))
        for msg_type in DUMPED_MSG_TYPES
    }

    csvwriters = {
        msg_type: csv.DictWriter(csvfile, fieldnames=CSV_FIELDS['common']+CSV_FIELDS[msg_type])
        for msg_type, csvfile in csvfiles.items()
    }
    for csvwriter in csvwriters.values():
        csvwriter.writeheader()

    return csvwriters


def pubMeasurements_extractor(msg_id, payload):
    timestamp, measures = payload
    for data in measures:
        yield {
            'msg.timestamp': timestamp,
            'msg.id': msg_id,
            'msg.type': 'pubMeasurements',
            #
            'sensor.timestamp': data['time'],
            'sensor.id': data['sensorID'],
            'sensor.value': data['sensorValue'],
        }


def pubProgress_extractor(msg_id, payload):
    timestamp, identification, value = payload
    yield {
        'msg.timestamp': timestamp,
        'msg.id': msg_id,
        'msg.type': 'pubProgress',
        #
        'sensor.cmd': identification['cmdID'],
        'sensor.task': identification['taskID'],
        'sensor.rank': identification['rankID'],
        'sensor.pid': identification['processID'],
        'sensor.tid': identification['threadID'],
        'sensor.value': value,
    }

def noop_extractor(*_):
    yield from ()


DUMPED_MSG_EXTRACTORS = {
    'pubMeasurements': pubMeasurements_extractor,
    'pubProgress': pubProgress_extractor,
}
assert DUMPED_MSG_TYPES.issubset(DUMPED_MSG_EXTRACTORS)


def dump_upstream_msg(csvwriters, msg):
    msg_id = uuid.uuid4()
    for msg_type, payload in msg.items():
        msg2rows = DUMPED_MSG_EXTRACTORS.get(msg_type, noop_extractor)
        csvwriter = csvwriters.get(msg_type)
        for row in msg2rows(msg_id, payload):
            csvwriter.writerow(row)


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


def update_sensors_list(daemon, known_sensors, *, maxtry=CPD_SENSORS_MAXTRY, sleep_duration=0.5):
    """Update in place the list known_sensors, returns the new sensors."""
    assert isinstance(known_sensors, list)

    new_sensors = []
    for _ in range(maxtry):
        new_sensors = [
            sensor
            for sensor in daemon.get_cpd().sensors()
            if sensor not in known_sensors
        ]
        if new_sensors:
            break  # new sensors have been retrieved
        time.sleep(sleep_duration)

    known_sensors.extend(new_sensors)
    return new_sensors


def launch_application(daemon_cfg, workload_cfg, *, setup=noop, teardown=noop, sleep_duration=0.5):
    with nrm.nrmd(daemon_cfg) as daemon:
        # extra daemon configuration before starting workload
        setup(daemon)

        # collect workload-independent sensors (e.g., RAPL)
        sensors = daemon.get_cpd().sensors()

        # launch workload
        daemon.run(**workload_cfg)

        # retrieve definition of extra sensors if required
        if workload_cfg['cmd'] in LIBNRM_INSTRUMENTED_BENCHMARKS:
            libnrm_sensors = update_sensors_list(daemon, sensors, sleep_duration=sleep_duration)
            if not libnrm_sensors:
                raise RuntimeError('Unable to get application sensors')

        # dump sensors values while waiting for the end of the execution
        with contextlib.ExitStack() as stack:
            # each message type is dumped into its own csv file
            # each csv file is created with open
            # we combine all open context managers thanks to an ExitStack
            csvwriters = initialize_csvwriters(stack)

            while not daemon.all_finished():
                msg = daemon.upstream_recv()
                dump_upstream_msg(csvwriters, msg)

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
        # 'verbose': 'Debug',
        'verbose': 'Info',
    }

    # workload configuration (i.e., app description + manifest)
    workload_cfg = {
        'cmd': cmd[0],
        'args': cmd[1:],
        'sliceID': 'sliceID',  # XXX: bug in pynrm/hnrm if missing or None (should be generated?)
        'manifest': {
            'app': {},
        },
    }
    # NB: if we want to keep the output of the launched command when run in
    # detached mode (which is the case with the Python API), we can wrap the
    # call in a shell
    #     {
    #         'cmd': 'sh',
    #         'args': ['-c', f'{command} >stdout 2>stderr'],
    #     }
    #
    # Uncomment the lines below to wrap the call:
    # workload_cfg.update(
    #     cmd='sh',
    #     args=['-c', ' '.join(cmd + ['>/tmp/stdout', '2>/tmp/stderr'])],
    # )

    # configure libnrm instrumentation if required
    if workload_cfg['cmd'] in LIBNRM_INSTRUMENTED_BENCHMARKS:
        workload_cfg['manifest']['app']['instrumentation'] = {
            'ratelimit': {'hertz': 1_000_000},
        }

    launch_application(
        daemon_cfg,
        workload_cfg,
        setup=lambda daemon: enforce_powercap(daemon, options.powercap),
    )


if __name__ == '__main__':
    options, cmd = cli()
    run(options, cmd)
