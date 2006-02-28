"""MySQLdb - A DB API v2.0 compatible interface to MySQL.

This package is a wrapper around _mysql, which mostly implements the
MySQL C API.

connect() -- connects to server

See the C API specification and the MySQL documentation for more info
on other items.

For information on how MySQLdb handles type conversion, see the
MySQLdb.converters module.

"""

__revision__ = """$Revision$"""[11:-2]
from release import __version__, version_info, __author__

import _mysql

if version_info != _mysql.version_info:
    raise ImportError, "this is MySQLdb version %s, but _mysql is version %r" %\
          (version_info, _mysql.version_info)

threadsafety = 1
apilevel = "2.0"
paramstyle = "format"

from _mysql import *
from MySQLdb.constants import FIELD_TYPE
from MySQLdb.times import Date, Time, Timestamp, \
    DateFromTicks, TimeFromTicks, TimestampFromTicks

from sets import ImmutableSet
class DBAPISet(ImmutableSet):

    """A special type of set for which A == x is true if A is a
    DBAPISet and x is a member of that set."""

    def __ne__(self, other):
        from sets import BaseSet
        if isinstance(other, BaseSet):
            return super(self).__ne__(self, other)
        else:
            return other not in self

    def __eq__(self, other):
        from sets import BaseSet
        if isinstance(other, BaseSet):
            return super(self).__eq__(self, other)
        else:
            return other in self


STRING    = DBAPISet([FIELD_TYPE.ENUM, FIELD_TYPE.STRING,
                     FIELD_TYPE.VAR_STRING])
BINARY    = DBAPISet([FIELD_TYPE.BLOB, FIELD_TYPE.LONG_BLOB,
                     FIELD_TYPE.MEDIUM_BLOB, FIELD_TYPE.TINY_BLOB])
NUMBER    = DBAPISet([FIELD_TYPE.DECIMAL, FIELD_TYPE.DOUBLE, FIELD_TYPE.FLOAT,
                     FIELD_TYPE.INT24, FIELD_TYPE.LONG, FIELD_TYPE.LONGLONG,
                     FIELD_TYPE.TINY, FIELD_TYPE.YEAR])
DATE      = DBAPISet([FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE])
TIME      = DBAPISet([FIELD_TYPE.TIME])
TIMESTAMP = DBAPISet([FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME])
DATETIME  = TIMESTAMP
ROWID     = DBAPISet()

def Binary(x):
    from array import array
    return array('c', x)

def Connect(*args, **kwargs):
    """Factory function for connections.Connection."""
    from connections import Connection
    return Connection(*args, **kwargs)

connect = Connection = Connect

__all__ = [ 'BINARY', 'Binary', 'Connect', 'Connection', 'DATE',
    'Date', 'Time', 'Timestamp', 'DateFromTicks', 'TimeFromTicks',
    'TimestampFromTicks', 'DataError', 'DatabaseError', 'Error',
    'FIELD_TYPE', 'IntegrityError', 'InterfaceError', 'InternalError',
    'MySQLError', 'NULL', 'NUMBER', 'NotSupportedError', 'DBAPISet',
    'OperationalError', 'ProgrammingError', 'ROWID', 'STRING', 'TIME',
    'TIMESTAMP', 'Warning', 'apilevel', 'connect', 'connections',
    'constants', 'cursors', 'debug', 'escape', 'escape_dict',
    'escape_sequence', 'escape_string', 'get_client_info',
    'paramstyle', 'string_literal', 'threadsafety', 'version_info']




