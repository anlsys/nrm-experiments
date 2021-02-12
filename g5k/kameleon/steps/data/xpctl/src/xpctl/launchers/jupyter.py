# -*- coding: utf-8 -*-

"""
Jupyter notebook launcher.

This module contains the code to launch the Jupyter notebook packaged with
hnrm.
"""

import os
import signal
import subprocess
import sys

from . import command
from . import helpers


START_CMD = command.Command('jupyter-notebook') \
                .arg('--no-browser') \
                .arg('--ip="0.0.0.0"') \
                .arg('--NotebookApp.default_url=/tree/notebooks')

STOP_CMD = command.Command('jupyter-notebook') \
               .arg('stop')


# ==========  helpers  ==========

def forge_run_cmd(*, cmd, user):
    """Forge a command description for `subprocess.run`."""
    nix_cmd = command.NixShellCommand() \
                  .pure() \
                  .arg('jupyter', 'true') \
                  .arg('experiment', 'true') \
                  .path('<hnrm/shell.nix>') \
                  .command(cmd, interactive=False)

    runas_cmd = command.ProxyCommand('runuser') \
                    .args('-u', user) \
                    .command(nix_cmd)

    return runas_cmd


def forge_sigint_handler(*, user):
    """Forge a SIGINT handler to cleanly shut down Jupyter."""

    def sigint_handler(signum, _):
        assert signum == signal.SIGINT
        print('Caught SIGINT, shutting down Jupyter: please be patient', file=sys.stderr)  # XXX: logs

        stop_cmd = forge_run_cmd(
            cmd=STOP_CMD,
            user=user,
        )
        subprocess.run(  # ask Jupyter notebook to shutdown
            stop_cmd.build(),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    return sigint_handler


# ==========  runner  ==========

@helpers.manage_remaining_processes(forceclean=True)
def launch(params):  # pylint: disable=missing-function-docstring
    stop_jupyter_on_sigint = forge_sigint_handler(
        user=params['config']['xpctl']['user'],
    )

    with helpers.signal_handler(signal.SIGINT, stop_jupyter_on_sigint):
        start_cmd = forge_run_cmd(
            cmd=START_CMD,
            user=params['config']['xpctl']['user']
        )
        print(start_cmd.build(), file=sys.stderr)  # XXX: logs
        subprocess.run(
            start_cmd.build(),
            check=False,
            preexec_fn=os.setsid,  # create a dedicated session for processes created by Jupyter
        )
