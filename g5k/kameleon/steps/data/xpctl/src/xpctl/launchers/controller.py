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


GNU_TIME_LOG_PATH = pathlib.Path('/tmp/time-metrics.csv')
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
    with open(GNU_TIME_LOG_PATH, 'w') as gnu_time_log:
        print(','.join(t[0] for t in GNU_TIME_FORMAT), file=gnu_time_log, flush=True)
    shutil.chown(GNU_TIME_LOG_PATH, user=user)

    # /!\ we avoid bash builtin with the `command` builtin /!\
    timed_cmd = command.ProxyCommand('command time') \
                    .arg('--append') \
                    .arg(f'--output={GNU_TIME_LOG_PATH}') \
                    .arg('--format=' + ','.join(t[1] for t in GNU_TIME_FORMAT)) \
                    .command(runner_cmd)

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
