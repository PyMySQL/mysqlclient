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
    0,
    9,
    0,
    "beta",
    1)
if version_info[3] == "final": __version__ = "%d.%d.%d" % version_info[:3]
else: __version__ = "%d.%d.%d%1.1s%d" % version_info[:5]

import _mysql

if __version__ != getattr(_mysql, '__version__', None):
    raise ImportError, "this is MySQLdb version %s, but _mysql is version %s" %\
          (__version__, _mysql.__version__)


threadsafety = 2
apilevel = "2.0"
paramstyle = "format"


class DBAPITypeObject:

    """Helper class for determining column types; required by DB API."""
    
    def __init__(self,*values):
        self.values = values
        
    def __cmp__(self,other):
        if other in self.values:
            return 0
        if other < self.values:
            return 1
        else:
            return -1


_Set = DBAPITypeObject
from constants import FIELD_TYPE

STRING    = _Set(FIELD_TYPE.CHAR, FIELD_TYPE.ENUM, FIELD_TYPE.INTERVAL,
                 FIELD_TYPE.SET, FIELD_TYPE.STRING, FIELD_TYPE.VAR_STRING)
BINARY    = _Set(FIELD_TYPE.BLOB, FIELD_TYPE.LONG_BLOB, FIELD_TYPE.MEDIUM_BLOB,
                 FIELD_TYPE.TINY_BLOB)
NUMBER    = _Set(FIELD_TYPE.DECIMAL, FIELD_TYPE.DOUBLE, FIELD_TYPE.FLOAT,
	         FIELD_TYPE.INT24, FIELD_TYPE.LONG, FIELD_TYPE.LONGLONG,
	         FIELD_TYPE.TINY, FIELD_TYPE.YEAR)
DATE      = _Set(FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE)
TIME      = _Set(FIELD_TYPE.TIME)
TIMESTAMP = _Set(FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME)
ROWID     = _Set()

def Binary(x): return str(x)

from _mysql import *
from connections import Connection

def Connect(*args, **kwargs):
    """Factory function for connections.Connection."""
    return apply(Connection, args, kwargs)

connect = Connect

__all__ = ['BINARY', 'Binary', 'Connect', 'Connection', 'DATE', 'DataError', 'DatabaseError', 'Error', 'FIELD_TYPE', 'IntegrityError', 'InterfaceError', 'InternalError', 'MySQLError', 'NULL', 'NUMBER', 'NotSupportedError', 'OperationalError', 'ProgrammingError', 'ROWID', 'STRING', 'TIME', 'TIMESTAMP', 'Warning', 'apilevel', 'connect', 'connections', 'constants', 'cursors', 'debug', 'escape', 'escape_dict', 'escape_sequence', 'escape_string', 'get_client_info', 'paramstyle', 'string_literal', 'threadsafety', 'version_info']

