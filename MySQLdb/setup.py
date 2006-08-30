#!/usr/bin/env python

class Abort(Exception): pass

import os
import sys
from distutils.core import setup
from distutils.extension import Extension
from ConfigParser import SafeConfigParser

if sys.version_info < (2, 3):
    raise Abort, "Python-2.3 or newer is required"

config = SafeConfigParser()
config.read(['metadata.cfg', 'site.cfg'])

metadata = dict(config.items('metadata'))
options = dict(config.items('options'))

metadata['py_modules'] = filter(None, metadata['py_modules'].split('\n'))
metadata['classifiers'] = filter(None, metadata['classifiers'].split('\n'))

def mysql_config(what):
    from os import popen
    f = popen("mysql_config --%s" % what)
    data = f.read().strip().split()
    if f.close(): data = []
    return data

# This dequote() business is required for some older versions
# of mysql_config

def dequote(s):
    if s[0] in "\"'" and s[0] == s[-1]:
        s = s[1:-1]
    return s

def enabled(option):
    value = options[option]
    s = value.lower()
    if s in ('yes','true','1','y'):
        return True
    elif s in ('no', 'false', '0', 'n'):
        return False
    else:
        raise Abort, "Unknown value %s for option %s" % (value, option)

if os.name == "posix":
    flag_prefix = "-"
else: # assume windows
    flag_prefix = "/"

def compiler_flag(f): return flag_prefix + f

extra_objects = []
static = enabled('static')
if enabled('embedded'):
    libs = mysql_config("libmysqld-libs")
    client = "mysqld"
elif enabled('threadsafe'):
    libs = mysql_config("libs_r")
    client = "mysqlclient_r"
    if not libs:
        libs = mysql_config("libs")
        client = "mysqlclient"
else:
    libs = mysql_config("libs")
    client = "mysqlclient"

name = "MySQL-%s" % os.path.basename(sys.executable)
if enabled('embedded'):
    name = name + "-embedded"
metadata['name'] = name

library_dirs = [ dequote(i[2:]) for i in libs if i.startswith(compiler_flag("L")) ]
libraries = [ dequote(i[2:]) for i in libs if i.startswith(compiler_flag("l")) ]

removable_compile_args = [ compiler_flag(f) for f in "ILl" ]
extra_compile_args = [ i for i in mysql_config("cflags")
                       if i[:2] not in removable_compile_args ]
include_dirs = [ dequote(i[2:])
                 for i in mysql_config('include')
                 if i.startswith(compiler_flag('I')) ]
if not include_dirs: # fix for MySQL-3.23
    include_dirs = [ dequote(i[2:])
		     for i in mysql_config('cflags')
		     if i.startswith(compiler_flag('I')) ]

if static:
    extra_objects.append(os.path.join(
        library_dirs[0],'lib%s.a' % client))

extra_compile_args.append(compiler_flag("Dversion_info=%s" % metadata['version_info']))
extra_compile_args.append(compiler_flag("D__version__=%s" % metadata['version']))

rel = open("MySQLdb/release.py",'w')
rel.write("""
__author__ = "%(author)s <%(author_email)s>"
version_info = %(version_info)s
__version__ = "%(version)s"
""" % metadata)
rel.close()

del metadata['version_info']

ext_mysql_metadata = dict(
    name="_mysql",
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_compile_args=extra_compile_args,
    extra_objects=extra_objects,
    sources=['_mysql.c'],
    )
if config.read(['site.cfg']):
    ext_mysql_metadata.update([ (k, v.split()) for k, v in config.items('compiler') ])
ext_mysql = Extension(**ext_mysql_metadata)
metadata['ext_modules'] = [ext_mysql]
setup(**metadata)
