# -*- coding: utf-8 -*-

"""
Launcher helper snippets.

The functions defined in this module are useful code snippets shared by the
launchers.
"""

import contextlib
import functools
import signal
import subprocess
import sys

from . import command


def manage_remaining_processes(func=None, *, forceclean=False):
    """
    Deals with processes remaining from previous experiments.

    Args:
        forceclean: Override --clean-remaining-processes option.
    """
    if func is None:
        return functools.partial(manage_remaining_processes, forceclean=forceclean)

    @functools.wraps(func)
    def wrapper(params):
        params['clean'] = params['clean'] or forceclean  # override clean
        #
        print(f'Checking for remaining processes owned by {params["config"]["xpctl"]["user"]}', file=sys.stderr)  # XXX: logs
        check_remaining_processes = subprocess.run(
            ('pgrep', '--list-full', '--euid', params['config']['xpctl']['user'], ),
            check=False,
        )
        if check_remaining_processes.returncode not in (0, 1):
            raise subprocess.SubprocessError(
                check_remaining_processes.returncode,
                check_remaining_processes.args,
            )
        if check_remaining_processes.returncode == 0:  # One or more processes matched the criteria (cf. pgrep(1))
            print(f'Found remaining processes owned by {params["config"]["xpctl"]["user"]}', file=sys.stderr)  # XXX: logs
            if params['clean']:
                print('Clean option active: killing remaining processes', file=sys.stderr)  # XXX: logs
                subprocess.check_call(
                    ('pkill', '--euid', params['config']['xpctl']['user'], )
                )
            else:
                print('Clean option inactive: aborting', file=sys.stderr)  # XXX: logs
                sys.exit(1)
        #
        return func(params)

    return wrapper


@contextlib.contextmanager
def signal_handler(signalnum, handler):
    """
    Create a context manager where signalnum is handled by handler.

    The original handler for signalnum is restored upon exiting the context.
    """
    orig_handler = signal.signal(signalnum, handler)
    try:
        yield
    finally:
        signal.signal(signalnum, orig_handler)


#------------------------------------------------------------------------------

GNU_TIME_FORMAT = (
    # ('csv.header', '%time-format')
    ('cmd', r'\"%C\"'),
    ('retcode', '%x'),
    ('elapsed.time', '%e'),
    ('system.time', '%S'),
    ('user.time', '%U'),
    ('cpu.share', '%P'),
    ('avg.mem', '%K'),
    ('avg.rss', '%t'),
    ('max.rss', '%M'),
    ('avg.data', '%D'),
    ('avg.text', '%X'),
    ('avg.stack', '%p'),
    ('page.size', '%Z'),
    ('major.page.faults', '%F'),
    ('minor.page.faults', '%R'),
    ('swaps', '%W'),
    ('fs.inputs', '%I'),
    ('fs.outputs', '%O'),
    ('sock.rcvd', '%r'),
    ('sock.sent', '%s'),
    ('signals', '%k'),
    ('time.ctx.switch', '%c'),
    ('io.ctx.switch', '%w'),
)


def time_command(cmd, *, output):
    """
    Wrap a command to collect execution metrics with GNU time in output.
    """

    # create a new file with CSV header
    with open(output, 'w') as gnu_time_log:
        print(','.join(t[0] for t in GNU_TIME_FORMAT), file=gnu_time_log, flush=True)

    # /!\ we avoid bash builtin with the `command` builtin /!\
    timed_cmd = command.ProxyCommand('command time') \
                    .arg('--append') \
                    .arg(f'--output={output}') \
                    .arg('--format=' + ','.join(t[1] for t in GNU_TIME_FORMAT)) \
                    .arg('--quiet') \
                    .command(cmd)

    return timed_cmd
