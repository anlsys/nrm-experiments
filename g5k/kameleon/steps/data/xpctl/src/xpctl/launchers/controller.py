# -*- coding: utf-8 -*-

"""
Controller experiments launcher.

This module contains the code to launch controller experiments.
"""

import pathlib
import shutil
import subprocess
import sys

from . import command
from . import helpers


def forge_run_cmd(*, cmd, runner, user, ctrl_config):
    """Forge a command description for `subprocess.run`."""

    # assign arguments to relevant commands
    cmd_builder = command.BenchmarkCommandBuilder.by_name(cmd[0])
    nix_cmd, bench_cmd = cmd_builder.prepare_commands(cmd)

    # wrap bench_cmd with experiment runner command
    runner_cmd = command.ProxyCommand(runner) \
                     .arg(ctrl_config) \
                     .command(bench_cmd)

    # enable libnrm
    if not cmd_builder.supports_libnrm:
        raise RuntimeError(f'"{cmd[0]}" does not support required libnrm instrumentation')
    nix_cmd.arg('nrmSupport', 'true')

    # collect metrics with GNU time
    time_metrics_path = pathlib.Path('/tmp/time-metrics.csv')
    timed_cmd = helpers.time_command(runner_cmd, output=time_metrics_path)
    shutil.chown(time_metrics_path, user=user)  # ensure user has read/write access

    # build final nix_cmd by injecting runner_cmd
    nix_cmd.command(timed_cmd, interactive=False)

    runas_cmd = command.ProxyCommand('runuser') \
                    .args('-u', user) \
                    .command(nix_cmd)

    return runas_cmd


@helpers.manage_remaining_processes
def launch(params):  # pylint: disable=missing-function-docstring
    start_cmd = forge_run_cmd(
        cmd=params['cmd'],
        runner=params['config']['runners']['controller'],
        user=params['config']['xpctl']['user'],
        ctrl_config=params['ctrl_config']
    )
    print(start_cmd.build(), file=sys.stderr)  # XXX: logs
    subprocess.run(
        start_cmd.build(),
        check=True,
    )
