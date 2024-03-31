# mysqlclient

This project is a fork of [MySQLdb1](https://github.com/farcepest/MySQLdb1).
This project adds Python 3 support and fixed many bugs.

* PyPI: https://pypi.org/project/mysqlclient/
* GitHub: https://github.com/PyMySQL/mysqlclient


## Support

**Do Not use Github Issue Tracker to ask help.  OSS Maintainer is not free tech support**

When your question looks relating to Python rather than MySQL:

* Python mailing list [python-list](https://mail.python.org/mailman/listinfo/python-list)
* Slack [pythondev.slack.com](https://pyslackers.com/web/slack)

Or when you have question about MySQL:

* [MySQL Community on Slack](https://lefred.be/mysql-community-on-slack/)


## Install

### Windows

Building mysqlclient on Windows is very hard.
But there are some binary wheels you can install easily.

If binary wheels do not exist for your version of Python, it may be possible to
build from source, but if this does not work, **do not come asking for support.**
To build from source, download the
[MariaDB C Connector](https://mariadb.com/downloads/#connectors) and install
it. It must be installed in the default location
(usually "C:\Program Files\MariaDB\MariaDB Connector C" or
"C:\Program Files (x86)\MariaDB\MariaDB Connector C" for 32-bit). If you
build the connector yourself or install it in a different location, set the
environment variable `MYSQLCLIENT_CONNECTOR` before installing. Once you have
the connector installed and an appropriate version of Visual Studio for your
version of Python:

```
$ pip install mysqlclient
```

### macOS (Homebrew)

Install MySQL and mysqlclient:

```bash
$ # Assume you are activating Python 3 venv
$ brew install mysql pkg-config
$ pip install mysqlclient
```

If you don't want to install MySQL server, you can use mysql-client instead:

```bash
$ # Assume you are activating Python 3 venv
$ brew install mysql-client pkg-config
$ export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"
$ pip install mysqlclient
```

### Linux

**Note that this is a basic step.  I can not support complete step for build for all
environment.  If you can see some error, you should fix it by yourself, or ask for
support in some user forum.  Don't file a issue on the issue tracker.**

You may need to install the Python 3 and MySQL development headers and libraries like so:

* `$ sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config`  # Debian / Ubuntu
* `% sudo yum install python3-devel mysql-devel pkgconfig`  # Red Hat / CentOS

Then you can install mysqlclient via pip now:

```
$ pip install mysqlclient
```

### Customize build (POSIX)

mysqlclient uses `pkg-config --cflags --ldflags mysqlclient` by default for finding
compiler/linker flags.

You can use `MYSQLCLIENT_CFLAGS` and `MYSQLCLIENT_LDFLAGS` environment
variables to customize compiler/linker options.

```bash
$ export MYSQLCLIENT_CFLAGS=`pkg-config mysqlclient --cflags`
$ export MYSQLCLIENT_LDFLAGS=`pkg-config mysqlclient --libs`
$ pip install mysqlclient
```

### Documentation

Documentation is hosted on [Read The Docs](https://mysqlclient.readthedocs.io/)
