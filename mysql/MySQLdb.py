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

import _mysql
from _mysql import *
from time import localtime
import re, types

threadsafety = 2
apilevel = "2.0"
paramstyle = "format"

try:
    import threading
    _threading = threading
    del threading
except ImportError:
    _threading = None

def Thing2Str(s, d={}): return str(s)
def Long2Int(l, d={}): s = str(l); return s[-1] == 'L' and s[:-1] or s
def None2NULL(o, d={}): return "NULL"
def Thing2Literal(o, d={}): return string_literal(str(o))

# MySQL-3.23.xx now has a new escape_string function that uses
# the connection to determine what character set is in use and
# quote accordingly. So this will be overridden by the connect()
# method.

quote_conv = { types.IntType: Thing2Str,
	       types.LongType: Long2Int,
	       types.FloatType: Thing2Str,
	       types.NoneType: None2NULL,
               types.TupleType: escape_sequence,
               types.ListType: escape_sequence,
               types.DictType: escape_dict,
	       types.StringType: Thing2Literal } # default

type_conv = { FIELD_TYPE.TINY: int,
              FIELD_TYPE.SHORT: int,
              FIELD_TYPE.LONG: long,
              FIELD_TYPE.FLOAT: float,
              FIELD_TYPE.DOUBLE: float,
              FIELD_TYPE.LONGLONG: long,
              FIELD_TYPE.INT24: int,
              FIELD_TYPE.YEAR: int }

try:
    try:
        from mx import DateTime # new packaging
        from mx.DateTime import Date, Time, Timestamp, ISO, \
            DateTimeType, DateTimeDeltaType
    except ImportError:
        import DateTime # old packaging
        from DateTime import Date, Time, Timestamp, ISO, \
            DateTimeType, DateTimeDeltaType

    def DateFromTicks(ticks):
	return apply(Date, localtime(ticks)[:3])

    def TimeFromTicks(ticks):
	return apply(Time, localtime(ticks)[3:6])

    def TimestampFromTicks(ticks):
	return apply(Timestamp, localtime(ticks)[:6])

    def format_DATE(d):      return d.strftime("%Y-%m-%d")
    def format_TIME(d):      return d.strftime("%H:%M:%S")
    def format_TIMESTAMP(d): return d.strftime("%Y-%m-%d %H:%M:%S")

    def mysql_timestamp_converter(s):
	parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
				       s[8:10],s[10:12],s[12:14])))
	return apply(Timestamp, tuple(parts))

    type_conv[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
    type_conv[FIELD_TYPE.DATETIME] = ISO.ParseDateTime
    type_conv[FIELD_TYPE.TIME] = ISO.ParseTimeDelta
    type_conv[FIELD_TYPE.DATE] = ISO.ParseDate

    def DateTime2literal(d, c={}): return "'%s'" % format_TIMESTAMP(d)
    def DateTimeDelta2literal(d, c={}): return "'%s'" % format_TIME(d)

    quote_conv[DateTimeType] = DateTime2literal
    quote_conv[DateTimeDeltaType] = DateTimeDelta2literal

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

class BaseCursor:
    
    """A base for Cursor classes. Useful attributes:
    
    description -- DB API 7-tuple describing columns in last query
    arraysize -- default number of rows fetchmany() will fetch
    
    See the MySQL docs for more information."""

    def __init__(self, connection):
        self.connection = connection
        self.description = None
        self.rowcount = -1
        self.arraysize = 100

    def close(self):
        self.connection = None

    def _check_open(self):
        if not self.connection:
            raise ProgrammingError, "cursor closed"
        
    def setinputsizes(self, *args): pass
      
    def setoutputsizes(self, *args): pass
         
    def execute(self, query, args=None):
        """rows=cursor.execute(query, args=None)
        
        query -- string, query to execute on server
        args -- sequence or mapping, parameters to use with query.
        rows -- rows affected, if any"""
        self._check_open()
        from types import ListType, TupleType
        from string import rfind, join, split, atoi
        qc = self.connection.quote_conv
        if not args:
            return self._query(query)
        elif type(args) is ListType and type(args[0]) is TupleType:
 	    return self.executemany(query, args) # deprecated
 	else:
            try:
                return self._query(query % escape(args, qc))
	    except TypeError, m:
                if m.args[0] in ("not enough arguments for format string",
                                 "not all arguments converted"):
                    raise ProgrammingError, m.args[0]
                else:
                    raise

    def executemany(self, query, args):
        """cursor.executemany(self, query, args)
        
        query -- string, query to execute on server
        args -- sequence of sequences or mappings, parameters to use with
            query. The query must contain the clause "values ( ... )".
            The parenthetical portion will be repeated once for each
            item in the sequence.
        
        This method performs multiple-row inserts and similar queries."""
        self._check_open()
        from string import join
        m = insert_values.search(query)
        if not m: raise ProgrammingError, "can't find values"
        p = m.start(1)
        qc = self.connection.quote_conv
        try:
	    q = [query % escape(args[0], qc)]
	except TypeError, msg:
            if msg.args[0] in ("not enough arguments for format string",
                             "not all arguments converted"):
                raise ProgrammingError, msg.args[0]
            else:
                raise
        qv = query[p:]
        for a in args[1:]: q.append(qv % escape(a, qc))
        return self._query(join(q, ',\n'))

    def __do_query(self, q):
        from string import split, atoi
        db = self.connection.db
        db.query(q)
        self._result = self._get_result()
     	self.rowcount = db.affected_rows()
        self.description = self._result and self._result.describe() or None
        self._insert_id = db.insert_id()
        self._info = db.info()
        self._check_for_warnings()
        return self.rowcount

    def _check_for_warnings(self): pass

    _query = __do_query

    def info(self):
        try: return self._info
        except AttributeError: raise ProgrammingError, "execute() first"
    
    def insert_id(self):
        try: return self._insert_id
        except AttributeError: raise ProgrammingError, "execute() first"
    
    def nextset(self): return None

    def _fetch_row(self):
        r = self._result.fetch_row(1, self._fetch_type)
        return r and r[0] or ()

    def _fetch_rows(self, size):
        return self._result.fetch_row(size, self._fetch_type)

    def _fetch_all_rows(self): 
        return self._result.fetch_row(0, self._fetch_type)
         

class CursorWarningMixIn:

    def _check_for_warnings(self):
        from string import atoi, split
        if self._info:
            warnings = atoi(split(self._info)[-1])
    	    if warnings:
     	        raise Warning, self._info


class CursorStoreResultMixIn:

    def _get_result(self): return self.connection.db.store_result()

    def close(self):
        self.connection = None
        self._rows = ()

    def _query(self, q):
        self.connection._acquire()
        try:
            rowcount = self._BaseCursor__do_query(q)
            self._rows = self._result and self._fetch_all_rows() or ()
            self._pos = 0
            del self._result
            return rowcount
        finally:
            self.connection._release()
            
    def fetchone(self):
        """Fetches a single row from the cursor."""
        if self._pos >= len(self._rows): return None
        result = self._rows[self._pos]
        self._pos = self._pos+1
        return result

    def fetchmany(self, size=None):
        """cursor.fetchmany(size=cursor.arraysize)
        
        size -- integer, maximum number of rows to fetch."""
        end = self._pos + size or self.arraysize
        result = self._rows[self._pos:end]
        self._pos = end
        return result

    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        result = self._pos and self._rows[self._pos:] or self._rows
        self._pos = len(self._rows)
        return result
    
    def seek(self, row, whence=0):
        if whence == 0:
            self._pos = row
        elif whence == 1:
            self._pos = self._pos + row
        elif whence == 2:
            self._pos = len(self._rows) + row
     
    def tell(self): return self._pos


class CursorUseResultMixIn:

    def __init__(self, connection):
        BaseCursor.__init__(self, connection)
        if not self.connection._acquire(0):
            raise ProgrammingError, "would deadlock"

    def close(self):
        if self.connection: self.connection._release()
        self.connection = None
        
    def __del__(self):
        try:
            del self._result
        finally:
            self.close()
        
    def _get_result(self): return self.connection.db.use_result()

    def fetchone(self):
        """Fetches a single row from the cursor."""
        self._check_open()
        try:
            return self._fetch_row()
        except AttributeError:
            raise ProgrammingError, "no query executed yet"
             
    def fetchmany(self, size=None):
        """cursor.fetchmany(size=cursor.arraysize)
        
        size -- integer, maximum number of rows to fetch."""
        self._check_open()
        return self._fetch_rows(size or self.arraysize)
         
    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_open()
        return self._fetch_all_rows()


class CursorTupleRowsMixIn:

    _fetch_type = 0


class CursorDictRowsMixIn:

    _fetch_type = 1

    ## XXX Deprecated
    
    def fetchoneDict(self, *args, **kwargs):
        return apply(self.fetchone, args, kwargs)

    def fetchmanyDict(self, *args, **kwargs):
        return apply(self.fetchmany, args, kwargs)

    def fetchallDict(self, *args, **kwargs):
        return apply(self.fetchall, args, kwargs)


class CursorOldDictRowsMixIn(CursorDictRowsMixIn):

    _fetch_type = 2


class CursorNW(CursorStoreResultMixIn, CursorTupleRowsMixIn,
               BaseCursor): pass

class Cursor(CursorWarningMixIn, CursorNW): pass

class DictCursorNW(CursorStoreResultMixIn, CursorDictRowsMixIn,
                   BaseCursor): pass

class DictCursor(CursorWarningMixIn, DictCursorNW): pass

class SSCursorNW(CursorUseResultMixIn, CursorTupleRowsMixIn,
                 BaseCursor): pass

class SSCursor(CursorWarningMixIn, SSCursorNW): pass

class SSDictCursorNW(CursorUseResultMixIn, CursorDictRowsMixIn,
                     BaseCursor): pass

class SSDictCursor(CursorWarningMixIn, SSDictCursorNW): pass


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
    conv -- dictionary, maps MySQL FIELD_TYPE.* to Python functions which
            convert a string to the appropriate Python type
    
    Returns a Connection object.
    
    Useful attributes and methods:
    
    db -- connection object from _mysql. Good for accessing some of the
        MySQL-specific calls.
    close -- close the connection.
    cursor -- create a cursor (emulated) for executing queries.
    """
    
    def __init__(self, **kwargs):
        from _mysql import connect
        from string import split
        if not kwargs.has_key('conv'): kwargs['conv'] = type_conv.copy()
        self.quote_conv = kwargs.get('quote_conv', quote_conv.copy())
        if kwargs.has_key('cursorclass'):
            self.cursorclass = kwargs['cursorclass']
            del kwargs['cursorclass']
        else:
            self.cursorclass = Cursor
        self.db = apply(connect, (), kwargs)
        self.quote_conv[types.StringType] = self.Thing2Literal
        self._transactional = self.db.server_capabilities & CLIENT.TRANSACTIONS
        if _threading: self.__lock = _threading.Lock()

    if _threading:
        def _acquire(self, blocking=1): return self.__lock.acquire(blocking)
        def _release(self): return self.__lock.release()
    else:
        def _acquire(self, blocking=1): return 1
        def _release(self): return 1
        
    def Thing2Literal(self, o, d={}): return self.db.string_literal(str(o))
    
    def close(self):
        """Close the connection. No further activity possible."""
        self.db.close()
         
    def commit(self):
        """Commit the current transaction."""
        if self._transactional:
            self.db.query("COMMIT")

    def rollback(self):
        """Rollback the current transaction."""
        if self._transactional:
            self.db.query("ROLLBACK")
        else: raise NotSupportedError, "Not supported by server"

    def cursor(self, cursorclass=None):
        """Create a cursor on which queries may be performed."""
        return (cursorclass or self.cursorclass)(self)

    # Non-portable MySQL-specific stuff
    # Methods not included on purpose (use Cursors instead):
    #     query, store_result, use_result

    def affected_rows(self): return self.db.affected_rows()
    def dump_debug_info(self): return self.db.dump_debug_info()
    def escape_string(self, s): return self.db.escape_string(s)
    def get_host_info(self): return self.db.get_host_info()
    def get_proto_info(self): return self.db.get_proto_info()
    def get_server_info(self): return self.db.get_server_info()
    def info(self): return self.db.info()
    def kill(self, p): return self.db.kill(p)
    def list_dbs(self): return self.db.list_dbs().fetch_row(0)
    def list_fields(self, table): return self.db.list_fields(table).fetch_row(0)
    def list_processes(self): return self.db.list_processes().fetch_row(0)
    def list_tables(self, db): return self.db.list_tables(db).fetch_row(0)
    def field_count(self): return self.db.field_count()
    num_fields = field_count # used prior to MySQL-3.22.24
    def ping(self): return self.db.ping()
    def row_tell(self): return self.db.row_tell()
    def select_db(self, db): return self.db.select_db(db)
    def shutdown(self): return self.db.shutdown()
    def stat(self): return self.db.stat()
    def string_literal(self, s): return self.db.string_literal(s)
    def thread_id(self): return self.db.thread_id()

    def _try_feature(self, feature, *args, **kwargs):
        try:
            return apply(getattr(self.db, feature), args, kwargs)
        except AttributeError:
            raise NotSupportedError, "not supported by MySQL library"
    def character_set_name(self):
        return self._try_feature('character_set_name')
    def change_user(self, *args, **kwargs):
        return apply(self._try_feature, ('change_user',)+args, kwargs)


Connect = connect = Connection
