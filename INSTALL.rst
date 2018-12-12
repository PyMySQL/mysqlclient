====================
MySQLdb Installation
====================

.. contents::
..

Prerequisites
-------------

+ Python 2.7, 3.5 or higher

+ setuptools

  * https://pypi.org/project/setuptools/

+ MySQL 5.5 or higher

  * https://www.mysql.com/downloads/

  * MySQL 5.1 may work, but not supported.

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

    static
        if True, try to link against a static library; otherwise link
        against dynamic libraries (default).
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


Red Hat Linux
.............

MySQL-python is pre-packaged in Red Hat Linux 7.x and newer. This
includes Fedora Core and Red Hat Enterprise Linux.


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
