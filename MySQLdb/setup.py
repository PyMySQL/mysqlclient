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

def config(what):
    if sys.platform == "win32":
        try:
            from win32pipe import popen
        except ImportError:
            print "win32pipe is required for building on Windows."
            print "Get it here: http://www.python.org/windows/win32/"
            raise
    else:
        from os import popen
    return popen("mysql_config --%s" % what).read().strip().split()

include_dirs = [ i[2:] for i in config('include') ]

if mysqlclient == "mysqlclient":
    libs = config("libs")
elif mysqlclient == "mysqlclient_r":
    libs = config("libs_r")
elif mysqlclient == "mysqld":
    libs = config("embedded")
library_dirs = [ i[2:] for i in libs if i[:2] == "-L" ]
libraries = [ i[2:] for i in libs if i[:2] == "-l" ]

# For reasons I do not understand, mysql_client --libs includes -lz
# but --libs_r does *not*. This has to be a bug...
# http://bugs.mysql.com/bug.php?id=6273

if sys.platform == "win32":
    if "zlib" not in libraries:
        libraries.append("zlib")
else:
    if "z" not in libraries:
        libraries.append("z")

extra_compile_args = config("cflags")

# avoid frightening noobs with warnings about missing directories
include_dirs = [ d for d in include_dirs if os.path.isdir(d) ]
library_dirs = [ d for d in library_dirs if os.path.isdir(d) ]

classifiers = """
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
Topic :: Database :: Database Engines/Servers
"""

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
    'classifiers': [ c for c in classifiers.split('\n') if c ],
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
            libraries=libraries,
            extra_compile_args=extra_compile_args,
            ),
        ],
    }

setup(**metadata)
