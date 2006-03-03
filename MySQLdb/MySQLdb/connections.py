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

        charset
          If supplied, the connection character set will be changed
          to this character set (MySQL-4.1 and newer). This implies
          use_unicode=True.
          
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

        kwargs2 = kwargs.copy()
        if kwargs.has_key('conv'):
            kwargs2['conv'] = conv = kwargs['conv'].copy()
        else:
            kwargs2['conv'] = conv = conversions.copy()
        if kwargs.has_key('cursorclass'):
            self.cursorclass = kwargs['cursorclass']
            del kwargs2['cursorclass']
        else:
            self.cursorclass = self.default_cursor

        charset = kwargs.get('charset', '')
        if kwargs.has_key('charset'):
            del kwargs2['charset']
        if charset:
            use_unicode = True
        else:
            use_unicode = False
        use_unicode = kwargs.get('use_unicode', use_unicode)
        if kwargs.has_key('use_unicode'):
            del kwargs2['use_unicode']
            
        client_flag = kwargs.get('client_flag', 0)
        client_version = tuple([ int(n) for n in _mysql.get_client_info().split('.')[:2] ])
        if client_version >= (4, 1):
            client_flag |= CLIENT.MULTI_STATEMENTS
        if client_version >= (5, 0):
            client_flag |= CLIENT.MULTI_RESULTS
            
        kwargs2['client_flag'] = client_flag

        super(Connection, self).__init__(*args, **kwargs2)

        self._server_version = tuple([ int(n) for n in self.get_server_info().split('.')[:2] ])
        self.charset = self.character_set_name()

        if charset and self.charset != charset:
            if self._server_version < (4, 1):
                raise UnsupportedError, "server is too old to change charset"
            self.set_character_set(charset)
            self.charset = charset

        if use_unicode:
            def u(s):
                # can't refer to self.character_set_name()
                # because this results in reference cycles
                # and memory leaks
                return s.decode(charset)
            conv[FIELD_TYPE.STRING].insert(-1, (None, u))
            conv[FIELD_TYPE.VAR_STRING].insert(-1, (None, u))
            conv[FIELD_TYPE.BLOB].insert(-1, (None, u))

        def string_literal(obj, dummy=None):
            return self.string_literal(obj)
        
        def unicode_literal(u, dummy=None):
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

    def begin(self):
        """Explicitly begin a connection. Non-standard.
        DEPRECATED: Will be removed in 1.3.
        Use an SQL BEGIN statement instead."""
        from warnings import warn
        warn("begin() is non-standard and will be removed in 1.3",
             DeprecationWarning, 2)
        self.query("BEGIN")
        
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

    if not hasattr(_mysql.connection, 'set_character_set'):

        def set_character_set(self, charset):
            """Set the connection character set. This version
            uses the SET NAMES <charset> SQL statement.

            You probably shouldn't try to change character sets
            after opening the connection."""
            self.query('SET NAMES %s' % charset)
            self.store_result()
            
    def show_warnings(self):
        """Return detailed information about warnings as a
        sequence of tuples of (Level, Code, Message). This
        is only supported in MySQL-4.1 and up. If your server
        is an earlier version, an empty sequence is returned."""
        if self._server_version < (4,1): return ()
        self.query("SHOW WARNINGS")
        r = self.store_result()
        warnings = r.fetch_row(0)
        return [ (level.tostring(), int(code), message.tostring())
                 for level, code, message in warnings ]
    
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
