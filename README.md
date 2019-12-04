# mysqlclient

[![Build Status](https://secure.travis-ci.org/PyMySQL/mysqlclient-python.png)](http://travis-ci.org/PyMySQL/mysqlclient-python)

This is a fork of [MySQLdb1](https://github.com/farcepest/MySQLdb1).

This project adds Python 3 support and bug fixes.
I hope this fork is merged back to MySQLdb1 like distribute was merged back to setuptools.


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

### macOS (Homebrew)

Install MySQL and mysqlclient:

```
# Assume you are activating Python 3 venv
$ brew install mysql
$ pip install mysqlclient
```

If you don't want to install MySQL server, you can use mysql-client instead:

```
# Assume you are activating Python 3 venv
$ brew install mysql-client
$ echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.bash_profile
$ export PATH="/usr/local/opt/mysql-client/bin:$PATH"
$ pip install mysqlclient
```

### Linux

**Note that this is a basic step.  I can not support complete step for build for all
environment.  If you can see some error, you should fix it by yourself, or ask for
support in some user forum.  Don't file a issue on the issue tracker.**

You may need to install the Python 3 and MySQL development headers and libraries like so:

* `$ sudo apt-get install python3-dev default-libmysqlclient-dev build-essential`  # Debian / Ubuntu
* `% sudo yum install python3-devel mysql-devel`  # Red Hat / CentOS

Then you can install mysqlclient via pip now:

```
$ pip install mysqlclient
```

### Documentation

Documentation is hosted on [Read The Docs](https://mysqlclient.readthedocs.io/)

