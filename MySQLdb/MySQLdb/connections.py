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


class Connection(_mysql.connection):

    """MySQL Database Connection Object"""

    default_cursor = cursors.Cursor
    
    def __init__(self, *args, **kwargs):
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
        unicode_errors -- If set to a string, this is used as the errors
                parameter to the unicode function; by default it is
                'strict'. See documentation for unicode for more details.
        client_flag -- integer, flags to use or 0
               (see MySQL docs or constants/CLIENTS.py)
        ssl -- dictionary or mapping, contains SSL connection parameters; see
               the MySQL documentation for more details (mysql_ssl_set()).
               If this is set, and the client does not support SSL,
               UnsupportedError will be raised.

        There are a number of undocumented, non-standard methods. See the
        documentation for the MySQL C API for some hints on what they do.

        """
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
            errors = kwargs.get('unicode_errors', 'strict')
            del kwargs2['unicode']
            if kwargs.has_key('unicode_errors'):
                del kwargs2['unicode_errors']
            if charset:
                self.charset = charset
                u = lambda s, c=charset, e=errors: unicode(s, c, e)
            else:
                u = unicode
            conv[FIELD_TYPE.STRING] = u
            conv[FIELD_TYPE.VAR_STRING] = u
            conv[FIELD_TYPE.BLOB].insert(-1, (None, u))
        super(Connection, self).__init__(*args, **kwargs2)
        self.converter[types.StringType] = self.string_literal
        self.converter[types.UnicodeType] = self.unicode_literal
        self._transactional = self.server_capabilities & CLIENT.TRANSACTIONS
        if self._transactional:
            # PEP-249 requires autocommit to be initially off
            self.autocommit(0)
        self.messages = []
        
    def __del__(self):
        try:
            self.close()
        except:
            pass

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
        return self.literal(u.encode(self.charset))

    if not hasattr(_mysql.connection, 'warning_count'):

        def warning_count(self):
            """Return the number of warnings generated from the
            last query. This is derived from the info() method."""
            from string import atoi
            info = self.info()
            if info:
                return atoi(info.split()[-1])
            else:
                return 0
            
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
