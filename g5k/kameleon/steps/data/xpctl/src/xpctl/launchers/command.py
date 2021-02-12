# -*- coding: utf-8 -*-

"""
Command builder.

Helper classes to build commands bits by bits (inspired by Rust's
`std::process::Command`).

The module is organized in two class hierarchies:
    1. `Command` and its sub-classes are used to build commands compatible with
       `subprocess.run`
    2. `BenchmarkCommandBuilder` and its sub-classes are used to parse
        benchmark commands, and build the `Command` to run the benchmark
"""

import argparse
import pathlib


class Command:
    """Generic command."""

    def __init__(self, program):
        self._args = [str(program)]

    def arg(self, arg):
        """Add an argument to pass to the program."""
        self._args.append(str(arg))
        return self

    def args(self, *args):
        """Add multiple arguments to pass to the program."""
        self._args.extend(map(str, args))
        return self

    def build(self):
        """Build a suitable args to be fed to subprocess.run for this Command."""
        return tuple(self._args)

    def __str__(self):
        return ' '.join(self.build())


class NixShellCommand(Command):
    """`nix-shell` command."""

    def __init__(self):
        super().__init__('nix-shell')
        self._path = None

    def arg(self, name, value):  # pylint: disable=arguments-differ
        """Assign the Nix expression value to name."""
        super().args('--arg', name, value)
        return self

    def argstr(self, name, value):
        """Assign the string value to name."""
        super().args('--argstr', name, value)
        return self

    def option(self, name, value):
        """Set the Nix configuration option name to value."""
        super().args('--option', name, value)
        return self

    def pure(self):
        """Ask for a pure shell."""
        super().arg('--pure')
        return self

    def command(self, cmd, *, interactive=False):
        """Set the command to execute within the nix-shell."""
        optstring = '--command' if interactive else '--run'
        super().args(optstring, str(cmd))
        return self

    def path(self, path):
        """Set the path (file containing a derivation) argument of nix-shell."""
        assert isinstance(path, (str, pathlib.Path, ))
        if self._path is not None:
            raise RuntimeError('Cowardly refusing to re-assign path')
        self._path = str(path)
        return self

    def build(self):
        full_cmd = super().build()
        if self._path is not None:
            full_cmd = full_cmd + (self._path, )
        return full_cmd


class ProxyCommand(Command):
    """
    Build a command responsible to run another command.
    """

    def __init__(self, program):
        super().__init__(program)
        self._proxied_cmd = None

    def command(self, cmd):
        """Set the command to run with this ProxyCommand."""
        assert isinstance(cmd, Command)
        if self._proxied_cmd is not None:
            raise RuntimeError('Cowardly refusing to re-assign proxied command')
        self._proxied_cmd = cmd
        return self

    def build(self):
        if self._proxied_cmd is None:
            raise RuntimeError('Proxying empty command')
        full_cmd = super().build() + ('--', ) + self._proxied_cmd.build()
        return full_cmd


#-------------------------------------------------------------------------------

class BenchmarkCommandBuilder:
    """
    Benchmark command building logic.

    The benchmark command builder parses, and builds a `Command` out of the
    arguments supplied on the command line.

    .. warning::
        The BenchmarkCommandBuilder is not meant for direct use: it is built as
        an abstract factory class.

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
        Return the BenchmarkCommandBuilder sub-class corresponding to a given benchmark.
        """
        try:
            return cls._available_dispatchers[benchmark]
        except KeyError:
            raise KeyError(f'Unknown benchmark (no dispatcher is registered): "{benchmark}"') from None

    @classmethod
    def prepare_commands(cls, cmd):
        """
        Prepare commands to run the benchmark with respect to cmdline.

        Args:
            cmd: The list of token composing the benchmark raw command.

        Returns:
            The tuple of Commands (nix_cmd, bench_cmd), with arguments provided
            as required for the actual benchmark.
        """
        program, *args = cmd

        nix_cmd = NixShellCommand() \
                      .pure() \
                      .path(cls.nix_path)
        bench_cmd = Command(program) \
                        .args(*args)

        return nix_cmd, bench_cmd


class _STREAM(BenchmarkCommandBuilder, benchmarks=('stream_c', )):
    """
    Command building logic for STREAM benchmark.
    """

    nix_path = '<xpctl/stream.nix>'

    @classmethod
    def prepare_commands(cls, cmd):
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

        program, *args = cmd

        nix_cmd, _ = super().prepare_commands(cmd)
        bench_cmd = Command(program)  # do not feed args to bench_cmd yet

        # dispatch arguments to the relevant `Command`
        nix_args, bench_args = nix_args_parser.parse_known_intermixed_args(args)

        nix_cmd.arg('nrmSupport', 'true') \
               .argstr('iterationCount', nix_args.niter) \
               .argstr('problemSize', nix_args.psize)
        bench_cmd.args(*bench_args)

        return nix_cmd, bench_cmd


class _AMG(BenchmarkCommandBuilder, benchmarks=('amg', )):
    """
    Command building logic for Algebraic multigrid benchmark (AMG).
    """

    nix_path = '<xpctl/amg.nix>'

    @classmethod
    def prepare_commands(cls, cmd):
        nix_cmd, bench_cmd = super().prepare_commands(cmd)
        nix_cmd.arg('nrmSupport', 'true')  # enable libnrm support
        return nix_cmd, bench_cmd


class _NPB(BenchmarkCommandBuilder, benchmarks=('ep.A.x', 'ep.B.x', 'ep.C.x', 'ep.D.x', 'ep.E.x', )):
    """
    Command building logic for NAS Parallel Benchmarks (NBP).
    """

    nix_path = '<xpctl/nas.nix>'
