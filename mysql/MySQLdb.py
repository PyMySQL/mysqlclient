"""MySQLdb - A DB API v2.0 compatible interface to MySQL.

This module is a thin wrapper around _mysql, which mostly implements
the MySQL C API. All symbols from that module are imported.

connect() -- connects to server

See the API specification and the MySQL documentation for more info on
other items.

For information on how MySQLdb handles type conversion, see the
_mysql_const.converters module.

"""

__author__ = "Andy Dustman <andy@dustman.net>"
__version__ = "0.3.6"
__revision__ = """$Revision$"""[11:-2]

import _mysql
from _mysql import *
if __version__ != getattr(_mysql, '__version__', None):
    raise ImportError, "this is MySQLdb version %s, but _mysql is version %s" %\
          (__version__, _mysql.__version__)

from _mysql_const import converters
from _mysql_const.converters import *
import re, types
from types import ListType, TupleType
from string import rfind, join, split, atoi

threadsafety = 2
apilevel = "2.0"
paramstyle = "format"

try:
    import threading
    _threading = threading
    del threading
except ImportError:
    _threading = None

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
        self._thequery = ''

    def close(self):
        """Close the cursor. No further queries will be possible."""
        self.connection = None

    def _check_open(self):
        if not self.connection:
            raise ProgrammingError, "cursor closed"
        
    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
      
    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""
         
    def execute(self, query, args=None):
        """Execute a query.
        
        query -- string, query to execute on server
        args -- sequence or mapping, parameters to use with query.
        returns long integer rows affected, if any"""
        self._check_open()
        self._thequery = query
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
        """Execute a multi-row query.
        
        query -- string, query to execute on server
        args -- sequence of sequences or mappings, parameters to use with
            query. The query must contain the clause "values ( ... )".
            The parenthetical portion will be repeated once for each
            item in the sequence.
        returns long integer rows affected, if any
        
        This method performs multiple-row inserts and similar queries."""
        self._check_open()
        self._thequery = query
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
        """Return some information about the last query (db.info())"""
        try: return self._info
        except AttributeError: raise ProgrammingError, "execute() first"
    
    def insert_id(self):
        """Return the last inserted ID on an AUTO_INCREMENT columns."""
        try: return self._insert_id
        except AttributeError: raise ProgrammingError, "execute() first"
    
    def nextset(self):
        """Does nothing. Required by DB API."""
        return None

    def _fetch_row(self):
        r = self._result.fetch_row(1, self._fetch_type)
        return r and r[0] or ()

    def _fetch_rows(self, size):
        return self._result.fetch_row(size, self._fetch_type)

    def _fetch_all_rows(self): 
        return self._result.fetch_row(0, self._fetch_type)
         

class CursorWarningMixIn:

    """This is a MixIn class that provides the capability of raising
    the Warning exception when something went slightly wrong with your
    query."""

    def _check_for_warnings(self):
        from string import atoi, split
        if self._info:
            warnings = atoi(split(self._info)[-1])
    	    if warnings:
     	        raise Warning, self._info


class CursorStoreResultMixIn:

    """This is a MixIn class which causes the entire result set to be
    stored on the client side, i.e. it uses mysql_store_result(). If the
    result set can be very large, consider adding a LIMIT clause to your
    query, or using CursorUseResultMixIn instead."""

    def _get_result(self): return self.connection.db.store_result()

    def close(self):
        """Close the cursor. Further queries will not be possible."""
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
        if not self._thequery: raise ProgrammingError, "execute() first"
        if self._pos >= len(self._rows): return None
        result = self._rows[self._pos]
        self._pos = self._pos+1
        return result

    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        if not self._thequery: raise ProgrammingError, "execute() first"
        end = self._pos + size or self.arraysize
        result = self._rows[self._pos:end]
        self._pos = end
        return result

    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        if not self._thequery: raise ProgrammingError, "execute() first"
        result = self._pos and self._rows[self._pos:] or self._rows
        self._pos = len(self._rows)
        return result
    
    def seek(self, row, whence=0):
        """seek to a given row of the result set analogously to file.seek().
        This is non-standard extension."""
        if whence == 0:
            self._pos = row
        elif whence == 1:
            self._pos = self._pos + row
        elif whence == 2:
            self._pos = len(self._rows) + row
     
    def tell(self):
        """Return the current position in the result set analogously to
        file.tell(). This is a non-standard extension."""
        return self._pos


class CursorUseResultMixIn:

    """This is a MixIn class which causes the result set to be stored in
    the server and sent row-by-row to client side, i.e. it uses
    mysql_use_result(). You MUST retrieve the entire result set and close()
    the cursor before additional queries can be peformed on the connection."""

    def __init__(self, connection):
        BaseCursor.__init__(self, connection)
        if not self.connection._acquire(0):
            raise ProgrammingError, "would deadlock"

    def close(self):
        """Close the cursor. No further queries can be executed."""
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
        if not self._thequery: raise ProgrammingError, "execute() first"
        return self._fetch_row()
             
    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_open()
        if not self._thequery: raise ProgrammingError, "execute() first"
        return self._fetch_rows(size or self.arraysize)
         
    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_open()
        if not self._thequery: raise ProgrammingError, "execute() first"
        return self._fetch_all_rows()


class CursorTupleRowsMixIn:

    """This is a MixIn class that causes all rows to be returned as tuples,
    which is the standard form required by DB API."""

    _fetch_type = 0


class CursorDictRowsMixIn:

    """This is a MixIn class that causes all rows to be returned as
    dictionaries. This is a non-standard feature."""

    _fetch_type = 1

    def fetchoneDict(self, *args, **kwargs):
        """Fetch a single row as a dictionary. Deprecated:
        Use fetchone() instead."""
        return apply(self.fetchone, args, kwargs)

    def fetchmanyDict(self, *args, **kwargs):
        """Fetch several rows as a list of dictionaries. Deprecated:
        Use fetchmany() instead."""
        return apply(self.fetchmany, args, kwargs)

    def fetchallDict(self, *args, **kwargs):
        """Fetch all available rows as a list of dictionaries. Deprecated:
        Use fetchall() instead."""
        return apply(self.fetchall, args, kwargs)


class CursorOldDictRowsMixIn(CursorDictRowsMixIn):

    """This is a MixIn class that returns rows as dictionaries with
    the same key convention as the old Mysqldb (MySQLmodule). Don't
    use this."""

    _fetch_type = 2


class CursorNW(CursorStoreResultMixIn, CursorTupleRowsMixIn,
               BaseCursor):
    """This is a basic Cursor class that returns rows as tuples and
    stores the result set in the client. Warnings are not raised."""

class Cursor(CursorWarningMixIn, CursorNW):
    """This is the standard Cursor class that returns rows as tuples and
    stores the result set in the client. Warnings are raised as necessary."""

class DictCursorNW(CursorStoreResultMixIn, CursorDictRowsMixIn,
                   BaseCursor):
    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client. Warnings are not raised."""

class DictCursor(CursorWarningMixIn, DictCursorNW):
     """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client. Warnings are raised as necessary."""
   
class SSCursorNW(CursorUseResultMixIn, CursorTupleRowsMixIn,
                 BaseCursor):
    """This is a basic Cursor class that returns rows as tuples and
    stores the result set in the server. Warnings are not raised."""

class SSCursor(CursorWarningMixIn, SSCursorNW):
    """This is a Cursor class that returns rows as tuples and
    stores the result set in the server. Warnings are raised as necessary."""

class SSDictCursorNW(CursorUseResultMixIn, CursorDictRowsMixIn,
                     BaseCursor):
    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the server. Warnings are not raised."""

class SSDictCursor(CursorWarningMixIn, SSDictCursorNW):
     """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the server. Warnings are raised as necessary."""


class Connection:

    """Create a connection to the database. Note that this interface
    uses keyword arguments exclusively.
    
    host -- string, host to connect to or NULL pointer (localhost)
    user -- string, user to connect as or NULL (your username)
    passwd -- string, password to use or NULL (no password)
    db -- string, database to use or NULL (no DB selected)
    port -- integer, TCP/IP port to connect to or default MySQL port
    unix_socket -- string, location of unix_socket to use or use TCP
    client_flags -- integer, flags to use or 0 (see MySQL docs)
    conv -- dictionary, maps MySQL FIELD_TYPE.* to Python functions which
            convert a string to the appropriate Python type
    quote_conv -- dictionary, maps Python types or classes to Python
            functions which convert a value of that type (or instance
            of that class) into an SQL literal value
    connect_time -- number of seconds to wait before the connection
            attempt fails.
    compress -- if set, compression is enabled
    init_command -- command which is run once the connection is created
    read_default_file -- see the MySQL documentation for mysql_options()
    read_default_group -- see the MySQL documentation for mysql_options()
    
    Returns a Connection object.

    There are a number of undocumented, non-standard methods. See the
    documentation for the MySQL C API for some hints on what they do.
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
        self.quote_conv[types.StringType] = self.db.string_literal
        self._transactional = self.db.server_capabilities & CLIENT.TRANSACTIONS
        if _threading: self.__lock = _threading.Lock()

    def __del__(self):
        self.close()
        
    if _threading:
        def _acquire(self, blocking=1): return self.__lock.acquire(blocking)
        def _release(self): return self.__lock.release()
    else:
        def _acquire(self, blocking=1): return 1
        def _release(self): return 1
        
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
        """Create a cursor on which queries may be performed.
        The optional cursorclass parameter is used to create
        the Cursor. By default, self.cursorclass=Cursor is used."""
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


def Connect(*args, **kwargs):
    """Factory function for Connection."""
    return apply(Connection, args, kwargs)

connect = Connect
