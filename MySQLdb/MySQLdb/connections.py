"""

This module implements connections for MySQLdb. Presently there is
only one class: Connection. Others are unlikely. However, you might
want to make your own subclasses. In most cases, you will probably
override Connection.default_cursor with a non-standard Cursor class.

"""
import cursors
from _mysql_exceptions import Warning, Error, InterfaceError, DataError, \
     DatabaseError, OperationalError, IntegrityError, InternalError, \
     NotSupportedError, ProgrammingError
import types, _mysql


def defaulterrorhandler(connection, cursor, errorclass, errorvalue):
    """

    If cursor is not None, (errorclass, errorvalue) is appended to
    cursor.messages; otherwise it is appended to
    connection.messages. Then errorclass is raised with errorvalue as
    the value.

    You can override this with your own error handler by assigning it
    to the instance.

    """
    error = errorclass, errorvalue
    if cursor:
        cursor.messages.append(error)
    else:
        connection.messages.append(error)
    raise errorclass, errorvalue


if hasattr(types, "ObjectType"):

    class ConnectionBase(_mysql.connection):

        def _make_connection(self, args, kwargs):
            apply(super(ConnectionBase, self).__init__, args, kwargs)

else:
    
    class ConnectionBase:
        
        def _make_connection(self, args, kwargs):
            self._db = apply(_mysql.connect, args, kwargs)
            
        def __getattr__(self, attr):
            if hasattr(self, "_db"):
                return getattr(self._db, attr)
            raise AttributeError, attr

        
class Connection(ConnectionBase):

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
    unicode -- If set to a string, character columns are returned as
            unicode objects with this encoding. If set to None, the
            default encoding is used. If not set at all, character
            columns are returned as normal strings.
    client_flag -- integer, flags to use or 0 (see MySQL docs or constants/CLIENTS.py)

    There are a number of undocumented, non-standard methods. See the
    documentation for the MySQL C API for some hints on what they do.

    """

    default_cursor = cursors.Cursor
    
    def __init__(self, *args, **kwargs):
        from constants import CLIENT, FIELD_TYPE
        from converters import conversions
        import types
        kwargs2 = kwargs.copy()
        if kwargs.has_key('conv'):
            kwargs2['conv'] = conv = kwargs['conv']
        else:
            kwargs2['conv'] = conv = conversions.copy()
        if kwargs.has_key('cursorclass'):
            self.cursorclass = kwargs['cursorclass']
            del kwargs2['cursorclass']
        else:
            self.cursorclass = self.default_cursor
        if kwargs.has_key('unicode'):
            charset = kwargs['unicode']
            del kwargs2['unicode']
            if charset:
                u = lambda s, c=charset: unicode(s, c)
            else:
                u = unicode
            conv[FIELD_TYPE.CHAR] = u
            conv[FIELD_TYPE.STRING] = u
            conv[FIELD_TYPE.VAR_STRING] = u
        self._make_connection(args, kwargs2)
        self.converter[types.StringType] = self.string_literal
        if hasattr(types, 'UnicodeType'):
            self.converter[types.UnicodeType] = self.unicode_literal
        self._transactional = self.server_capabilities & CLIENT.TRANSACTIONS
        self.messages = []
        
    def __del__(self):
        try:
            self.close()
        except:
            pass
        
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
            self.errorhandler(None,
                              NotSupportedError, "Not supported by server")
            
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

        Non-standard.

        """
        return self.escape(o, self.converter)

    def unicode_literal(self, u, dummy=None):
        """

        Convert a unicode object u to a string using the current
        character set as the encoding. If that's not available,
        latin1 is used.

        Non-standard.

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
