%define ver 0.2.1
%define rel 1
Summary: Python interface to MySQL-3.22
Name: MySQL-python
Version: %ver
Release: %rel
Copyright: Python-style
Group: Applications/Databases
Source: http://dustman.net/andy/python/MySQLdb/%ver/MySQLdb-%ver.tar.gz
URL: http://dustman.net/andy/python/MySQLdb
Requires: python >= 1.5.2
BuildRoot: /tmp/mysqldb-root
Packager: Andy Dustman <adustman@comstar.net>
#Icon: linux-python-db-icon.gif

%changelog

* Fri Mar 10 2000 Andy Dustman <adustman@comstar.net>

- change the name so that it's more of a MySQL package rather than
  a Python package.

* Tue Apr 06 1999 Andy Dustman <adustman@comstar.net>

- initial release

- mostly this spec is ripped off from Oli Andrich.

%description
Python interface to MySQL-3.22

MySQLdb is an interface to the popular MySQL database server for Python.
The design goals are:

-     Compliance with Python database API version 2.0 
-     Thread-safety 
-     Thread-friendliness (threads will not block each other) 
-     Compatibility with MySQL 3.22

This module should be mostly compatible with an older interface
written by Joe Skinner and others. However, the older version is
a) not thread-friendly, b) written for MySQL 3.21, c) apparently
not actively maintained. No code from that version is used in
MySQLdb. MySQLdb is distributed free of charge under a license
derived from the Python license.
%prep
%setup -n MySQLdb-%ver

%build
python build.py

%install
mkdir -p $RPM_BUILD_ROOT/usr/lib/python1.5/site-packages
make install prefix=$RPM_BUILD_ROOT/usr
cp MySQLdb.py{,c,o} $RPM_BUILD_ROOT/usr/lib/python1.5/site-packages
%clean
%files
%defattr(-, root, root)
%doc license.py examples/* doc/*
/usr/lib/python1.5/site-packages/MySQLdb.py
/usr/lib/python1.5/site-packages/MySQLdb.pyc
/usr/lib/python1.5/site-packages/MySQLdb.pyo
/usr/lib/python1.5/site-packages/_mysqlmodule.so
