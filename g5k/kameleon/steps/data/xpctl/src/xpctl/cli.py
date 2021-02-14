#-*- coding: utf-8 -*-

"""
Logic to handle the Command Line Interface (CLI) of the main command.
"""

import collections

import cerberus
import click
import ruamel.yaml

from . import schemas


# ==========  helpers  ==========

def read_xpctl_config(_ctx, _param, value):
    """Read a valid xpctl configuration file."""

    yaml_parser = ruamel.yaml.YAML(typ='safe', pure=True)
    raw_config = yaml_parser.load(value)

    validator = cerberus.Validator(schema=schemas.XPCTL_CONF_SCHEMA)
    config = validator.validated(raw_config)

    if config is None:
        raise click.BadParameter('bogus configuration file')

    if config['version'] != schemas.XPCTL_CONF_VERSION:
        raise click.BadParameter(f'invalid version of configuration format, expected version {schemas.XPCTL_CONF_VERSION}')

    return config


# ==========  CLI logic  ==========

# -----  main command  -----

@click.group()
@click.option(
    '-F', '--config-file', 'config',
    envvar='XPCTL_CONF',
    type=click.File(mode='r'),
    callback=read_xpctl_config,
    required=True,
    help='Specify which configuration file to use.',
    show_envvar=True,
)
@click.option(
    '-c', '--clean-remaining-processes', 'clean',
    is_flag=True,
    flag_value=True,
    help='Clean remaining processes from previous experiments.',
)
def cli(config, clean):
    """
    Experiments management tool.

    \b
    This is the main command, see sub-commands for available actions.
    Options at this level are propagated to sub-commands.
    """
    click.echo('Main cmd')


# -----  Jupyter sub-command  -----

@cli.command()
@click.pass_context  # let sub-command access its parent's params
def jupyter(ctx):
    """Launch Jupyter notebook."""

    click.echo('jupyter sub-cmd')
    params = collections.ChainMap(ctx.params, ctx.parent.params)

    from .launchers.jupyter import launch  # pylint: disable=import-outside-toplevel
    launch(params)


# -----  identification experiment sub-command  -----

@cli.command()
@click.option(
    '-p', '--experiment-plan', 'plan',
    type=click.Path(exists=True, readable=True),
    required=True,
    help='Experiment plan.',
    metavar='PATH',
)
@click.argument(
    'cmd',
    nargs=-1,
    type=click.UNPROCESSED,
    required=True,
)
@click.pass_context  # let sub-command access its parent's params
def identification(ctx, plan, cmd):
    """Launch identification experiment."""

    click.echo('identification sub-cmd')
    params = collections.ChainMap(ctx.params, ctx.parent.params)

    from .launchers.identification import launch  # pylint: disable=import-outside-toplevel
    launch(params)


# -----  controller experiment sub-command  -----

@cli.command()
@click.option(
    '-c', '--controller-configuration', 'ctrl_config',
    type=click.Path(exists=True, readable=True),
    required=True,
    help='Controller configuration.',
    metavar='PATH',
)
@click.argument(
    'cmd',
    nargs=-1,
    type=click.UNPROCESSED,
    required=True,
)
@click.pass_context  # let sub-command access its parent's params
def controller(ctx, ctrl_config, cmd):
    """Launch controller experiment."""

    click.echo('controller sub-cmd')
    params = collections.ChainMap(ctx.params, ctx.parent.params)

    from .launchers.controller import launch  # pylint: disable=import-outside-toplevel
    launch(params)
