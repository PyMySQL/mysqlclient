#!/usr/bin/env python

"""\
=========================
Python interface to MySQL
=========================

MySQLdb is an interface to the popular MySQL_ database server for
Python.  The design goals are:

- Compliance with Python database API version 2.0 [PEP-0249]_

- Thread-safety

- Thread-friendliness (threads will not block each other) 

MySQL-3.22 through 4.1 and Python-2.3 through 2.4 are currently
supported.

MySQLdb is `Free Software`_.

.. _MySQL: http://www.mysql.com/
.. _`Free Software`: http://www.gnu.org/
.. [PEP-0249] http://www.python.org/peps/pep-0249.html

"""

import os
import sys
from distutils.core import setup
from distutils.extension import Extension

mysqlclient = os.getenv('mysqlclient', 'mysqlclient')
mysqloptlibs = os.getenv('mysqloptlibs', '').split()
embedded_server = (mysqlclient == 'mysqld')

name = "MySQL-%s" % os.path.basename(sys.executable)
if embedded_server:
    name = name + "-embedded"
version = "1.1.8"

# include files and library locations should cover most platforms
include_dirs = [
    '/usr/local/include/mysql',
    '/usr/local/mysql/include',
    '/usr/local/mysql/include/mysql',
    '/usr/include/mysql', 
    ]
library_dirs = [
    '/usr/local/lib/mysql',
    '/usr/local/mysql/lib',
    '/usr/local/mysql/lib/mysql',
    '/usr/lib/mysql',
    ]

libraries = [mysqlclient] + mysqloptlibs

# On some platorms, this can be used to find the shared libraries
# at runtime, if they are in a non-standard location. Doesn't
# work for Linux gcc.
runtime_library_dirs = []

# This can be used to force linking against static libraries.
extra_objects = []

# Sometimes the compiler or linker needs an extra switch to make
# things work.
extra_compile_args = []
extra_link_args = []

if sys.platform == "netbsd1":
    include_dirs = ['/usr/pkg/include/mysql']
    library_dirs = ['/usr/pkg/lib/mysql']
elif sys.platform in ("freebsd4", "openbsd3"):
    LOCALBASE = os.getenv('LOCALBASE', '/usr/local')
    include_dirs = ['%s/include/mysql' % LOCALBASE]
    library_dirs = ['%s/lib/mysql' % LOCALBASE]
elif sys.platform == "sunos5": # Solaris 2.8 + gcc
    runtime_library_dirs.append('/usr/local/lib:/usr/openwin/lib:/usr/dt/lib') 
    extra_compile_args.append("-fPIC")
elif sys.platform == "win32": # Ugh
    include_dirs = [r'c:\mysql\include']
    library_dirs = [r'c:\mysql\lib\opt']
    libraries.extend(['zlib', 'msvcrt', 'libcmt', 'wsock32', 'advapi32'])
    extra_objects = [r'c:\mysql\lib\opt\mysqlclient.lib']
elif sys.platform == "cygwin":
    include_dirs = ['/c/mysql/include']
    library_dirs = ['/c/mysql/lib']
    extra_compile_args.append('-DMS_WIN32')
elif sys.platform[:6] == "darwin": # Mac OS X
    include_dirs.append('/sw/include/mysql')
    library_dirs.append('/sw/lib/mysql')
    extra_link_args.append('-flat_namespace')
elif sys.platform == 'linux2' and os.getenv('HOSTTYPE') == 'alpha':
    libraries.extend(['ots', 'cpml'])
elif os.name == "posix": # UNIX-ish platforms not covered above
    pass # default should work
else:
    raise "UnknownPlatform", "sys.platform=%s, os.name=%s" % \
          (sys.platform, os.name)

# avoid frightening noobs with warnings about missing directories
include_dirs = [ d for d in include_dirs if os.path.isdir(d) ]
library_dirs = [ d for d in library_dirs if os.path.isdir(d) ]

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Other Environment
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: MacOS :: MacOS X
Operating System :: Microsoft :: Windows :: Windows NT/2000
Operating System :: OS Independent
Operating System :: POSIX
Operating System :: POSIX :: Linux
Operating System :: Unix
Programming Language :: C
Programming Language :: Python
Topic :: Database
Topic :: Database :: Database Engines/Servers""".split('\n')

metadata = {
    'name': name,
    'version': version,
    'description': "Python interface to MySQL",
    'long_description': __doc__,
    'author': "Andy Dustman",
    'author_email': "andy@dustman.net",
    'license': "GPL",
    'platforms': "ALL",
    'url': "http://sourceforge.net/projects/mysql-python",
    'download_url': "http://prdownloads.sourceforge.net/mysql-python/" \
                    "MySQL-python-%s.tar.gz" % version,
    'classifiers': classifiers,
    'py_modules': [
        "_mysql_exceptions",
        "MySQLdb.converters",
        "MySQLdb.connections",
        "MySQLdb.cursors",
        "MySQLdb.sets",
        "MySQLdb.times",
        "MySQLdb.stringtimes",
        "MySQLdb.mxdatetimes",
        "MySQLdb.pytimes",
        "MySQLdb.constants.CR",
        "MySQLdb.constants.FIELD_TYPE",
        "MySQLdb.constants.ER",
        "MySQLdb.constants.FLAG",
        "MySQLdb.constants.REFRESH",
        "MySQLdb.constants.CLIENT",
        ],
    'ext_modules': [
        Extension(
            name='_mysql',
            sources=['_mysql.c'],
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            runtime_library_dirs=runtime_library_dirs,
            libraries=libraries,
            extra_objects=extra_objects,
            extra_link_args=extra_link_args,
            extra_compile_args=extra_compile_args,
            ),
        ],
    }

setup(**metadata)
