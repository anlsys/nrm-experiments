# -*- coding: utf-8 -*-

"""
Identification experiments launcher.

This module contains the code to launch identification experiments
(e.g., static gain experiments, …).
"""

import argparse
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


# ==========  module-specific helpers  ==========

class BenchmarkCommandParser:
    """
    Benchmark command parsing logic.

    The benchmark command parser build the configuration out of the arguments
    supplied on the command line.

    .. warning::
        The BenchmarkCommandParser is not meant for direct use: it is built as
        an abstract class.

    `xpctl` abstracts away the phase at which benchmark are configured: some
    parameters are set at compile time while other parameters are fed as
    arguments of the benchmark program.

    `xpctl` let the user specify all benchmark parameters as arguments of the
    benchmark program.

    This hierarchy of classes extracts the supplied arguments, and dispatches
    them where they belong:
        - compile-time parameters are supplied to the nix-shell command,
        - "classical" parameters are fed to the benchmark binary
    """

    _available_dispatchers = {}
    nix_path = None

    @classmethod
    def __init_subclass__(cls, *, benchmarks=(), **kwargs):
        assert isinstance(benchmarks, tuple)
        for key in benchmarks:
            assert isinstance(key, str)
            assert key not in cls._available_dispatchers, f'Shadowing existing benchmark dispatcher: "{key}"'
            super.__init_subclass__(**kwargs)
            cls._available_dispatchers[key] = cls

    @classmethod
    def by_name(cls, benchmark):
        """
        Return the BenchmarkCommandParser sub-class corresponding to a given benchmark.
        """
        try:
            return cls._available_dispatchers[benchmark]
        except KeyError:
            raise KeyError(f'Unknown benchmark (no dispatcher is registered): "{benchmark}"') from None

    @classmethod
    def dispatch(cls, *, args, bench_cmd, nix_cmd):
        """
        Dispatch arguments to the correct command builder.

        This procedure modifies bench_cmd and nix_cmd in place.
        """
        bench_cmd.args(*args)
        nix_cmd.path(cls.nix_path)


class STREAMParser(BenchmarkCommandParser, benchmarks=('stream_c', )):
    """
    Parsing logic for STREAM benchmark.
    """

    nix_path = pathlib.Path('stream.nix')

    @classmethod
    def dispatch(cls, *, args, bench_cmd, nix_cmd):
        # extract nix-shell arguments with a dedicated parser
        nix_args_parser = argparse.ArgumentParser(
            prog='STREAM',
            usage=argparse.SUPPRESS,
            add_help=False,
        )
        nix_args_parser.add_argument(
            '-n', '--iterationCount',
            type=int,
            dest='niter',
            metavar='iterationCount',
            required=True,
        )
        nix_args_parser.add_argument(
            '-s', '--problemSize',
            type=int,
            dest='psize',
            metavar='problemSize',
            required=True,
        )
        nix_args, bench_args = nix_args_parser.parse_known_intermixed_args(args)

        bench_cmd.args(*bench_args)
        nix_cmd.arg('nrmSupport', 'true') \
               .argstr('iterationCount', nix_args.niter) \
               .argstr('problemSize', nix_args.psize) \
               .path(cls.nix_path)


class AMGParser(BenchmarkCommandParser, benchmarks=('amg', )):
    """
    Parsing logic for Algebraic multigrid benchmark (AMG).
    """

    nix_path = pathlib.Path('amg.nix')

    @classmethod
    def dispatch(cls, *, args, bench_cmd, nix_cmd):
        nix_cmd.arg('nrmSupport', 'true')  # enable libnrm support
        super().dispatch(
            args=args,
            bench_cmd=bench_cmd,
            nix_cmd=nix_cmd,
        )


class NPBParser(BenchmarkCommandParser, benchmarks=('ep.A.x', 'ep.B.x', 'ep.C.x', 'ep.D.x', 'ep.E.x', )):
    """
    Parsing logic for NAS Parallel Benchmarks (NBP).
    """

    nix_path = pathlib.Path('nas.nix')


def forge_run_cmd(*, cmd, runner, user, hnrm_home, plan):
    """Forge a command description for `subprocess.run`."""

    program, args = cmd[0], cmd[1:]

    bench_cmd = command.Command(program)

    # prepare nix_cmd with common arguments
    nix_cmd = command.NixShellCommand() \
            .pure() \
            .arg('hnrmHome', hnrm_home)

    # assign arguments to relevant commands
    args_dispatcher = BenchmarkCommandParser.by_name(program)
    args_dispatcher.dispatch(
        args=args,
        bench_cmd=bench_cmd,
        nix_cmd=nix_cmd,
    )

    # wrap bench_cmd with experiment runner command
    runner_cmd = command.ProxyCommand(runner) \
                         .arg(plan) \
                         .command(bench_cmd)

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


# ==========  launcher  ==========

@helpers.manage_remaining_processes
def launch(params):  # pylint: disable=missing-function-docstring
    start_cmd = forge_run_cmd(
        cmd=params['cmd'],
        runner=params['config']['runners']['identification'],
        user=params['config']['xpctl']['user'],
        hnrm_home=params['config']['hnrm']['home'],
        plan=params['plan'],
    )
    print(start_cmd.build(), file=sys.stderr)  # XXX: logs
    subprocess.run(
        start_cmd.build(),
        cwd=params['config']['xpctl']['confdir'],
        check=True,
    )
