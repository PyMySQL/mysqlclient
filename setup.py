#!/usr/bin/env python

import os

import setuptools

REQUIRES = ['setuptools-scm']

if os.name == "posix":
    from setup_posix import get_config
else:  # assume windows
    from setup_windows import get_config

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

metadata, options = get_config()

metadata['packages'] = setuptools.find_namespace_packages(include=['tiledb.*'])

metadata['ext_modules'] = [
    setuptools.Extension("tiledb.sql._mysql", sources=['tiledb/sql/_mysql.c'], **options)
]
metadata['long_description'] = readme
metadata['long_description_content_type'] = "text/markdown"
metadata["python_requires"] = ">=3.5"
# Add package data for installing errmsg.sys
# MANIFEST.in seems to work for most cases, but some people report needing this so lets include it
metadata['package_data'] = {
    '': ['errmsg.sys'],
}

metadata['include_package_data'] = True
metadata['zip_safe'] = False

metadata['install_requires'] = ['setuptools-scm']

setuptools.setup(**metadata)
