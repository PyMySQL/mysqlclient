#!/usr/bin/env python

"""Setup script for the MySQLdb module distribution."""

import os
from distutils.core import setup
from distutils.extension import Extension

# You may need to edit this script to point to the location of your
# MySQL installation.  It should be sufficient to change the value of
# the MYSQL_DIR variable below.
MYSQL_INCLUDE_DIR = '/usr/include/mysql'
MYSQL_LIB_DIR = '/usr/lib/mysql'

setup (# Distribution meta-data
        name = "MySQLdb",
        version = "0.2.2",
        description = "An interface to MySQL",
        author = "Andy Dustman",
        author_email = "andy@dustman.net",
        url = "http://dustman.net/andy/python/MySQLdb",

        # Description of the modules and packages in the distribution

        py_modules = ["MySQLdb", "CompatMysqldb"],

        ext_modules = [Extension(
                name='_mysqlmodule',
                sources=['_mysqlmodule.c'],
                include_dirs=[MYSQL_INCLUDE_DIR],
		# maybe comment to force dynamic libraries
                # library_dirs=[MYSQL_LIB_DIR],
		# uncomment if linking against dynamic libraries
		runtime_library_dirs=[MYSQL_LIB_DIR],
                libraries=['mysqlclient',
			'z', # needed for MyZQL-3.23
                        # Some C++ compiler setups "forget" to
                        # link to the c++ libs (notably on
                        # Solaris), so you might succeed in
                        # linking them in by hand:
                        # 'stdc++', 'gcc',
                        ],
		# uncomment to force use of the static library
		# extra_objects=[`MYSQL_LIB_DIR`+'libmysqlclient.a'],
                )]
)
