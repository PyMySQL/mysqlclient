"""MySQLdb - A DB API v2.0 compatible interface to MySQL.

This package is a wrapper around _mysql, which mostly implements the
MySQL C API.

connect() -- connects to server

See the C API specification and the MySQL documentation for more info
on other items.

For information on how MySQLdb handles type conversion, see the
MySQLdb.converters module.

"""

__author__ = "Andy Dustman <andy@dustman.net>"
__revision__ = """$Revision$"""[11:-2]
version_info = (
    1,
    0,
    1,
    "final",
    1)
if version_info[3] == "final": __version__ = "%d.%d.%d" % version_info[:3]
else: __version__ = "%d.%d.%d%1.1s%d" % version_info[:5]

import _mysql

v = getattr(_mysql, 'version_info', None)
if version_info != v:
    raise ImportError, "this is MySQLdb version %s, but _mysql is version %s" %\
          (version_info, v)
del v

threadsafety = 1
apilevel = "2.0"
paramstyle = "format"

from _mysql import *
from MySQLdb.sets import DBAPISet, Set
from MySQLdb.constants import FIELD_TYPE
from MySQLdb.times import Date, Time, Timestamp, \
    DateFromTicks, TimeFromTicks, TimestampFromTicks


STRING    = DBAPISet(FIELD_TYPE.CHAR, FIELD_TYPE.ENUM, FIELD_TYPE.STRING,
                     FIELD_TYPE.VAR_STRING)
BINARY    = DBAPISet(FIELD_TYPE.BLOB, FIELD_TYPE.LONG_BLOB,
                     FIELD_TYPE.MEDIUM_BLOB, FIELD_TYPE.TINY_BLOB)
NUMBER    = DBAPISet(FIELD_TYPE.DECIMAL, FIELD_TYPE.DOUBLE, FIELD_TYPE.FLOAT,
                     FIELD_TYPE.INT24, FIELD_TYPE.LONG, FIELD_TYPE.LONGLONG,
                     FIELD_TYPE.TINY, FIELD_TYPE.YEAR)
DATE      = DBAPISet(FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE)
TIME      = DBAPISet(FIELD_TYPE.TIME)
TIMESTAMP = DBAPISet(FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME)
DATETIME  = TIMESTAMP
ROWID     = DBAPISet()

def Binary(x): return str(x)

def Connect(*args, **kwargs):
    """Factory function for connections.Connection."""
    from connections import Connection
    return apply(Connection, args, kwargs)

connect = Connection = Connect

__all__ = [ 'BINARY', 'Binary', 'Connect', 'Connection', 'DATE',
    'Date', 'Time', 'Timestamp', 'DateFromTicks', 'TimeFromTicks',
    'TimestampFromTicks', 'DataError', 'DatabaseError', 'Error',
    'FIELD_TYPE', 'IntegrityError', 'InterfaceError', 'InternalError',
    'MySQLError', 'NULL', 'NUMBER', 'NotSupportedError', 'DBAPISet',
    'OperationalError', 'ProgrammingError', 'ROWID', 'STRING', 'TIME',
    'TIMESTAMP', 'Set', 'Warning', 'apilevel', 'connect', 'connections',
    'constants', 'cursors', 'debug', 'escape', 'escape_dict',
    'escape_sequence', 'escape_string', 'get_client_info',
    'paramstyle', 'string_literal', 'threadsafety', 'version_info']




