"""MySQLdb Cursors

This module implements Cursors of various types for MySQLdb. By
default, MySQLdb uses the Cursor class.

"""

import re
import sys
PY2 = sys.version_info[0] == 2

from MySQLdb.compat import unicode

restr = r"""
    \s
    values
    \s*
    (
        \(
            [^()']*
            (?:
                (?:
                        (?:\(
                            # ( - editor highlighting helper
                            .*
                        \))
                    |
                        '
                            [^\\']*
                            (?:\\.[^\\']*)*
                        '
                )
                [^()']*
            )*
        \)
    )
"""

insert_values = re.compile(restr, re.S | re.I | re.X)

from _mysql_exceptions import Warning, Error, InterfaceError, DataError, \
     DatabaseError, OperationalError, IntegrityError, InternalError, \
     NotSupportedError, ProgrammingError


class BaseCursor(object):
    """A base for Cursor classes. Useful attributes:
    
    description
        A tuple of DB API 7-tuples describing the columns in
        the last executed query; see PEP-249 for details.

    description_flags
        Tuple of column flags for last query, one entry per column
        in the result set. Values correspond to those in
        MySQLdb.constants.FLAG. See MySQL documentation (C API)
        for more information. Non-standard extension.
    
    arraysize
        default number of rows fetchmany() will fetch
    """

    from _mysql_exceptions import MySQLError, Warning, Error, InterfaceError, \
         DatabaseError, DataError, OperationalError, IntegrityError, \
         InternalError, ProgrammingError, NotSupportedError
    
    _defer_warnings = False
    
    def __init__(self, connection):
        from weakref import ref
    
        self.connection = ref(connection)
        self.description = None
        self.description_flags = None
        self.rowcount = -1
        self.arraysize = 1
        self._executed = None
        self.lastrowid = None
        self.messages = []
        self.errorhandler = connection.errorhandler
        self._result = None
        self._warnings = 0
        self._info = None
        self.rownumber = None
        
    def close(self):
        """Close the cursor. No further queries will be possible."""
        try:
            if self.connection is None or self.connection() is None:
                return
            while self.nextset():
                pass
        finally:
            self.connection = None
            self.errorhandler = None
            self._result = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        del exc_info
        self.close()

    def _check_executed(self):
        if not self._executed:
            self.errorhandler(self, ProgrammingError, "execute() first")

    def _warning_check(self):
        from warnings import warn
        if self._warnings:
            # When there is next result, fetching warnings cause "command
            # out of sync" error.
            if self._result and self._result.has_next:
                msg = "There are %d MySQL warnings." % (self._warnings,)
                self.messages.append(msg)
                warn(msg, self.Warning, 3)
                return

            warnings = self._get_db().show_warnings()
            if warnings:
                # This is done in two loops in case
                # Warnings are set to raise exceptions.
                for w in warnings:
                    self.messages.append((self.Warning, w))
                for w in warnings:
                    warn(w[-1], self.Warning, 3)
            elif self._info:
                self.messages.append((self.Warning, self._info))
                warn(self._info, self.Warning, 3)

    def nextset(self):
        """Advance to the next result set.

        Returns None if there are no more result sets.
        """
        if self._executed:
            self.fetchall()
        del self.messages[:]

        db = self._get_db()
        nr = db.next_result()
        if nr == -1:
            return None
        self._do_get_result()
        self._post_get_result()
        self._warning_check()
        return 1

    def _post_get_result(self): pass

    def _do_get_result(self):
        db = self._get_db()
        self._result = self._get_result()
        self.rowcount = db.affected_rows()
        self.rownumber = 0
        self.description = self._result and self._result.describe() or None
        self.description_flags = self._result and self._result.field_flags() or None
        self.lastrowid = db.insert_id()
        self._warnings = db.warning_count()
        self._info = db.info()
    
    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
      
    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""

    def _get_db(self):
        con = self.connection
        if con is not None:
            con = con()
        if con is None:
            raise ProgrammingError("cursor closed")
        return con
    
    def execute(self, query, args=None):
        """Execute a query.
        
        query -- string, query to execute on server
        args -- optional sequence or mapping, parameters to use with query.

        Note: If args is a sequence, then %s must be used as the
        parameter placeholder in the query. If a mapping is used,
        %(key)s must be used as the placeholder.

        Returns long integer rows affected, if any
        """
        while self.nextset():
            pass
        db = self._get_db()

        # NOTE:
        # Python 2: query should be bytes when executing %.
        # All unicode in args should be encoded to bytes on Python 2.
        # Python 3: query should be str (unicode) when executing %.
        # All bytes in args should be decoded with ascii and surrogateescape on Python 3.
        # db.literal(obj) always returns str.

        if PY2 and isinstance(query, unicode):
            query = query.encode(db.unicode_literal.charset)

        if args is not None:
            if isinstance(args, dict):
                args = dict((key, db.literal(item)) for key, item in args.items())
            else:
                args = tuple(map(db.literal, args))
            if not PY2 and isinstance(query, bytes):
                query = query.decode(db.unicode_literal.charset)
            query = query % args

        if isinstance(query, unicode):
            query = query.encode(db.unicode_literal.charset, 'surrogateescape')

        res = None
        try:
            res = self._query(query)
        except TypeError as m:
            if m.args[0] in ("not enough arguments for format string",
                             "not all arguments converted"):
                self.errorhandler(self, ProgrammingError, m.args[0])
            else:
                self.errorhandler(self, TypeError, m)
        except Exception:
            exc, value = sys.exc_info()[:2]
            self.errorhandler(self, exc, value)
        self._executed = query
        if not self._defer_warnings: self._warning_check()
        return res

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
        del self.messages[:]
        db = self._get_db()
        if not args: return
        if PY2 and isinstance(query, unicode):
            query = query.encode(db.unicode_literal.charset)
        elif not PY2 and isinstance(query, bytes):
            query = query.decode(db.unicode_literal.charset)
        m = insert_values.search(query)
        if not m:
            r = 0
            for a in args:
                r = r + self.execute(query, a)
            return r
        p = m.start(1)
        e = m.end(1)
        qv = m.group(1)
        try:
            q = []
            for a in args:
                if isinstance(a, dict):
                    q.append(qv % dict((key, db.literal(item))
                                       for key, item in a.items()))
                else:
                    q.append(qv % tuple([db.literal(item) for item in a]))
        except TypeError as msg:
            if msg.args[0] in ("not enough arguments for format string",
                               "not all arguments converted"):
                self.errorhandler(self, ProgrammingError, msg.args[0])
            else:
                self.errorhandler(self, TypeError, msg)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            exc, value = sys.exc_info()[:2]
            self.errorhandler(self, exc, value)
        qs = '\n'.join([query[:p], ',\n'.join(q), query[e:]])
        if not PY2:
            qs = qs.encode(db.unicode_literal.charset, 'surrogateescape')
        r = self._query(qs)
        if not self._defer_warnings: self._warning_check()
        return r

    def callproc(self, procname, args=()):
        """Execute stored procedure procname with args

        procname -- string, name of procedure to execute on server

        args -- Sequence of parameters to use with procedure

        Returns the original args.

        Compatibility warning: PEP-249 specifies that any modified
        parameters must be returned. This is currently impossible
        as they are only available by storing them in a server
        variable and then retrieved by a query. Since stored
        procedures return zero or more result sets, there is no
        reliable way to get at OUT or INOUT parameters via callproc.
        The server variables are named @_procname_n, where procname
        is the parameter above and n is the position of the parameter
        (from zero). Once all result sets generated by the procedure
        have been fetched, you can issue a SELECT @_procname_0, ...
        query using .execute() to get any OUT or INOUT values.

        Compatibility warning: The act of calling a stored procedure
        itself creates an empty result set. This appears after any
        result sets generated by the procedure. This is non-standard
        behavior with respect to the DB-API. Be sure to use nextset()
        to advance through all result sets; otherwise you may get
        disconnected.
        """

        db = self._get_db()
        for index, arg in enumerate(args):
            q = "SET @_%s_%d=%s" % (procname, index,
                                         db.literal(arg))
            if isinstance(q, unicode):
                q = q.encode(db.unicode_literal.charset)
            self._query(q)
            self.nextset()

        q = "CALL %s(%s)" % (procname,
                             ','.join(['@_%s_%d' % (procname, i)
                                       for i in range(len(args))]))
        if isinstance(q, unicode):
            q = q.encode(db.unicode_literal.charset)
        self._query(q)
        self._executed = q
        if not self._defer_warnings:
            self._warning_check()
        return args

    def _do_query(self, q):
        db = self._get_db()
        self._last_executed = q
        db.query(q)
        self._do_get_result()
        return self.rowcount

    def _query(self, q):
        return self._do_query(q)

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


class CursorStoreResultMixIn(object):

    """This is a MixIn class which causes the entire result set to be
    stored on the client side, i.e. it uses mysql_store_result(). If the
    result set can be very large, consider adding a LIMIT clause to your
    query, or using CursorUseResultMixIn instead."""

    def _get_result(self): return self._get_db().store_result()

    def _query(self, q):
        rowcount = self._do_query(q)
        self._post_get_result()
        return rowcount

    def _post_get_result(self):
        self._rows = self._fetch_row(0)
        self._result = None

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
        if self.rownumber:
            result = self._rows[self.rownumber:]
        else:
            result = self._rows
        self.rownumber = len(self._rows)
        return result

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
                              "unknown scroll mode %s" % repr(mode))
        if r < 0 or r >= len(self._rows):
            self.errorhandler(self, IndexError, "out of range")
        self.rownumber = r

    def __iter__(self):
        self._check_executed()
        result = self.rownumber and self._rows[self.rownumber:] or self._rows
        return iter(result)


class CursorUseResultMixIn(object):

    """This is a MixIn class which causes the result set to be stored
    in the server and sent row-by-row to client side, i.e. it uses
    mysql_use_result(). You MUST retrieve the entire result set and
    close() the cursor before additional queries can be peformed on
    the connection."""

    _defer_warnings = True

    def _get_result(self): return self._get_db().use_result()

    def fetchone(self):
        """Fetches a single row from the cursor."""
        self._check_executed()
        r = self._fetch_row(1)
        if not r:
            self._warning_check()
            return None
        self.rownumber = self.rownumber + 1
        return r[0]

    def fetchmany(self, size=None):
        """Fetch up to size rows from the cursor. Result set may be smaller
        than size. If size is not defined, cursor.arraysize is used."""
        self._check_executed()
        r = self._fetch_row(size or self.arraysize)
        self.rownumber = self.rownumber + len(r)
        if not r:
            self._warning_check()
        return r

    def fetchall(self):
        """Fetchs all available rows from the cursor."""
        self._check_executed()
        r = self._fetch_row(0)
        self.rownumber = self.rownumber + len(r)
        self._warning_check()
        return r

    def __iter__(self):
        return self

    def next(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    __next__ = next


class CursorTupleRowsMixIn(object):
    """This is a MixIn class that causes all rows to be returned as tuples,
    which is the standard form required by DB API."""

    _fetch_type = 0


class CursorDictRowsMixIn(object):
    """This is a MixIn class that causes all rows to be returned as
    dictionaries. This is a non-standard feature."""

    _fetch_type = 1

    def fetchoneDict(self):
        """Fetch a single row as a dictionary. Deprecated:
        Use fetchone() instead. Will be removed in 1.3."""
        from warnings import warn
        warn("fetchoneDict() is non-standard and will be removed in 1.3",
             DeprecationWarning, 2)
        return self.fetchone()

    def fetchmanyDict(self, size=None):
        """Fetch several rows as a list of dictionaries. Deprecated:
        Use fetchmany() instead. Will be removed in 1.3."""
        from warnings import warn
        warn("fetchmanyDict() is non-standard and will be removed in 1.3",
             DeprecationWarning, 2)
        return self.fetchmany(size)

    def fetchallDict(self):
        """Fetch all available rows as a list of dictionaries. Deprecated:
        Use fetchall() instead. Will be removed in 1.3."""
        from warnings import warn
        warn("fetchallDict() is non-standard and will be removed in 1.3",
             DeprecationWarning, 2)
        return self.fetchall()


class CursorOldDictRowsMixIn(CursorDictRowsMixIn):
    """This is a MixIn class that returns rows as dictionaries with
    the same key convention as the old Mysqldb (MySQLmodule). Don't
    use this."""

    _fetch_type = 2


class Cursor(CursorStoreResultMixIn, CursorTupleRowsMixIn,
             BaseCursor):
    """This is the standard Cursor class that returns rows as tuples
    and stores the result set in the client."""


class DictCursor(CursorStoreResultMixIn, CursorDictRowsMixIn,
                 BaseCursor):
     """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client."""


class SSCursor(CursorUseResultMixIn, CursorTupleRowsMixIn,
               BaseCursor):
    """This is a Cursor class that returns rows as tuples and stores
    the result set in the server."""


class SSDictCursor(CursorUseResultMixIn, CursorDictRowsMixIn,
                   BaseCursor):
    """This is a Cursor class that returns rows as dictionaries and
    stores the result set in the server."""


