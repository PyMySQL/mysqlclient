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

        host
          string, host to connect
          
        user
          string, user to connect as

        passwd
          string, password to use

        db
          string, database to use

        port
          integer, TCP/IP port to connect to

        unix_socket
          string, location of unix_socket to use

        conv
          conversion dictionary, see MySQLdb.converters

        connect_time
          number of seconds to wait before the connection attempt
          fails.

        compress
          if set, compression is enabled

        named_pipe
          if set, a named pipe is used to connect (Windows only)

        init_command
          command which is run once the connection is created

        read_default_file
          file from which default client values are read

        read_default_group
          configuration group to use from the default file

        cursorclass
          class object, used to create cursors (keyword only)

        use_unicode
          If True, text-like columns are returned as unicode objects
          using the connection's character set.  Otherwise, text-like
          columns are returned as strings.  columns are returned as
          normal strings. Unicode objects will always be encoded to
          the connection's character set regardless of this setting.

        client_flag
          integer, flags to use or 0
          (see MySQL docs or constants/CLIENTS.py)

        ssl
          dictionary or mapping, contains SSL connection parameters;
          see the MySQL documentation for more details
          (mysql_ssl_set()).  If this is set, and the client does not
          support SSL, UnsupportedError will be raised.

        local_infile
          integer, non-zero enables LOAD LOCAL INFILE; zero disables
    
        There are a number of undocumented, non-standard methods. See the
        documentation for the MySQL C API for some hints on what they do.

        """
        from constants import CLIENT, FIELD_TYPE
        from converters import conversions
        import types
        from weakref import proxy
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
        use_unicode = kwargs.get('use_unicode', 0)
        if kwargs.has_key('use_unicode'):
            del kwargs2['use_unicode']
                
        super(Connection, self).__init__(*args, **kwargs2)

        self.charset = self.character_set_name().split('_')[0]

        if use_unicode:
            def u(s, self=proxy(self)):
                return s.decode(self.charset)
            conv[FIELD_TYPE.STRING] = u
            conv[FIELD_TYPE.VAR_STRING] = u
            conv[FIELD_TYPE.BLOB].insert(-1, (None, u))

        def string_literal(obj, dummy=None, self=proxy(self)):
            return self.string_literal(obj)
        
        def unicode_literal(u, dummy=None, self=proxy(self)):
            return self.literal(u.encode(self.charset))
         
        self.converter[types.StringType] = string_literal
        self.converter[types.UnicodeType] = unicode_literal
        self._transactional = self.server_capabilities & CLIENT.TRANSACTIONS
        if self._transactional:
            # PEP-249 requires autocommit to be initially off
            self.autocommit(0)
        self.messages = []
        
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

        Non-standard. For internal use; do not use this in your
        applications.

        """
        return self.escape(o, self.converter)

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
