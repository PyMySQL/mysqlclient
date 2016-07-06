====================
MySQLdb Installation
====================

.. contents::
..

Prerequisites
-------------

+ Python 2.6, 2.7, 3.3 or higher

  * http://www.python.org/

+ setuptools

  * http://pypi.python.org/pypi/setuptools

+ MySQL 5.0 or higher

  * http://www.mysql.com/downloads/

  * MySQL-4.0 and MySQL-4.1 may work, but not supported.

  * MySQL-5.0 is supported and tested, including stored procedures.

  * MySQL-5.1 is supported (currently a release candidate) but untested.
    It should work.

  * Red Hat Linux packages:

    - mysql-devel to compile

    - mysql and/or mysql-devel to run

  * MySQL.com RPM packages:

    - MySQL-devel to compile

    - MySQL-shared if you want to use their shared
      library. Otherwise you'll get a statically-linked module,
      which may or may not be what you want.

    - MySQL-shared to run if you compiled with MySQL-shared installed

+ C compiler

  * Most free software-based systems already have this, usually gcc.

  * Most commercial UNIX platforms also come with a C compiler, or
    you can also use gcc.

  * If you have some Windows flavor, you should use Windows SDK or
    Visual C++.


Building and installing
-----------------------

The setup.py script uses mysql_config to find all compiler and linker
options, and should work as is on any POSIX-like platform, so long as
mysql_config is in your path.

Depending on which version of MySQL you have, you may have the option
of using three different client libraries. To select the client library,
edit the [options] section of site.cfg:

    embedded
        use embedded server library (libmysqld) if True; otherwise use
	one of the client libraries (default).

    threadsafe
        thread-safe client library (libmysqlclient_r) if True (default);
	otherwise use non-thread-safe (libmysqlclient). You should
	always use the thread-safe library if you have the option;
	otherwise you *may* have problems.

    static
        if True, try to link against a static library; otherwise link
	against dynamic libraries (default). You may need static linking
	to use the embedded server.
        This option doesn't work for MySQL>5.6 since libmysqlclient
        requires libstdc++. If you want to use, add `-lstdc++` to
        mysql_config manually.

If `<mysql prefix>/lib` is not added to `/etc/ld.so.conf`, `import _mysql`
doesn't work. To fix this, (1) set `LD_LIBRARY_PATH`, or (2) add
`-Wl,-rpath,<mysql prefix>/lib` to ldflags in your mysql_config.

Finally, putting it together::

  $ tar xz mysqlclient-1.3.6.tar.gz
  $ cd mysqlclient-1.3.6
  $ # edit site.cfg if necessary
  $ python setup.py build
  $ sudo python setup.py install # or su first


Windows
.......

I don't do Windows. However if someone provides me with a package for
Windows, I'll make it available. Don't ask me for help with Windows
because I can't help you.

Generally, though, running setup.py is similar to above::

  C:\...> python setup.py install
  C:\...> python setup.py bdist_wininst

The latter example should build a Windows installer package, if you
have the correct tools. In any event, you *must* have a C compiler.
Additionally, you have to set an environment variable (mysqlroot)
which is the path to your MySQL installation. In theory, it would be
possible to get this information out of the registry, but like I said,
I don't do Windows, but I'll accept a patch that does this.

On Windows, you will definitely have to edit site.cfg since there is
no mysql_config in the MySQL package.


Binary Packages
---------------

I don't plan to make binary packages any more. However, if someone
contributes one, I will make it available. Several OS vendors have
their own packages available.


RPMs
....

If you prefer to install RPMs, you can use the bdist_rpm command with
setup.py. This only builds the RPM; it does not install it. You may
want to use the --python=XXX option, where XXX is the name of the
Python executable, i.e. python, python2, python2.4; the default is
python. Using this will incorporate the Python executable name into
the package name for the RPM so you have install the package multiple
times if you need to support more than one version of Python. You can
also set this in setup.cfg.


Red Hat Linux
.............

MySQL-python is pre-packaged in Red Hat Linux 7.x and newer. This
includes Fedora Core and Red Hat Enterprise Linux. You can also
build your own RPM packages as described above.


Debian GNU/Linux
................

Packaged as `python-mysqldb`_::

	# apt-get install python-mysqldb

Or use Synaptic.

.. _`python-mysqldb`: http://packages.debian.org/python-mysqldb


Ubuntu
......

Same as with Debian.


Gentoo Linux
............

Packaged as `mysql-python`_. ::

      # emerge sync
      # emerge mysql-python
      # emerge zmysqlda # if you use Zope

.. _`mysql-python`: https://packages.gentoo.org/packages/search?q=mysql-python


BSD
...

MySQL-python is a ported package in FreeBSD, NetBSD, and OpenBSD,
although the name may vary to match OS conventions.


License
-------

GPL or the original license based on Python 1.5.2's license.


:Author: Andy Dustman <andy@dustman.net>
:Revision: $Id$
