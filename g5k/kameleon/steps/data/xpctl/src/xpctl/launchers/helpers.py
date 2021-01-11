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
