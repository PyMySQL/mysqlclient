#!/usr/bin/env python

import os
import io

import setuptools

if os.name == "posix":
    from setup_posix import get_config
else:  # assume windows
    from setup_windows import get_config

with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

metadata, options = get_config()
metadata['ext_modules'] = [
    setuptools.Extension("MySQLdb._mysql", sources=['MySQLdb/_mysql.c'], **options)
]
metadata['long_description'] = readme
metadata['long_description_content_type'] = "text/markdown"
setuptools.setup(**metadata)
