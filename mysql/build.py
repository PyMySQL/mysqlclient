#!/usr/bin/env python

import license
print license.__doc__

import sys, os
# XXX probably will only work right on UNIX only.
version = sys.version[:3]
lversion = sys.version[:5]
if lversion < '1.5.2':
    print "You need at least Python-1.5.2. You have:"
    print sys.version
    sys.exit(1)
prefix = sys.exec_prefix
config = "%s/lib/python%s/config" % (prefix, version)
os.system("cp %s/Makefile.pre.in ." % config)
os.system("make -f Makefile.pre.in boot")
os.system("make")
try: import _mysql
except ImportError, m:
    print "Whoa, couldn't import _mysql: %s" % str(m)
    print "Probably _mysqlmodule.so didn't compile correctly."
    print "Or your library paths may be bad. Check the FAQ."
    sys.exit(1)
import MySQLdb
os.system("python -O -c 'import MySQLdb'")
print """Now, as root, run:
make install
cp MySQLdb.py{,c,o} %s/lib/python%s/site-packages""" % (prefix, version)
