# -*- coding: utf-8 -*-

"""
Schemas of configuration files.

Configuration files used by xpctl must be valid with respect to the
configuration schemas defined in this module.
"""

import pathlib

import cerberus


cerberus.Validator.types_mapping['path'] = \
        cerberus.TypeDefinition('path', (pathlib.Path, ), ())

XPCTL_CONF_VERSION = 2  # current version of configuration format

XPCTL_CONF_SCHEMA = {
    'version': {
        'type': 'integer',
        'min': 1,
        'required': True,
    },
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
    'xpctl': {
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
    'runners': {
        'type': 'dict',
        'empty': False,
        'required': True,
        'keysrules': {
            'type': 'string',
        },
        'valuesrules': {
            'type': 'path',
            'coerce': pathlib.Path,
        }
    },
}
