# mysqlclient

[![Build Status](https://secure.travis-ci.org/PyMySQL/mysqlclient-python.png)](http://travis-ci.org/PyMySQL/mysqlclient-python)

This is a fork of [mysqlclient-python](https://github.com/PyMySQL/mysqlclient-python).

This project is designed to be used with TileDB-SQL which is a reduced build of MariaDB with support for using
the [MyTile](https://github.com/TileDB-Inc/TileDB-MariaDB) storage engine for accessing TileDB Arrays.

This is not meant to be used a general purpose MariaDB Client, it is only meant to be used with linking against
the embedded version of MariaDB. This has been tested only with MariaDB 10.4 and the MyTile storage engine.

# Install

## Conda

Conda packages will be available on conda forge soon.

```
conda install -c conda-forge tiledb-sql
```

## Pypi

A pypi package will be build from conda using conda-press

```
pip install tiledb-sql
```

## Compiling From Source

### Prerequisites

You may need to install the Python development headers and compile MariaDB from source

#### Python development headers

* `sudo apt-get install python-dev default-libmysqlclient-dev`  # Debian / Ubuntu
* `sudo yum install python-devel mysql-devel`  # Red Hat / CentOS
* `brew install mysql-connector-c`  # macOS (Homebrew)  (Currently, it has bug. See below)

On Windows, there are binary wheels you can install without MySQLConnector/C or MSVC.

#### Compiling MyTile

Please follow the [MyTile compilation instructions](https://docs.tiledb.com/developer/mariadb/installation)

### Building TileDB-SQL-Py package

If you've installed mytile into `$HOME/mytile_server` simply build the python package with:

```
PATH="$HOME/mytile_server/bin:${PATH}" python setup.py build_ext --inplace
```

Now you can use it with

```
import tiledb.sql
import pandas
db = tiledb.sql.connect(db="test")
pd.read_sql(sql="select * from `s3://my_bucket/my_array`, con=db)
```

# Documentation

Documentation is hosted on [TileDB Developer Docs](https://docs.tiledb.com/developer/api-usage/running-sql)

