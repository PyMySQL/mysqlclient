====================================
 MySQLdb Frequently Asked Questions
====================================

.. contents::
..


Build Errors
------------

  ld: fatal: library -lmysqlclient_r: not found

mysqlclient_r is the thread-safe library. It's not available on
all platforms, or all installations, apparently. You'll need to
reconfigure site.cfg (in MySQLdb-1.2.1 and newer) to have
threadsafe = False.

  mysql.h: No such file or directory

This almost always mean you don't have development packages
installed. On some systems, C headers for various things (like MySQL)
are distributed as a seperate package. You'll need to figure out
what that is and install it, but often the name ends with -devel.

Another possibility: Some older versions of mysql_config behave oddly
and may throw quotes around some of the path names, which confused
MySQLdb-1.2.0. 1.2.1 works around these problems. If you see things
like -I'/usr/local/include/mysql' in your compile command, that's
probably the issue, but it shouldn't happen any more.


ImportError
-----------

  ImportError: No module named _mysql 

If you see this, it's likely you did some wrong when installing
MySQLdb; re-read (or read) README. _mysql is the low-level C module
that interfaces with the MySQL client library.

Various versions of MySQLdb in the past have had build issues on
"weird" platforms; "weird" in this case means "not Linux", though
generally there aren't problems on Unix/POSIX platforms, including
BSDs and Mac OS X. Windows has been more problematic, in part because
there is no `mysql_config` available in the Windows installation of
MySQL. 1.2.1 solves most, if not all, of these problems, but you will
still have to edit a configuration file so that the setup knows where
to find MySQL and what libraries to include.


  ImportError: libmysqlclient_r.so.14: cannot open shared object file: No such file or directory 

The number after .so may vary, but this means you have a version of
MySQLdb compiled against one version of MySQL, and are now trying to
run it against a different version. The shared library version tends
to change between major releases.

Solution: Rebuilt MySQLdb, or get the matching version of MySQL.

Another thing that can cause this: The MySQL libraries may not be on
your system path.

Solutions:

* set the LD_LIBRARY_PATH environment variable so that it includes
  the path to the MySQL libraries.

* set static=True in site.cfg for static linking

* reconfigure your system so that the MySQL libraries are on the
  default loader path. In Linux, you edit /etc/ld.so.conf and run
  ldconfig. For Solaris, see `Linker and Libraries Guide
  <http://docs.sun.com/app/docs/doc/817-3677/6mj8mbtbe?a=view>`_.


  ImportError: ld.so.1: python: fatal: libmtmalloc.so.1: DF_1_NOOPEN tagged object may not be dlopen()'ed 

This is a weird one from Solaris. What does it mean? I have no idea.
However, things like this can happen if there is some sort of a compiler
or environment mismatch between Python and MySQL. For example, on some
commercial systems, you might have some code compiled with their own
compiler, and other things compiled with GCC. They don't always mesh
together. One way to encounter this is by getting binary packages from
different vendors.

Solution: Rebuild Python or MySQL (or maybe both) from source.

  ImportError: dlopen(./_mysql.so, 2): Symbol not found: _sprintf$LDBLStub 
  Referenced from: ./_mysql.so 
  Expected in: dynamic lookup 

This is one from Mac OS X. It seems to have been a compiler mismatch,
but this time between two different versions of GCC. It seems nearly
every major release of GCC changes the ABI in some why, so linking
code compiled with GCC-3.3 and GCC-4.0, for example, can be
problematic.


My data disappeared! (or won't go away!)
----------------------------------------

Starting with 1.2.0, MySQLdb disables autocommit by default, as
required by the DB-API standard (`PEP-249`_). If you are using InnoDB
tables or some other type of transactional table type, you'll need
to do connection.commit() before closing the connection, or else
none of your changes will be written to the database.

Conversely, you can also use connection.rollback() to throw away
any changes you've made since the last commit.

Important note: Some SQL statements -- specifically DDL statements
like CREATE TABLE -- are non-transactional, so they can't be
rolled back, and they cause pending transactions to commit.


Other Errors
------------

  OperationalError: (1251, 'Client does not support authentication protocol requested by server; consider upgrading MySQL client')  

This means your server and client libraries are not the same version.
More specifically, it probably means you have a 4.1 or newer server
and 4.0 or older client. You can either upgrade the client side, or
try some of the workarounds in `Password Hashing as of MySQL 4.1
<http://dev.mysql.com/doc/refman/5.0/en/password-hashing.html>`_.


Other Resources
---------------

* Help forum. Please search before posting.

* `Google <http://www.google.com/>`_

* READ README!

* Read the User's Guide

* Read `PEP-249`_

.. _`PEP-249`: http://www.python.org/peps/pep-0249.html

