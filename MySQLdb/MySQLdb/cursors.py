"""MySQLdb Cursors

This module implements Cursors of various types for MySQLdb. By
default, MySQLdb uses the Cursor class.

"""

import re
insert_values = re.compile(r'\svalues\s*(\(.+\))', re.IGNORECASE)
from _mysql_exceptions import Warning, Error, InterfaceError, DataError, \
     DatabaseError, OperationalError, IntegrityError, InternalError, \
     NotSupportedError, ProgrammingError


class BaseCursor:
    
    """A base for Cursor classes. Useful attributes:
    
    description -- DB API 7-tuple describing columns in last query
    arraysize -- default number of rows fetchmany() will fetch
    
    See the MySQL docs for more information."""

    from _mysql_exceptions import MySQLError, Warning, Error, InterfaceError, \
         DatabaseError, DataError, OperationalError, IntegrityError, \
         InternalError, ProgrammingError, NotSupportedError

    def __init__(self, connection):
        self.connection = connection
        self.description = None
        self.rowcount = -1
        self.arraysize = 100
        self._executed = None
        self.lastrowid = None
        self.messages = []
        self.errorhandler = connection.errorhandler
        self._result = None
        
    def __del__(self):
        self.close()
        
    def close(self):
        """Close the cursor. No further queries will be possible."""
        if not self.connection: return
        del self.messages[:]
        self.nextset()
        self.connection = None
        self.errorhandler = None
        self._result = None

    def _check_executed(self):
        if not self._executed:
            self.errorhandler(self, ProgrammingError, "execute() first")

    def nextset(self):
        """Advance to the next result set.

        Returns None if there are no more result sets.

        Note that MySQL does not support multiple result sets at this
        time.

        """
        del self.messages[:]
        if self._executed:
            self.fetchall()
        return None
    
    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
      
    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""

    def _get_db(self):
        if not self.connection:
            self.errorhandler(self, ProgrammingError, "cursor closed")
        return self.connection
    
    def execute(self, query, args=None):

        """Execute a query.
        
        query -- string, query to execute on server
        args -- optional sequence or mapping, parameters to use with query.

        Note: If args is a sequence, then %s must be used as the
        parameter placeholder in the query. If a mapping is used,
        %(key)s must be used as the placeholder.

        Returns long integer rows affected, if any

        """
        del self.messages[:]
        return self._execute(query, args)
    
    def _execute(self, query, args):
        from types import ListType, TupleType
        from sys import exc_info
        try:
            if args is None:
                r = self._query(query)
            else:
                r = self._query(query % self.connection.literal(args))
        except TypeError, m:
            if m.args[0] in ("not enough arguments for format string",
                             "not all arguments converted"):
                self.errorhandler(self, ProgrammingError, m.args[0])
            else:
                self.errorhandler(self, TypeError, m)
        except:
            exc, value, tb = exc_info()
            del tb
            self.errorhandler(self, exc, value)
        self._executed = query
        return r

    def executemany(self, query, args):

        """Execute a multi-row query.
        
        query -- string, query to execute on server

        args

            Sequence of sequences or mappings, parameters to use with
            query.
            
        Returns long integer rows affected, if any.
        
        This method improves performance on multiple-row INSERT and
        REPLACE. Otherwise it is equivalent to looping over args with
        execute().

        """
        from string import join
        from sys import exc_info
        del self.messages[:]
        if not args: return
        m = insert_values.search(query)
        if not m:
            r = 0
            for a in args:
                r = r + self._execute(query, a)
            return r
        p = m.start(1)
        qv = query[p:]
        qargs = self.connection.literal(args)
        try:
            q = [ query % qargs[0] ]
            for a in qargs[1:]: q.append( qv % a )
        except TypeError, msg:
            if msg.args[0] in ("not enough arguments for format string",
                               "not all arguments converted"):
                self.errorhandler(self, ProgrammingError, msg.args[0])
            else:
                self.errorhandler(self, TypeError, msg)
        except:
            exc, value, tb = exc_info()
            del tb
            self.errorhandler(self, exc, value)
        r = self._query(join(q,',\n'))
        self._executed = query
        return r

    def __do_query(self, q):

        from string import split, atoi
        db = self._get_db()
        db.query(q)
        self._result = self._get_result()
        self.rowcount = db.affected_rows()
        self.rownumber = 0
        self.description = self._result and self._result.describe() or None
        self.lastrowid = db.insert_id()
        self._check_for_warnings()
        return self.rowcount

    def _check_for_warnings(self): pass

    _query = __do_query

    def info(self):
        """Return some information about the last query (db.info())
        DEPRECATED: Use messages attribute"""
        self._check_executed()
        if self.messages:
            return self.messages[-1]
        else:
            return ''
        
    def insert_id(self):
        """Return the last inserted ID on an AUTO_INCREMENT columns.
        DEPRECATED: use lastrowid attribute"""
        self._check_executed()
        return self.lastrowid
    
    def _fetch_row(self, size=1):
        if not self._result:
            return ()
        return self._result.fetch_row(size, self._fetch_type)

    def __iter__(self):
        return iter(self.fetchone, None)

    Warning = Warning
    Error = Error
    InterfaceError = InterfaceError
    DatabaseError = DatabaseError
    DataError = DataError
    OperationalError = OperationalError
    IntegrityError = IntegrityError
    InternalError = InternalError
    ProgrammingError = ProgrammingError
    NotSupportedError = NotSupportedError
   
        
class CursorWarningMixIn:

    """This is a MixIn class that provides the capability of raising
    the Warning exception when something went slightly wrong with your
    query."""

    def _check_for_warnings(self):
        from string import atoi, split
        info = self._get_db().info()
        if not info:
            return
        warnings = atoi(split(info)[-1])
        if warnings:
            raise Warning, info


class CursorStoreResultMixIn:

    """This is a MixIn class which causes the entire result set to be
    stored on the client side, i.e. it uses mysql_store_result(). If the
    result set can be very large, consider adding a LIMIT clause to your
    query, or using CursorUseResultMixIn instead."""

    def _get_result(self): return self._get_db().store_result()

    def close(self):
        """Close the cursor. Further queries will not be possible."""
        self._rows = ()
        BaseCursor.close(self)

    def _query(self, q):
        rowcount = self._BaseCursor__do_query(q)
        self._rows = self._fetch_row(0)
        self._result = None
        return rowcount
            
    def fetchone(self):
        """Fetches a single row from the cursor. None indicates that
        no more rows are available."""
        self._check_executed()
        if self.rownumber >= len(self._rows): return None
        result = self._rows[self.rownumber]
        self.rownumber = self.rownumber+1
        return result

    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_executed()
        end = self.rownumber + (size or self.arraysize)
        result = self._rows[self.rownumber:end]
        self.rownumber = min(end, len(self._rows))
        return result

    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_executed()
        result = self.rownumber and self._rows[self.rownumber:] or self._rows
        self.rownumber = len(self._rows)
        return result
    
    def seek(self, row, whence=0):
        """seek to a given row of the result set analogously to file.seek().
        This is non-standard extension. DEPRECATED: Use scroll method"""
        self._check_executed()
        if whence == 0:
            self.rownumber = row
        elif whence == 1:
            self.rownumber = self.rownumber + row
        elif whence == 2:
            self.rownumber = len(self._rows) + row
     
    def tell(self):
        """Return the current position in the result set analogously to
        file.tell(). This is a non-standard extension. DEPRECATED:
        use rownumber attribute"""
        self._check_executed()
        return self.rownumber

    def scroll(self, value, mode='relative'):
        """Scroll the cursor in the result set to a new position according
        to mode.
        
        If mode is 'relative' (default), value is taken as offset to
        the current position in the result set, if set to 'absolute',
        value states an absolute target position."""
        self._check_executed()
        if mode == 'relative':
            r = self.rownumber + value
        elif mode == 'absolute':
            r = value
        else:
            self.errorhandler(self, ProgrammingError,
                              "unknown scroll mode %s" % `mode`)
        if r < 0 or r >= len(self._rows):
            self.errorhandler(self, IndexError, "out of range")
        self.rownumber = r

    def __iter__(self):
        self._check_executed()
        result = self.rownumber and self._rows[self.rownumber:] or self._rows
        return iter(result)
    

class CursorUseResultMixIn:

    """This is a MixIn class which causes the result set to be stored
    in the server and sent row-by-row to client side, i.e. it uses
    mysql_use_result(). You MUST retrieve the entire result set and
    close() the cursor before additional queries can be peformed on
    the connection."""

    def close(self):
        """Close the cursor. No further queries can be executed."""
        del self.messages[:]
        self.nextset()
        self._result = None
        BaseCursor.close(self)

    def _get_result(self): return self._get_db().use_result()

    def fetchone(self):
        """Fetches a single row from the cursor."""
        self._check_executed()
        r = self._fetch_row(1)
        if not r: return None
        self.rownumber = self.rownumber + 1
        return r[0]
             
    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_executed()
        r = self._fetch_row(size or self.arraysize)
        self.rownumber = self.rownumber + len(r)
        return r
         
    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_executed()
        r = self._fetch_row(0)
        self.rownumber = self.rownumber + len(r)
        return r
    

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


