#!/usr/bin/env python

"""Setup script for the MySQLdb module distribution."""

import os, sys
from distutils.core import setup
from distutils.extension import Extension

YES = 1
NO = 0

# set this to 1 if you have the thread-safe mysqlclient library
thread_safe_library = NO

# You probably don't have to do anything past this point. If you
# do, please mail me the configuration for your platform. Don't
# forget to include the value of sys.platform and os.name.

mysqlclient = thread_safe_library and "mysqlclient_r" or "mysqlclient"

if sys.platform == "linux-i386": # Red Hat
    include_dirs = ['/usr/include/mysql']
    library_dirs = ['/usr/lib/mysql']
    libraries = [mysqlclient, "z"]
    runtime_library_dirs = []
    extra_objects = []
elif sys.platform in ("freebsd4", "openbsd2"): 
    include_dirs = ['/usr/local/include/mysql']
    library_dirs = ['/usr/local/lib/mysql']
    libraries = [mysqlclient, "z"]
    runtime_library_dirs = []
    extra_objects = []
elif sys.platform == "win32":
    include_dirs = [r'c:\mysql\include']
    library_dirs = [r'c:\mysql\lib\opt']
    libraries = [mysqlclient, 'zlib', 'msvcrt', 'libcmt',
                 'wsock32', 'advapi32']
    runtime_library_dirs = []
    extra_objects = [r'c:\mysql\lib\opt\mysqlclient.lib']
elif os.name == "posix": # most Linux/UNIX platforms
    include_dirs = ['/usr/include/mysql']
    library_dirs = ['/usr/lib/mysql']
    # MySQL-3.23 seems to need libz
    libraries = [mysqlclient, "z"]
    # On some platorms, this can be used to find the shared libraries
    # at runtime, if they are in a non-standard location. Doesn't
    # work for Linux gcc.
    ## runtime_library_dirs = library_dirs
    runtime_library_dirs = []
    # This can be used on Linux to force use of static mysqlclient lib
    ## extra_objects = ['/usr/lib/mysql/libmysqlclient.a']
    extra_objects = []
else:
    raise "UnknownPlatform", "sys.platform=%s, os.name=%s" % \
          (sys.platform, os.name)
    
long_description = \
"""Python interface to MySQL-3.23

MySQLdb is an interface to the popular MySQL database server for Python.
The design goals are:

-     Compliance with Python database API version 2.0 
-     Thread-safety 
-     Thread-friendliness (threads will not block each other) 
-     Compatibility with MySQL-3.23 and later

This module should be mostly compatible with an older interface
written by Joe Skinner and others. However, the older version is
a) not thread-friendly, b) written for MySQL 3.21, c) apparently
not actively maintained. No code from that version is used in
MySQLdb. MySQLdb is free software.

"""

setup (# Distribution meta-data
        name = "MySQL-python",
        version = "0.9.0b2",
        description = "An interface to MySQL",
	long_description=long_description,
        author = "Andy Dustman",
        author_email = "andy@dustman.net",
        url = "http://dustman.net/andy/python/MySQLdb",

        # Description of the modules and packages in the distribution

        py_modules = ["CompatMysqldb",
                      "_mysql_exceptions",
                      "MySQLdb.converters",
                      "MySQLdb.connections",
                      "MySQLdb.cursors",
                      "MySQLdb.data",
                      "MySQLdb.constants.CR",
                      "MySQLdb.constants.FIELD_TYPE",
                      "MySQLdb.constants.ER",
                      "MySQLdb.constants.FLAG",
                      "MySQLdb.constants.REFRESH",
                      "MySQLdb.constants.CLIENT",
                     ],

        ext_modules = [Extension(
                name='_mysql',
                sources=['_mysql.c'],
                include_dirs=include_dirs,
                library_dirs=library_dirs,
		runtime_library_dirs=runtime_library_dirs,
                libraries=libraries,
		extra_objects=extra_objects,
                )],
)
