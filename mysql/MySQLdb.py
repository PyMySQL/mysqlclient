"""MySQLdb - A DB API v2.0 compatible interface to MySQL.

This module is a thin wrapper around _mysql, which mostly implements the
MySQL C API. All symbols from that module are imported.

connect() -- connects to server
type_conv -- dictionary mapping SQL types to Python functions, which
             convert a string into an appropriate data type. Reasonable
             defaults are set for most items, and you can add your own.

See the API specification and the MySQL documentation for more info
on other items.

This module uses the mxDateTime package for handling date/time types.
"""

__version__ = """$Revision$"""[11:-2]

from _mysql import *
from time import localtime
import re

threadsafety = 1
apilevel = "2.0"
paramstyle = "format"

try:
    from DateTime import Date, Time, Timestamp, ISO

    def DateFromTicks(ticks):
	return apply(Date, localtime(ticks)[:3])

    def TimeFromTicks(ticks):
	return apply(Time, localtime(ticks)[3:6])

    def TimestampFromTicks(ticks):
	return apply(Timestamp, localtime(ticks)[:6])

    def format_DATE(d):      return d.Format("%Y-%m-%d")
    def format_TIME(d):      return d.Format("%H:%M:%S")
    def format_TIMESTAMP(d): return d.Format("%Y-%m-%d %H:%M:%S")

    def mysql_timestamp_converter(s):
	parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
				       s[8:10],s[10:12],s[12:14])))
	return apply(Timestamp, tuple(parts))

    type_conv[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
    type_conv[FIELD_TYPE.DATETIME] = ISO.ParseDateTime
    type_conv[FIELD_TYPE.TIME] = ISO.ParseTime
    type_conv[FIELD_TYPE.DATE] = ISO.ParseDate

except ImportError:
    # no DateTime? We'll muddle through somehow.
    from time import strftime

    def DateFromTicks(ticks):
	return strftime("%Y-%m-%d", localtime(ticks))

    def TimeFromTicks(ticks):
	return strftime("%H:%M:%S", localtime(ticks))

    def TimestampFromTicks(ticks):
	return strftime("%Y-%m-%d %H:%M:%S", localtime(ticks))

    def format_DATE(d): return d
    format_TIME = format_TIMESTAMP = format_DATE


class DBAPITypeObject:
    
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

insert_values = re.compile(r'values\s(\(.+\))', re.IGNORECASE)

def escape_dict(d):
    d2 = {}
    for k,v in d.items(): d2[k] = "'%s'" % escape_string(str(v))
    return d2


class _Cursor:
    
    """Created by a Connection object. Useful attributes:
    
    description -- DB API 7-tuple describing columns in last query
    arraysize -- default number of rows fetchmany() will fetch
    warnings -- should MySQL warnings raise a Warning exception?
    use -- should mysql_use_result be used instead of mysql_store_result?
    
    By default, warnings are issued, and mysql_store_result is used.
    See the MySQL docs for more information."""

    def __init__(self, connection, name='', use=0, warnings=1):
        self.connection = connection
        self.name = name
        self.description = None
        self.rowcount = -1
        self.result = None
        self.arraysize = None
        self.warnings = warnings
	self.use = use
        
    def setinputsizes(self, *args): pass
      
    def setoutputsizes(self, *args): pass
         
    def execute(self, query, args=None):
        """cursor.execute(query, args=None)
        
        query -- string, query to execute on server
        args -- sequence or mapping, parameters to use with query."""
        from types import ListType, TupleType
        from string import rfind, join, split, atoi
        if not args:
            self._query(query)
        elif type(args) is ListType and type(args[0]) is TupleType:
 	    self.executemany(query, args) # deprecated
 	else:
            try:
                self._query(query % escape_row(args))
            except TypeError:
                self._query(query % escape_dict(args))

    def executemany(self, query, args):
        """cursor.executemany(self, query, args)
        
        query -- string, query to execute on server
        args -- sequence of sequences or mappings, parameters to use with
            query. The query must contain the clause "values ( ... )".
            The parenthetical portion will be repeated once for each
            item in the sequence.
        
        This method performs multiple-row inserts and similar queries."""
        from string import join
        m = insert_values.search(query)
        if not m: raise ProgrammingError, "can't find values"
        p = m.start(1)
        escape = escape_row
        try:
	    q = [query % escape(args[0])]
	except TypeError:
	    escape = escape_dict
	    q = [query % escape(args[0])]
        qv = query[p:]
        for a in args[1:]: q.append(qv % escape(a))
        self._query(join(q, ',\n'))

    def _query(self, q):
        from string import split, atoi
        db = self.connection.db
        db.query(q)
        if self.use: self.result = db.use_result()
        else:        self.result = db.store_result()
	if self.result:
     	    self.description = self.result.describe()
     	    self.rowcount = self.result.num_rows()
     	else:
     	    self.description = None
     	    self.rowcount = -1
     	if self.warnings:
     	    w = db.info()
     	    if w:
     	        warnings = atoi(split(w)[-1])
     	        if warnings:
     	            raise Warning, w

    def fetchone(self):
        """Fetches a single row from the cursor."""
        try:
            return self.result.fetch_row()
        except AttributeError:
            raise ProgrammingError, "no query executed yet"
             
    def fetchmany(self, size=None):
        """cursor.fetchmany(size=cursor.inputsizes)
        
        size -- integer, maximum number of rows to fetch."""
        return self.result.fetch_rows(size or self.inputsizes or 1)
         
    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        return self.result.fetch_all_rows()
         
    def nextset(self): return None
     
     
class Connection:

    """Connection(host=NULL, user=NULL, passwd=NULL, db=NULL,
                  port=<MYSQL_PORT>, unix_socket=NULL, client_flag=0)
    
    Note: This interface uses keyword arguments exclusively.
    
    host -- string, host to connect to or NULL pointer (localhost)
    user -- string, user to connect as or NULL (your username)
    passwd -- string, password to use or NULL (no password)
    db -- string, database to use or NULL (no DB selected)
    port -- integer, TCP/IP port to connect to or default MySQL port
    unix_socket -- string, location of unix_socket to use or use TCP
    client_flags -- integer, flags to use or 0 (see MySQL docs)
    
    Returns a Connection object.
    
    Useful attributes and methods:
    
    db -- connection object from _mysql. Good for accessing some of the
        MySQL-specific calls.
    close -- close the connection.
    cursor -- create a cursor (emulated) for executing queries.
    CursorClass -- class used to create cursors (_Cursor). If you subclass
        the Connection object, you will probably want to override this.
    """
    
    CursorClass = _Cursor
    
    def __init__(self, **kwargs):
        from _mysql import connect
        self.db = apply(connect, (), kwargs)
     
    def close(self):
        """Close the connection. No further activity possible."""
        self.db.close()
         
    def commit(self): """Does nothing as there are no transactions."""
    
    def cursor(self, *args, **kwargs):
        """Create a cursor on which queries may be performed."""
        return apply(self.CursorClass, (self,)+args, kwargs)


Connect = connect = Connection
