======================
 What's new in 1.3.13
======================

Support build with MySQL 8

Fix decoding tiny/medium/long blobs (#215)

Remove broken row_seek() and row_tell() APIs (#220)

Reduce callproc roundtrip time (#223)


======================
 What's new in 1.3.12
======================

Fix tuple argument again (#201)

InterfaceError is raised when Connection.query() is called for closed connection (#202)

======================
 What's new in 1.3.11
======================

Support MariaDB 10.2 client library (#197, #177, #200)

Add NEWDECIMAL to the NUMBER DBAPISet (#167)

Allow bulk insert which no space around `VALUES` (#179)

Fix leak of `connection->converter`. (#182)

Support error `numbers > CR_MAX_ERROR` (#188)

Fix tuple argument support (#145)


======================
 What's new in 1.3.10
======================

Added `binary_prefix` option (disabled by default) to support
`_binary` prefix again. (#134)

Fix SEGV of `_mysql.result()` when argument's type is unexpected. (#138)

Deprecate context interface of Connection object. (#149)

Don't use workaround of `bytes.decode('ascii', 'surrogateescape')` on Python 3.6+. (#150)


=====================
 What's new in 1.3.9
=====================

Revert adding `_binary` prefix for bytes/bytearray parameter. It broke backward compatibility.

Fix Windows compile error on MSVC.


=====================
 What's new in 1.3.8
=====================

Update error constants (#113)

Use `_binary` prefix for bytes/bytearray parameters (#106)

Use mysql_real_escape_string_quote() if exists (#109)

Better Warning propagation (#101)

Fix conversion error when mysql_affected_rows returns -1

Fix Cursor.callproc may raise TypeError (#90, #91)

connect() supports the 'database' and 'password' keyword arguments.

Fix accessing dangling pointer when using ssl (#78)

Accept %% in Cursor.executemany (#83)

Fix warning that caused TypeError on Python 3 (#68)

=====================
 What's new in 1.3.7
=====================

Support link args other than '-L' and '-l' from mysql_config.

Missing value for column without default value cause IntegrityError.  (#33)

Support BIT type. (#38)

More tests for date and time columns. (#41)

Fix calling .execute() method for closed cursor cause TypeError. (#37)

Improve peformance to parse date. (#43)

Support geometry types (#49)

Fix warning while multi statement cause ProgrammingError. (#48)


=====================
 What's new in 1.3.6
=====================

Fix escape_string() doesn't work.

Remove `Cursor.__del__` to fix uncollectable circular reference on Python 3.3.

Add context manager support to `Cursor`. It automatically closes cursor on `__exit__`.

.. code-block::

    with conn.cursor() as cur:
        cur.execute("SELECT 1+1")
        print(cur.fetchone())
    # cur is now closed


=====================
 What's new in 1.3.5
=====================

Fix TINYBLOB, MEDIUMBLOB and LONGBLOB are treated as string and decoded
to unicode or cause UnicodeError.

Fix aware datetime is formatted with timezone offset (e.g. "+0900").


=====================
 What's new in 1.3.4
=====================

* Remove compiler warnings.
* Fix compile error when using libmariadbclient.
* Fix GIL deadlock while dealloc.

=====================
 What's new in 1.3.3
=====================

* Fix exception reraising doesn't work.

=====================
 What's new in 1.3.2
=====================

* Add send_query() and read_query_result() method to low level connection.
* Add waiter option.


=====================
 What's new in 1.3.1
=====================

This is a first fork of MySQL-python.
Now named "mysqlclient"

* Support Python 3
* Add autocommit option
* Support microsecond in datetime field.


=====================
 What's new in 1.2.4
=====================

final
=====

No changes.


rc 1
====

Fixed a dangling reference to the old types module.


beta 5
======

Another internal fix for handling remapped character sets.

`_mysql.c` was broken for the case where read_timeout was *not* available. (Issue #6)

Documentation was converted to sphinx but there is a lot of cleanup left to do.


beta 4
======

Added support for the MySQL read_timeout option. Contributed by
Jean Schurger (jean@schurger.org).

Added a workaround so that the MySQL character set utf8mb4 works with Python; utf8 is substituted
on the Python side.


beta 3
======

Unified test database configuration, and set up CI testing with Travis.

Applied several patches from André Malo (ndparker@users.sf.net) which fix some issues
with exception handling and reference counting and TEXT/BLOB conversion.


beta 2
======

Reverted an accidental change in the exception format. (issue #1)

Reverted some raise statements so that they will continue to work with Python < 2.6


beta 1
======

A lot of work has been done towards Python 3 compatibility, and avoiding warnings with Python 2.7.
This includes import changes, converting dict.has_kay(k) to k in dict, updating some test suite methods, etc.

Due to the difficulties of supporting Python 3 and Python < 2.7, 1.2.4 will support Python 2.4 though 2.7.
1.3.0 will support Python 3 and Python 2.7 and 2.6.

MySQLdb-2.0 is instead going to become moist-1.0. See https://github.com/farcepest/moist

The Windows build has been simplified, and I plan to correct pre-built i386 packages built
against the python.org Python-2.7 package and MySQL Connector/C-6.0. Contact me if you
need ia64 packages.

The connection's cursorclass (if not default) was being lost on reconnect.

Newer versions of MySQL don't use OpenSSL and therefore don't have HAVE_SSL defined, but they do have
a different SSL library. Fixed this so SSL support would be enabled in this case.

The regex that looked for SQL INSERT statement and VALUES in cursor.executemany() was made case-insensitive
again.


=====================
 What's new in 1.2.3
=====================

ez_setup.py has been update to include various fixes that affect the build.

Better Python version and dependency detection as well as eliminate exception
warnings under Python 2.6.

Eliminated memory leaks related to Unicode and failed connections.

Corrected connection .escape() functionality.

Miscellaneous cleanups and and expanded testing suite to ensure ongoing release
quality.

=====================
 What's new in 1.2.2
=====================

The build system has been completely redone and should now build
on Windows without any patching; uses setuptools.

Added compatibility for Python 2.5, including support for with statement.

connection.ping() now takes an optional boolean argument which can
enable (or disable) automatic reconnection.

Support returning SET columns as Python sets was removed due to an
API bug in MySQL; corresponding test removed.

Added a test for single-character CHAR columns.

BLOB columns are now returned as Python strings instead of byte arrays.

BINARY character columns are always returned as Python strings, and not
unicode.

Fixed a bug introduced in 1.2.1 where the new SHOW WARNINGS support broke
SSCursor.

Only encode the query (convert to a string) when it is a unicode instance;
re-encoding encoded strings would break things.

Make a deep copy of conv when connecting, since it can be modified.

Added support for new VARCHAR and BIT column types.

DBAPISet objects were broken, but nobody noticed.


========================
 What's new in 1.2.1_p2
========================

There are some minor build fixes which probably only affect MySQL
older than 4.0.

If you had MySQL older than 4.1, the new charset and sql_mode
parameters didn't work right. In fact, it was impossible to create
a connection due to the charset problem.

If you are using MySQL-4.1 or newer, there is no practical difference
between 1.2.1 and 1.2.1_p2, and you don't need to upgrade.


=====================
 What's new in 1.2.1
=====================

Switched to Subversion. Was going to do this for 1.3, but a
SourceForge CVS outage has forced the issue.

Mapped a lot of new 4.1 and 5.0 error codes to Python exceptions

Added an API call for mysql_set_character_set(charset) (MySQL > 5.0.7)

Added an API call for mysql_get_character_set_info() (MySQL > 5.0.10)

Revamped the build system. Edit site.cfg if necessary (probably not
in most cases)

Python-2.3 is now the minimum version.

Dropped support for mx.Datetime and stringtimes; always uses Python
datetime module now.

Improved unit tests

New connect() options:
* charset: sets character set, implies use_unicode
* sql_mode: sets SQL mode (i.e. ANSI, etc.; see MySQL docs)

When using MySQL-4.1 or newer, enables MULTI_STATEMENTS

When using MySQL-5.0 or newer, enables MULTI_RESULTS

When using MySQL-4.1 or newer, more detailed warning messages
are produced

SET columns returned as Python Set types; you can pass a Set as
a parameter to cursor.execute().

Support for the new MySQL-5.0 DECIMAL implementation

Support for Python Decimal type

Some use of weak references internally. Cursors no longer leak
if you don't close them. Connections still do, unfortunately.

ursor.fetchXXXDict() methods raise DeprecationWarning

cursor.begin() is making a brief reappearence.

cursor.callproc() now works, with some limitations.

