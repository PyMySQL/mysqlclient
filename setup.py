#!/usr/bin/env python

import os
import sys

import distutils.errors
import setuptools

if not hasattr(sys, "hexversion") or sys.hexversion < 0x02060000:
    raise distutils.errors.DistutilsError("Python 2.6 or newer is required")

if os.name == "posix":
    from setup_posix import get_config
else:  # assume windows
    from setup_windows import get_config

metadata, options = get_config()
metadata['ext_modules'] = [
    setuptools.Extension(sources=['_mysql.c'], **options)]
metadata['long_description'] = metadata['long_description'].replace(r'\n', '')
setuptools.setup(**metadata)
