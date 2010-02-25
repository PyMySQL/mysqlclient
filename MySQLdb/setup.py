#!/usr/bin/env python

import os
import sys
from setuptools import setup, Extension

if not hasattr(sys, "hexversion") or sys.hexversion < 0x02030000:
    raise Error("Python 2.3 or newer is required")

if os.name == "posix":
    from setup_posix import get_config
else: # assume windows
    from setup_windows import get_config

metadata, options = get_config()
metadata['ext_modules'] = [Extension(sources=['_mysql.c'], **options)]
metadata['long_description'] = metadata['long_description'].replace(r'\n', '')
setup(**metadata)
