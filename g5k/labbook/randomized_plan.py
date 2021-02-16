#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math
import pathlib
import random
import sys


__version__ = '0.0.1'


def _create_parser():
    parser = argparse.ArgumentParser(
        description='Generate a random experiment plan.'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'{pathlib.Path(__file__).stem} {__version__}',
    )
    parser.add_argument(
        '--seed',
        default=random.randrange(sys.maxsize),
        type=int,
        help='seed of the pseudo-random generator, useful to rebuild a file',
    )
    parser.add_argument(
        '--power-range',
        nargs=2,
        type=float,
        required=True,
        help='range of valid power caps [W]',
        metavar=('POWER_MIN', 'POWER_MAX'),
        dest='power',
    )
    parser.add_argument(
        '--period-range',
        nargs=2,
        type=float,
        required=True,
        help='range of valid periods [s]',
        metavar=('PERIOD_MIN', 'PERIOD_MAX'),
        dest='period',
    )
    parser.add_argument(
        '--duration',
        type=float,
        required=True,
        help='targeted duration [s] of the experiment plan: there is at most one event after this duration',
        metavar='DURATION',
        dest='duration',
    )
    return parser


def cli(args=None):
    parser = _create_parser()
    options = vars(parser.parse_args(args))  # read argparse.Namespace as a dict
    generate_plan(**options)


def generate_plan(*, seed, power, period, duration):
    # record generation command
    print(
        '# generation command:',
        pathlib.Path(__file__).name,
        f'--seed {seed}',
        '--power-range {} {}'.format(*power),
        '--period-range {} {}'.format(*period),
        f'--duration {duration}',
    )

    # write header
    print('version: 1')

    # initialize generator
    random.seed(a=seed)
    log_period = tuple(map(math.log10, period))
    now, powercap = 0, math.floor(max(power))

    # generate actions
    ACTION_FORMAT = '  - {{time: {now}, action: \'set_rapl_powercap\', args: [{powercap}] }}'

    print('actions:')
    while now < duration:
        print(ACTION_FORMAT.format(now=now, powercap=powercap))
        powercap = random.randint(*power)
        now += 10 ** random.uniform(*log_period)  # /!\ log10(period) is uniform /!\
    print(ACTION_FORMAT.format(now=now, powercap=powercap))


if __name__ == '__main__':
    cli()
