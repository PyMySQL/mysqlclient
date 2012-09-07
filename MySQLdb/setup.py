#!/usr/bin/env python

import os
import sys

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup, Extension

if not hasattr(sys, "hexversion") or sys.hexversion < 0x02040000:
    raise Error("Python 2.4 or newer is required")

if os.name == "posix":
    from setup_posix import get_config
else: # assume windows
    from setup_windows import get_config

metadata, options = get_config()
metadata['ext_modules'] = [Extension(sources=['_mysql.c'], **options)]
metadata['long_description'] = metadata['long_description'].replace(r'\n', '')
setup(**metadata)
