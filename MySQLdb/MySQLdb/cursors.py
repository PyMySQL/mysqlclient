"""MySQLdb Cursors

This module implements Cursors of various types for MySQLdb. By
default, MySQLdb uses the Cursor class.

"""

import re
insert_values = re.compile(r'values\s(\(.+\))', re.IGNORECASE)
from _mysql import escape, ProgrammingError, Warning

class BaseCursor:
    
    """A base for Cursor classes. Useful attributes:
    
    description -- DB API 7-tuple describing columns in last query
    arraysize -- default number of rows fetchmany() will fetch
    
    See the MySQL docs for more information."""

    def __init__(self, connection):
        self.__conn = connection
        self.description = None
        self.rowcount = -1
        self.arraysize = 100
        self._executed = None
        self._transaction = 0
        self.__c_locked = 0

    def __del__(self):
        self.close()
        
    def close(self):
        """Close the cursor. No further queries will be possible."""
        if not self.__conn: return
        self._end()
        self.__conn = None
        self._executed = None
        self._transaction = None

    def _check_executed(self):
        if not self._executed:
            raise ProgrammingError, "execute() first"
        
    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
      
    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""

    def _get_db(self):
        if not self.__conn:
            raise ProgrammingError, "cursor closed"
        return self.__conn._db
    
    def execute(self, query, args=None):

        """Execute a query.
        
        query -- string, query to execute on server
        args -- sequence or mapping, parameters to use with query.
        returns long integer rows affected, if any"""

        from types import ListType, TupleType
        qc = self._get_db().converter
        if not args:
            r = self._query(query)
        elif type(args) is ListType and type(args[0]) is TupleType:
 	    r = self.executemany(query, args) # deprecated
 	else:
            try:
                r = self._query(query % escape(args, qc))
	    except TypeError, m:
                if m.args[0] in ("not enough arguments for format string",
                                 "not all arguments converted"):
                    raise ProgrammingError, m.args[0]
                else:
                    raise
        self._executed = query
        return r

    def executemany(self, query, args):

        """Execute a multi-row query.
        
        query -- string, query to execute on server
        args -- sequence of sequences or mappings, parameters to use with
            query. The query must contain the clause "values ( ... )".
            The parenthetical portion will be repeated once for each
            item in the sequence.
        returns long integer rows affected, if any
        
        This method performs multiple-row inserts and similar queries."""

        from string import join
        qc = self._get_db().converter
        m = insert_values.search(query)
        if not m: raise ProgrammingError, "can't find values"
        p = m.start(1)
        qv = query[p:]
        qargs = escape(args, qc)
        try:
            q = [ query % qargs[0] ]
            for a in qargs[1:]: q.append( qv % a )
	except TypeError, msg:
            if msg.args[0] in ("not enough arguments for format string",
                               "not all arguments converted"):
                raise ProgrammingError, (0, msg.args[0])
            else:
                raise
        r = self._query(join(q,',\n'))
        self._executed = query
        return r

    def __do_query(self, q):
        from string import split, atoi
        db = self._get_db()
        if self._transaction: self._begin()
        try:
            db.query(q)
            self._result = self._get_result()
            self.rowcount = db.affected_rows()
            self.description = self._result and self._result.describe() or None
            self._insert_id = db.insert_id()
            self._info = db.info()
            self._check_for_warnings()
        except:
            self._end()
            raise
        return self.rowcount

    def _check_for_warnings(self): pass

    _query = __do_query

    def info(self):
        """Return some information about the last query (db.info())"""
        self._check_executed()
        return self._info
    
    def insert_id(self):
        """Return the last inserted ID on an AUTO_INCREMENT columns."""
        self._check_executed()
        return self._insert_id
    
    def nextset(self):
        """Does nothing. Required by DB API."""
        self._check_executed()
        return None

    def _fetch_row(self, size=1):
        return self._result.fetch_row(size, self._fetch_type)

    def _begin(self):
        self.__conn._begin()
        self._transaction = 1

    def _end(self):
        self._transaction = 0
        self.__conn._end()

    def _acquire(self):
        if self.__c_locked: return
        self.__conn._acquire()
        self.__c_locked = 1

    def _release(self):
        if not self.__conn: return
        self.__conn._release()
        self.__c_locked = 0
    
    def _is_transactional(self):
        return self.__conn._transactional

        
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

    def __init__(self, connection):
        BaseCursor.__init__(self, connection)
        self._acquire()
        
    def _get_result(self): return self._get_db().store_result()

    def close(self):
        """Close the cursor. Further queries will not be possible."""
        self._rows = ()
        BaseCursor.close(self)

    def _query(self, q):
        self._acquire()
        try:
            rowcount = self._BaseCursor__do_query(q)
            self._rows = self._result and self._fetch_row(0) or ()
            self._pos = 0
            del self._result
            if not self._is_transactional: self._end()
            return rowcount
        finally:
            self._release()
            
    def fetchone(self):
        """Fetches a single row from the cursor."""
        self._check_executed()
        if self._pos >= len(self._rows): return None
        result = self._rows[self._pos]
        self._pos = self._pos+1
        return result

    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_executed()
        end = self._pos + size or self.arraysize
        result = self._rows[self._pos:end]
        self._pos = end
        return result

    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_executed()
        result = self._pos and self._rows[self._pos:] or self._rows
        self._pos = len(self._rows)
        return result
    
    def seek(self, row, whence=0):
        """seek to a given row of the result set analogously to file.seek().
        This is non-standard extension."""
        self._check_executed()
        if whence == 0:
            self._pos = row
        elif whence == 1:
            self._pos = self._pos + row
        elif whence == 2:
            self._pos = len(self._rows) + row
     
    def tell(self):
        """Return the current position in the result set analogously to
        file.tell(). This is a non-standard extension."""
        self._check_executed()
        return self._pos


class CursorUseResultMixIn:

    """This is a MixIn class which causes the result set to be stored
    in the server and sent row-by-row to client side, i.e. it uses
    mysql_use_result(). You MUST retrieve the entire result set and
    close() the cursor before additional queries can be peformed on
    the connection."""

    def close(self):
        """Close the cursor. No further queries can be executed."""
        self._release()
        self._result = None
        BaseCursor.close(self)

    def _get_result(self): return self._get_db().use_result()

    def fetchone(self):
        """Fetches a single row from the cursor."""
        self._check_executed()
        r = self._fetch_row(1)
        return r and r[0] or None
             
    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_executed()
        return self._fetch_row(size or self.arraysize)
         
    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_open()
        return self._fetch_row(0)


class CursorTupleRowsMixIn:

    """This is a MixIn class that causes all rows to be returned as tuples,
    which is the standard form required by DB API."""

    _fetch_type = 0


class CursorDictRowsMixIn:

    """This is a MixIn class that causes all rows to be returned as
    dictionaries. This is a non-standard feature."""

    _fetch_type = 1

    def fetchoneDict(self):
        """Fetch a single row as a dictionary. Deprecated:
        Use fetchone() instead."""
        return self.fetchone()

    def fetchmanyDict(self, size=None):
        """Fetch several rows as a list of dictionaries. Deprecated:
        Use fetchmany() instead."""
        return self.fetchmany(size)

    def fetchallDict(self):
        """Fetch all available rows as a list of dictionaries. Deprecated:
        Use fetchall() instead."""
        return self.fetchall()


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

    """This is the standard Cursor class that returns rows as tuples
    and stores the result set in the client. Warnings are raised as
    necessary."""


class DictCursorNW(CursorStoreResultMixIn, CursorDictRowsMixIn,
                   BaseCursor):

    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client. Warnings are not raised."""


class DictCursor(CursorWarningMixIn, DictCursorNW):

     """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client. Warnings are raised as
    necessary."""
   

class SSCursorNW(CursorUseResultMixIn, CursorTupleRowsMixIn,
                 BaseCursor):

    """This is a basic Cursor class that returns rows as tuples and
    stores the result set in the server. Warnings are not raised."""


class SSCursor(CursorWarningMixIn, SSCursorNW):

    """This is a Cursor class that returns rows as tuples and stores
    the result set in the server. Warnings are raised as necessary."""


class SSDictCursorNW(CursorUseResultMixIn, CursorDictRowsMixIn,
                     BaseCursor):

    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the server. Warnings are not raised."""


class SSDictCursor(CursorWarningMixIn, SSDictCursorNW):

    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the server. Warnings are raised as
    necessary."""


