"""MySQLdb Connections Module

This module implements connections for MySQLdb. Presently there is
only one class: Connection. Others are unlikely. However, you might
want to make your own subclasses. In most cases, you will probably
override Connection.default_cursor with a non-standard Cursor class.

"""
import cursors
from _mysql_exceptions import Warning, Error, InterfaceError, DataError, \
     DatabaseError, OperationalError, IntegrityError, InternalError, \
     NotSupportedError, ProgrammingError

def defaulterrorhandler(connection, cursor, errorclass, errorvalue):
    if cursor:
        cursor.messages.append(errorvalue)
    else:
        connection.messages.append(errorvalue)
    raise errorclass, errorvalue


class Connection:

    """

    Create a connection to the database. It is strongly recommended
    that you only use keyword parameters. Consult the MySQL C API
    documentation for more information.

    host -- string, host to connect
    user -- string, user to connect as
    passwd -- string, password to use
    db -- string, database to use
    port -- integer, TCP/IP port to connect to
    unix_socket -- string, location of unix_socket to use
    conv -- conversion dictionary, see MySQLdb.converters
    connect_time -- number of seconds to wait before the connection
            attempt fails.
    compress -- if set, compression is enabled
    named_pipe -- if set, a named pipe is used to connect (Windows only)
    init_command -- command which is run once the connection is created
    read_default_file -- file from which default client values are read
    read_default_group -- configuration group to use from the default file
    cursorclass -- class object, used to create cursors (keyword only)

    There are a number of undocumented, non-standard methods. See the
    documentation for the MySQL C API for some hints on what they do.

    """

    default_cursor = cursors.Cursor
    
    def __init__(self, *args, **kwargs):
        from _mysql import connect
        from constants import CLIENT
        from converters import conversions
        import types
        kwargs2 = kwargs.copy()
        if not kwargs.has_key('conv'):
            kwargs2['conv'] = conversions.copy()
        if kwargs.has_key('cursorclass'):
            self.cursorclass = kwargs['cursorclass']
            del kwargs2['cursorclass']
        else:
            self.cursorclass = self.default_cursor
        self._db = apply(connect, args, kwargs2)
        self._db.converter[types.StringType] = self._db.string_literal
        if hasattr(types, 'UnicodeType'):
            self._db.converter[types.UnicodeType] = self.unicode_literal
        self._transactional = self._db.server_capabilities & CLIENT.TRANSACTIONS
        self.messages = []
        
    def __del__(self):
        if hasattr(self, '_db'): self.close()

    def __getattr__(self, attr):
        return getattr(self._db, attr)
    
    def begin(self):
        """Explicitly begin a transaction. Non-standard."""
        self.query("BEGIN")
        
    def commit(self):
        """Commit the current transaction."""
        if self._transactional:
            self.query("COMMIT")
            
    def rollback(self):
        """Rollback the current transaction."""
        if self._transactional:
            self.query("ROLLBACK")
        else:
            raise NotSupportedError, "Not supported by server"
            
    def cursor(self, cursorclass=None):
        """

        Create a cursor on which queries may be performed. The
        optional cursorclass parameter is used to create the
        Cursor. By default, self.cursorclass=cursors.Cursor is
        used.

        """
        return (cursorclass or self.cursorclass)(self)

    def literal(self, o):
        """

        If o is a single object, returns an SQL literal as a string.
        If o is a non-string sequence, the items of the sequence are
        converted and returned as a sequence.

        """
        import _mysql
        return _mysql.escape(o, self._db.converter)

    def unicode_literal(self, u, dummy=None):
        """

        Convert a unicode object u to a string using the current
        character set as the encoding. If that's not available,
        latin1 is used.

        """
        return self.literal(u.encode(self.character_set_name()))
        
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

    errorhandler = defaulterrorhandler

    
