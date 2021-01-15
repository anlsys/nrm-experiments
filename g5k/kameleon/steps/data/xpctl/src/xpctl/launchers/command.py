# -*- coding: utf-8 -*-

"""
Command builder.

Helper classes to build commands bits by bits (inspired by Rust's
`std::process::Command`).
"""

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
