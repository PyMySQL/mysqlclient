#!/usr/bin/env python

import os
import sys
from distutils.core import setup
from distutils.extension import Extension

if sys.version_info < (2, 3):
    raise Error, "Python-2.3 or newer is required"

if os.name == "posix":
    from setup_posix import get_config
else: # assume windows
    from setup_windows import get_config

metadata, options = get_config()
metadata['ext_modules'] = [Extension(sources=['_mysql.c'], **options)]
setup(**metadata)
