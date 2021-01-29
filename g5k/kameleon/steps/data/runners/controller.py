#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import logging.config
import math
import statistics
import time

import nrm.tooling as nrm


# frequency (in hertz) for RAPL sensor polling
RAPL_SENSOR_FREQ = 1

# maximum number of tries to get extra sensors definitions
CPD_SENSORS_MAXTRY = 5


# XXX: modularize by reading the xpctl_conf file
LIBNRM_INSTRUMENTED_BENCHMARKS = {  # benchmark requiring libnrm instrumentation
    'stream_c',
    'amg'
}


# logging configuration  ######################################################

LOGGER_NAME = 'controller-runner'

LOGS_LEVEL = 'INFO'

LOGS_CONF = {
    'version': 1,
    'formatters': {
        'precise': {
            # timestamp is epoch in seconds
            'format': '{created}\u0000{levelname}\u0000{process}\u0000{funcName}\u0000{message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': f'/tmp/{LOGGER_NAME}.log',
            'mode': 'w',
            'level': LOGS_LEVEL,
            'formatter': 'precise',
            'filters': [],
        },
    },
    'loggers': {
        LOGGER_NAME: {
            'level': LOGS_LEVEL,
            'handlers': [
                'file',
            ],
        },
    },
}

logging.config.dictConfig(LOGS_CONF)

logger = logging.getLogger(LOGGER_NAME)


# controller logic & configuration  ###########################################

# The system is approximated as a first order linear system.
# The controller is implemented as a Proportional-Integral (PI) controller.


# -----  RAPL characterization  -----

# The effective power consumption does not exactly match the powercap command.
# The deviation is modeled as an affine relation:
#     power consumption = f(powercap)
#                       = RAPL_SLOPE * powercap + RAPL_OFFSET

RAPL_SLOPE = 0.94  # (unitless)
RAPL_OFFSET = 0.03  # (in watt)


# -----  model parameters  -----

# The system is modeled with the following equation:
#     progress = f(powercap)
#              = GAIN_LINEAR * (1 - exp(-ALPHA * (powercap - BETA)))

# benchmark/cluster dependent parameters
ALPHA = 0.04  # (in 1/watt)
BETA = 30  # (in watt)

# powercap → progress parameters (first-order linear approximation)
GAIN_LINEAR = 25  # (in hertz)
TIME_CONSTANT = 0.5  # (in second)

# linearization/delinearization (with respect to the model equation)
def _linearize(value):
    return -math.exp(-ALPHA * (RAPL_SLOPE * value + RAPL_OFFSET - BETA))

def _delinearize(value):
    return (-math.log(-value) / ALPHA + BETA - RAPL_OFFSET) / RAPL_SLOPE


# -----  controller parameters  -----

RESPONSE_TIME = 30  # 5% response time (defined as 3·τ)
INTEGRAL_GAIN = TIME_CONSTANT / (GAIN_LINEAR * RESPONSE_TIME / 3)
PROPORTIONAL_GAIN = 1 / (GAIN_LINEAR * RESPONSE_TIME / 3)

# operating range
POWERCAP_MIN, POWERCAP_MAX = 40, 120
POWERCAP_LINEAR_MIN, POWERCAP_LINEAR_MAX = \
        _linearize(POWERCAP_MIN), _linearize(POWERCAP_MAX)


class PIController:
    def __init__(self, daemon, rapl_actuators):
        self.daemon = daemon
        self.rapl_actuators = rapl_actuators

        # objective configuration (requested system behavior)
        self.progress_setpoint = GAIN_LINEAR / 2

        # controller initial state
        self.powercap_linear = POWERCAP_LINEAR_MAX
        self.prev_error = 0

        # RAPL window monitoring
        self.rapl_window_timestamp = time.time()  # start of current RAPL window
        self.heartbeat_timestamps = []

    def control(self):
        while not self.daemon.all_finished():
            msg = self.daemon.upstream_recv()  # blocking call
            (msg_type, payload), = msg.items()  # single-key dict destructuring
            # dispatch to relevant logic
            if msg_type == 'pubProgress':
                self._update_progress(payload)
            elif msg_type == 'pubMeasurements':
                self._update_measure(payload)
            # XXX: re-integrate logging of values

    def _update_progress(self, payload):
        timestamp, _, _ = payload
        timestamp *= 1e-6  # convert µs in s
        self.heartbeat_timestamps.append(timestamp)

    @staticmethod
    def _estimate_progress(heartbeat_timestamps):
        """Estimate the heartbeats' frequency given a list of heartbeats' timestamps."""
        return statistics.median(
            1 / (second - first)
            for first, second in zip(heartbeat_timestamps, heartbeat_timestamps[1:])
        )

    def _update_measure(self, payload):
        timestamp, measures = payload
        timestamp *= 1e-6  # convert µs in s
        for data in measures:
            # XXX: handle case where we have multiple RaplKey at once
            if data['sensorID'].startswith('RaplKey'):
                # collect sensors
                window_duration = timestamp - self.rapl_window_timestamp
                progress_estimation = self._estimate_progress(self.heartbeat_timestamps)

                # estimate current error
                error = self.progress_setpoint - progress_estimation

                # compute command with linear equation
                self.powercap_linear = \
                        window_duration * INTEGRAL_GAIN * error + \
                        PROPORTIONAL_GAIN * (error - self.prev_error) + \
                        self.powercap_linear

                # thresholding (ensure POWERCAP_MIN ≤ powercap ≤ POWERCAP_MAX)
                #   this can be done in the linear space as the variable change
                #   is monotic (increasing if ALPHA > 0)
                assert ALPHA > 0
                self.powercap_linear = max(
                    min(
                        self.powercap_linear,
                        POWERCAP_LINEAR_MAX
                    ),
                    POWERCAP_LINEAR_MIN
                )

                # delinearize to get actual actuator value
                powercap = _delinearize(self.powercap_linear)

                # propagate state
                self.prev_error = error

                # reset monitoring variables for new upcoming RAPL window
                self.rapl_window_timestamp = timestamp
                self.heartbeat_timestamps = self.heartbeat_timestamps[-1:]

                # send command to actuator
                powercap = round(powercap)  # XXX: discretization induced by raplActions
                enforce_powercap(self.daemon, self.rapl_actuators, powercap)


# helper functions  ###########################################################

def update_sensors_list(daemon, known_sensors, *, maxtry=CPD_SENSORS_MAXTRY, sleep_duration=0.5):
    """Update in place the list known_sensors, returns the new sensors."""
    assert isinstance(known_sensors, list)

    new_sensors = []
    for _ in range(maxtry):
        new_sensors = [
            sensor
            for sensor in daemon.req_cpd().sensors()
            if sensor not in known_sensors
        ]
        if new_sensors:
            break  # new sensors have been retrieved
        time.sleep(sleep_duration)

    known_sensors.extend(new_sensors)  # extend known_sensors in place
    return new_sensors


def enforce_powercap(daemon, rapl_actuators, powercap):
    # for each RAPL actuator, create an action that sets the powercap to powercap
    set_pcap_actions = [
        nrm.Action(actuator.actuatorID, powercap)
        for actuator in rapl_actuators
    ]

    logger.info(f'set_pcap={powercap}')
    daemon.actuate(set_pcap_actions)


def collect_rapl_actuators(daemon):
    # the configuration of RAPL actuators solely depends on the daemon: there
    # is no need to wait for the application to start
    cpd = daemon.req_cpd()

    # get all RAPL actuator (XXX: should filter on tag rather than name)
    rapl_actuators = list(
        filter(
            lambda a: a.actuatorID.startswith('RaplKey'),
            cpd.actuators()
        )
    )
    logger.info(f'rapl_actuators={rapl_actuators}')
    return rapl_actuators


def launch_application(daemon_cfg, workload_cfg, *, sleep_duration=0.5):
    with nrm.nrmd(daemon_cfg) as daemon:
        # collect RAPL actuators
        rapl_actuators = collect_rapl_actuators(daemon)

        # collect workload-independent sensors (e.g., RAPL)
        sensors = daemon.req_cpd().sensors()
        logger.info(f'daemon_sensors={sensors}')

        # launch workload
        logger.info('launch workload')
        daemon.run(**workload_cfg)

        # retrieve definition of extra sensors if required
        if workload_cfg['cmd'] in LIBNRM_INSTRUMENTED_BENCHMARKS:
            app_sensors = update_sensors_list(daemon, sensors, sleep_duration=sleep_duration)
            if not app_sensors:
                logger.critical('failed to get application-specific sensors')
                raise RuntimeError('Unable to get application-specific sensors')
            logger.info(f'app_sensors={app_sensors}')

        controller = PIController(daemon, rapl_actuators)
        controller.control()


# main script  ################################################################

def cli(args=None):

    parser = argparse.ArgumentParser()

    options, cmd = parser.parse_known_args(args)
    if cmd[0] == '--':
        cmd = cmd[1:]

    return options, cmd


def run(options, cmd):
    # daemon configuration
    daemon_cfg = {
        'raplCfg': {
            'raplActions': [  # XXX: check with Valentin for continuous range
                {'microwatts': 1_000_000 * powercap}
                for powercap in range(POWERCAP_MIN, POWERCAP_MAX + 1)
            ],
        },
        'passiveSensorFrequency': {
            # this configures the frequency of all 'passive' sensors, we only
            # use RAPL sensors here
            'hertz': RAPL_SENSOR_FREQ,
        },
        # 'verbose': 'Debug',
        # 'verbose': 'Info',
        'verbose': 'Error',
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
    #     args=['-c', ' '.join(cmd), '>/tmp/stdout', '2>/tmp/stderr'],
    # )

    # configure libnrm instrumentation if required
    if workload_cfg['cmd'] in LIBNRM_INSTRUMENTED_BENCHMARKS:
        workload_cfg['manifest']['app']['instrumentation'] = {
            'ratelimit': {'hertz': 1_000_000},
        }

    logger.info(f'daemon_cfg={daemon_cfg}')
    logger.info(f'workload_cfg={workload_cfg}')
    launch_application(daemon_cfg, workload_cfg)


if __name__ == '__main__':
    options, cmd = cli()
    run(options, cmd)
