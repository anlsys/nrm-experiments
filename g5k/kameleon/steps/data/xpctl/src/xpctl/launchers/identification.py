# -*- coding: utf-8 -*-

"""
Identification experiments launcher.

This module contains the code to launch identification experiments
(e.g., static gain experiments, …).
"""

import pathlib
import shutil
import subprocess
import sys

from . import command
from . import helpers


def forge_run_cmd(*, cmd, runner, user, plan):
    """Forge a command description for `subprocess.run`."""

    # assign arguments to relevant commands
    cmd_builder = command.BenchmarkCommandBuilder.by_name(cmd[0])
    nix_cmd, bench_cmd = cmd_builder.prepare_commands(cmd)

    # wrap bench_cmd with experiment runner command
    runner_cmd = command.ProxyCommand(runner) \
                     .command(bench_cmd)

    # enable libnrm if the benchmark supports it
    if cmd_builder.supports_libnrm:
        nix_cmd.arg('nrmSupport', 'true')
        runner_cmd.arg('--enable-libnrm')

    # the experiment plan must be set after optional arguments (e.g., --enable-libnrm)
    runner_cmd.arg(plan)

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
        runner=params['config']['runners']['identification'],
        user=params['config']['xpctl']['user'],
        plan=params['plan'],
    )
    print(start_cmd.build(), file=sys.stderr)  # XXX: logs
    subprocess.run(
        start_cmd.build(),
        check=True,
    )
