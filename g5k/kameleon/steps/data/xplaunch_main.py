#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import contextlib
import functools
import os
import pathlib
import signal
import subprocess
import sys

import cerberus
import ruamel.yaml


##  CONFIGURATION FORMATS  #####################################################

PATH_TYPE = cerberus.TypeDefinition('path', (pathlib.Path, ), ())
cerberus.Validator.types_mapping[PATH_TYPE.name] = PATH_TYPE

XPLAUNCH_CONF_SCHEMA = {
    'hnrm': {
        'type': 'dict',
        'required': True,
        'schema': {
            'home': {
                'type': 'path',
                'coerce': pathlib.Path,
                'required': True,
            },
        },
    },
    'xplaunch': {
        'type': 'dict',
        'required': True,
        'schema': {
            'user': {
                'type': 'string',
                'required': True,
            },
            'confdir': {
                'type': 'path',
                'coerce': pathlib.Path,
                'required': True,
            },
        },
    },
}


##  COMMON HELPERS  ############################################################

def manage_remaining_processes(func=None, *, forceclean=False):
    """Deals with processes remaining from previous experiments.

    Args:
        forceclean: Override --clean-remaining-processes option.
    """
    if func is None:
        return functools.partial(manage_remaining_processes, forceclean=forceclean)

    @functools.wraps(func)
    def wrapper(args):
        args.clean = args.clean or forceclean  # override clean
        #
        print(f'Checking for remaining processes owned by {args.config["xplaunch"]["user"]}', file=sys.stderr)  # XXX: logs
        check_remaining_processes = subprocess.run(
            ['pgrep', '--list-full', '--euid', args.config['xplaunch']['user'], ],
            check=False,
        )
        if check_remaining_processes.returncode not in (0, 1):
            raise subprocess.SubprocessError(
                check_remaining_processes.returncode,
                check_remaining_processes.args,
            )
        if check_remaining_processes.returncode == 0:  # One or more processes matched the criteria (cf. pgrep(1))
            print(f'Found remaining processes owned by {args.config["xplaunch"]["user"]}', file=sys.stderr)  # XXX: logs
            if args.clean:
                print('Clean option active: killing remaining processes', file=sys.stderr)  # XXX: logs
                subprocess.check_call(
                    ['pkill', '--euid', args.config['xplaunch']['user'], ]
                )
            else:
                print('Clean option inactive: aborting', file=sys.stderr)  # XXX: logs
                sys.exit(1)
        #
        return func(args)

    return wrapper


@contextlib.contextmanager
def signal_handler(signalnum, handler):
    orig_handler = signal.signal(signalnum, handler)
    try:
        yield
    finally:
        signal.signal(signalnum, orig_handler)


def wrap_command(cmd, *, runas, nixargs):
    assert isinstance(nixargs, (list, tuple))
    assert isinstance(cmd, (list, tuple))

    runuser_prefix = ['runuser', '-u', runas, '--']
    nix_cmd = ['nix-shell', *nixargs, '--run']

    cmd = runuser_prefix + nix_cmd + [' '.join(map(str, cmd))]
    print(cmd, file=sys.stderr)  # XXX: logs
    return cmd


def _populate_config(conf_path):
    conf_path = pathlib.Path(conf_path)
    print(f'Using configuration file "{conf_path}"', file=sys.stderr)  # XXX: logs

    yaml_parser = ruamel.yaml.YAML(typ='safe', pure=True)  # XXX: pure=True required with ruamel v0.15.34 (debian buster)
    raw_config = yaml_parser.load(conf_path)

    validator = cerberus.Validator(schema=XPLAUNCH_CONF_SCHEMA)
    config = validator.validated(raw_config)

    if config is None:
        raise ValueError(f'Invalid configuration file "{conf_path}"')

    return config


def _build_xplcmd_path(xplcmd):
    """Build the path for the xplaunch command xplcmd."""
    assert isinstance(xplcmd, str)
    main_path = pathlib.Path(__file__)

    cmd_stems = main_path.stem.rsplit(sep='_', maxsplit=1)
    assert cmd_stems[-1] == 'main'
    cmd_stems[-1] = xplcmd
    cmd_stem = '_'.join(cmd_stems)

    return main_path.with_name(cmd_stem + main_path.suffix)


##  JUPYTER  ###################################################################

@manage_remaining_processes(forceclean=True)
def jupyter_subcmd(args=None):
    print(args, file=sys.stderr)  # XXX: logs

    def _clean_jupyter_stop_on_sigint(signum, _):
        assert signum == signal.SIGINT
        print('Caught SIGINT, shutting down Jupyter: please be patient', file=sys.stderr)  # XXX: logs
        stop_cmd = wrap_command(
            ('jupyter-notebook', 'stop'),
            nixargs=(
                '--pure',
                '--arg', 'jupyter', 'true',
                '--arg', 'experiment', 'true',
            ),
            runas=args.config['xplaunch']['user']
        )
        subprocess.run(  # ask jupyter notebook to shutdown
            stop_cmd,
            cwd=args.config['hnrm']['home'],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    with signal_handler(signal.SIGINT, _clean_jupyter_stop_on_sigint):
        jupyter_cmd = (
            'jupyter-notebook',
            '--no-browser',
            '--ip="0.0.0.0"',
            '--NotebookApp.default_url=/tree/notebooks',
        )
        start_cmd = wrap_command(
            jupyter_cmd,
            nixargs=(
                '--pure',
                '--arg', 'jupyter', 'true',
                '--arg', 'experiment', 'true',
            ),
            runas=args.config['xplaunch']['user']
        )
        subprocess.run(
            start_cmd,
            cwd=args.config['hnrm']['home'],
            check=False,
            preexec_fn=os.setsid,  # create a dedicated session for processes created by jupyter
        )


##  BENCHMARK PARSERS  #########################################################
"""
Benchmark parsing logic.

The benchmark parsing functions build the configuration out of the supplied
command line.
"""

def default_benchmark_parser(cmd, nixshell, enable_libnrm=False):
    """Dummy benchmark parser forwarding cmd as is."""
    assert isinstance(cmd, (list, tuple))
    assert isinstance(enable_libnrm, bool)
    benchmark_conf = {
        'nixshell': pathlib.Path(nixshell),
        'cmd': cmd,
        'nixargs': ('--arg', 'nrmSupport', 'true') if enable_libnrm else (),
    }
    return benchmark_conf


def stream_benchmark_parser(cmd):
    """Benchmark parser for stream: extracts nix-shell pseudo-arguments."""
    assert isinstance(cmd, (list, tuple))

    # extract nix-shell arguments with a dedicated parser
    nixargs_parser = argparse.ArgumentParser(
        prog=cmd[0],
        add_help=False,
    )
    nixargs_parser.add_argument(
        '-n', '--iterationCount',
        type=int,
        dest='niter',
        metavar='iterationCount',
        required=True,
    )
    nixargs_parser.add_argument(
        '-s', '--problemSize',
        type=int,
        dest='psize',
        metavar='problemSize',
        required=True,
    )
    nixargs, other_args = nixargs_parser.parse_known_intermixed_args(cmd[1:])

    # build benchmark description
    benchmark_conf = {
        'nixshell': pathlib.Path('stream.nix'),
        'cmd': (cmd[0], *other_args),
        'nixargs': (
            '--arg', 'nrmSupport', 'true',
            '--argstr', 'iterationCount', str(nixargs.niter),
            '--argstr', 'problemSize', str(nixargs.psize),
        ),
    }
    return benchmark_conf


def parse_benchmark_command(cmd):
    BENCHMARK_PARSERS = {
        # STREAM benchmark
        'stream_c': stream_benchmark_parser,
        # Algebraic multigrid benchmark (AMG)
        'amg': functools.partial(default_benchmark_parser, nixshell='amg.nix', enable_libnrm=True),
        # NAS Parallel Benchmarks
        'ep.A.x': functools.partial(default_benchmark_parser, nixshell='nas.nix'),
        'ep.B.x': functools.partial(default_benchmark_parser, nixshell='nas.nix'),
        'ep.C.x': functools.partial(default_benchmark_parser, nixshell='nas.nix'),
        'ep.D.x': functools.partial(default_benchmark_parser, nixshell='nas.nix'),
        'ep.E.x': functools.partial(default_benchmark_parser, nixshell='nas.nix'),
    }
    return BENCHMARK_PARSERS[cmd[0]](cmd)


##  STATIC GAIN  ###############################################################

def _build_run_cmd(cmd, *, runcmd):
    assert isinstance(cmd, (list, tuple))
    assert isinstance(runcmd, (list, tuple))
    return (*runcmd, '--', *cmd)


@manage_remaining_processes
def static_gain_subcmd(args=None):
    # check/format cmd
    assert isinstance(args.cmd, list)
    if not args.cmd:
        raise ValueError('missing command')
    dash_dash, *cmd = args.cmd
    if dash_dash != '--':
        raise ValueError('missing "--" between experiment options and command to run')
    if not cmd:
        raise ValueError('missing command')  # args.cmd == ['--']
    args.cmd = cmd  # remove leading --

    print(args, file=sys.stderr)  # XXX: logs

    benchmark_conf = parse_benchmark_command(cmd)
    cmd = wrap_command(
        cmd=_build_run_cmd(
            benchmark_conf['cmd'],
            runcmd=(_build_xplcmd_path('run_static_gain'), str(args.pcap)),
        ),
        nixargs=(
            '--pure',
            '--arg', 'hnrmHome', args.config['hnrm']['home'],
            *benchmark_conf['nixargs'],
            benchmark_conf['nixshell'],
        ),
        runas=args.config['xplaunch']['user']
    )
    subprocess.run(
        cmd,
        cwd=args.config['xplaunch']['confdir'],
        check=True,
    )


##  MAIN  ######################################################################

def main(args=None):

    # top-level parser definition (dispatch to relevant sub-command)  ##########
    toplevel_parser = argparse.ArgumentParser()
    toplevel_parser.add_argument(
        '-F', '--config-file',
        default=os.environ.get('XPLAUNCH_CONF'),
        dest='config',
        metavar='configfile',
        help='specify an alternate configuration file',
    )
    toplevel_parser.add_argument(
        '-c', '--clean-remaining-processes',
        action='store_true',
        dest='clean',
        help='clean remaining processes from previous experiments',
    )
    toplevel_parser.set_defaults(handler=lambda args: toplevel_parser.print_usage())
    #
    subparsers = toplevel_parser.add_subparsers(
        title='sub-commands',
        # dest='subcmd',
    )


    # jupyter_subcmd parser definition  ########################################

    jupyter_parser = subparsers.add_parser(
        'jupyter',
        description='launch jupyter notebook',
    )
    jupyter_parser.set_defaults(handler=jupyter_subcmd)


    # static_gain_subcmd parser definition  ####################################

    class _UniqueStore(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if getattr(namespace, self.dest, self.default) is not self.default:
                parser.error(option_string + " appears several times.")
            setattr(namespace, self.dest, values)

    def _powercap(string):
        try:
            pcap = int(string)
        except ValueError as err:
            msg = f'unable to parse as an integer: "{string}"'
            raise argparse.ArgumentTypeError(msg) from err
        if pcap <= 0:
            msg = f'invalid powercap: "{pcap}"'
            raise argparse.ArgumentTypeError(msg)
        return pcap

    static_gain_parser = subparsers.add_parser(
        'static-gain',
        description='run static gain experiment',
    )
    static_gain_parser.add_argument(
        '-p', '--powercap',
        type=_powercap,
        action=_UniqueStore,
        required=True,
        dest='pcap',
        metavar='powercap',
        help='RAPL maximum power (in watts)',
    )
    static_gain_parser.add_argument(  # XXX: replace with parse_known_args?
        'cmd',
        nargs=argparse.REMAINDER,
        help='command to be executed',
    )
    static_gain_parser.set_defaults(handler=static_gain_subcmd)


    # run!  ####################################################################
    options = toplevel_parser.parse_args(args)  # parse arguments
    options.config = _populate_config(options.config)
    options.handler(options)  # call handler for given sub-command


##  DO THE JOB!  ###############################################################

if __name__ == '__main__':
    main()
