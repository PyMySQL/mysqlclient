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

if sys.platform == "linux-386": # Red Hat
    include_dirs = ['/usr/include/mysql']
    library_dirs = ['/usr/lib/mysql']
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
    
setup (# Distribution meta-data
        name = "MySQLdb",
        version = "0.3.0b2",
        description = "An interface to MySQL",
        author = "Andy Dustman",
        author_email = "andy@dustman.net",
        url = "http://dustman.net/andy/python/MySQLdb",

        # Description of the modules and packages in the distribution

        py_modules = ["MySQLdb", "CompatMysqldb"],

        ext_modules = [Extension(
                name='_mysqlmodule',
                sources=['_mysqlmodule.c'],
                include_dirs=include_dirs,
                library_dirs=library_dirs,
		runtime_library_dirs=runtime_library_dirs,
                libraries=libraries,
		extra_objects=extra_objects,
                )],
)
