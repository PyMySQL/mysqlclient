# mysqlclient

[![Build Status](https://secure.travis-ci.org/PyMySQL/mysqlclient-python.png)](http://travis-ci.org/PyMySQL/mysqlclient-python)

This is a fork of [MySQLdb1](https://github.com/farcepest/MySQLdb1).

This project adds Python 3 support and bug fixes.
I hope this fork is merged back to MySQLdb1 like distribute was merged back to setuptools.

## Install

### Prerequisites

You may need to install the Python and MySQL development headers and libraries like so:

* `sudo apt-get install python-dev default-libmysqlclient-dev`  # Debian / Ubuntu
* `sudo yum install python-devel mysql-devel`  # Red Hat / CentOS
* `brew install mysql-connector-c`  # macOS (Homebrew)  (Currently, it has bug. See below)

On Windows, there are binary wheels you can install without MySQLConnector/C or MSVC.

#### Note on Python 3 : if you are using python3 then you need to install python3-dev using the following command :

`sudo apt-get install python3-dev` # debian / Ubuntu

`sudo yum install python3-devel `  # Red Hat / CentOS

#### **Note about bug of MySQL Connector/C on macOS**

See also: https://bugs.mysql.com/bug.php?id=86971

Versions of MySQL Connector/C may have incorrect default configuration options that cause compilation errors when `mysqlclient-python` is installed.  (As of November 2017, this is known to be true for homebrew's `mysql-connector-c` and [official package](https://dev.mysql.com/downloads/connector/c/))

Modification of `mysql_config` resolves these issues as follows.

Change

```
# on macOS, on or about line 112:
# Create options
libs="-L$pkglibdir"
libs="$libs -l "
```

to

```
# Create options
libs="-L$pkglibdir"
libs="$libs -lmysqlclient -lssl -lcrypto"
```

An improper ssl configuration may also create issues; see, e.g, `brew info openssl` for details on macOS.

### Install from PyPI

`pip install mysqlclient`

NOTE: Wheels for Windows may be not released with source package. You should pin version
in your `requirements.txt` to avoid trying to install newest source package.


### Install from source

1. Download source by `git clone` or [zipfile](https://github.com/PyMySQL/mysqlclient-python/archive/master.zip).
2. Customize `site.cfg`
3. `python setup.py install`

### Documentation

Documentation is hosted on [Read The Docs](https://mysqlclient.readthedocs.io/)

