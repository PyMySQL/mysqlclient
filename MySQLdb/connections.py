"""

This module implements connections for MySQLdb. Presently there is
only one class: Connection. Others are unlikely. However, you might
want to make your own subclasses. In most cases, you will probably
override Connection.default_cursor with a non-standard Cursor class.

"""
from MySQLdb import cursors
from _mysql_exceptions import Warning, Error, InterfaceError, DataError, \
     DatabaseError, OperationalError, IntegrityError, InternalError, \
     NotSupportedError, ProgrammingError
import types, _mysql
import re


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
    del cursor
    del connection
    raise errorclass, errorvalue

re_numeric_part = re.compile(r"^(\d+)")

def numeric_part(s):
    """Returns the leading numeric part of a string.

    >>> numeric_part("20-alpha")
    20
    >>> numeric_part("foo")
    >>> numeric_part("16b")
    16
    """

    m = re_numeric_part.match(s)
    if m:
        return int(m.group(1))
    return None


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

        connect_timeout
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

        sql_mode
          If supplied, the session SQL mode will be changed to this
          setting (MySQL-4.1 and newer). For more details and legal
          values, see the MySQL documentation.

        client_flag
          integer, flags to use or 0
          (see MySQL docs or constants/CLIENTS.py)

        ssl
          dictionary or mapping, contains SSL connection parameters;
          see the MySQL documentation for more details
          (mysql_ssl_set()).  If this is set, and the client does not
          support SSL, NotSupportedError will be raised.

        local_infile
          integer, non-zero enables LOAD LOCAL INFILE; zero disables

        autocommit
          If False (default), autocommit is disabled.
          If True, autocommit is enabled.
          If None, autocommit isn't set and server default is used.

        There are a number of undocumented, non-standard methods. See the
        documentation for the MySQL C API for some hints on what they do.

        """
        from MySQLdb.constants import CLIENT, FIELD_TYPE
        from MySQLdb.converters import conversions
        from weakref import proxy

        kwargs2 = kwargs.copy()

        if 'conv' in kwargs:
            conv = kwargs['conv']
        else:
            conv = conversions

        conv2 = {}
        for k, v in conv.items():
            if isinstance(k, int) and isinstance(v, list):
                conv2[k] = v[:]
            else:
                conv2[k] = v
        kwargs2['conv'] = conv2

        cursorclass = kwargs2.pop('cursorclass', self.default_cursor)
        charset = kwargs2.pop('charset', '')

        if charset:
            use_unicode = True
        else:
            use_unicode = False

        use_unicode = kwargs2.pop('use_unicode', use_unicode)
        sql_mode = kwargs2.pop('sql_mode', '')

        client_flag = kwargs.get('client_flag', 0)
        client_version = tuple([ numeric_part(n) for n in _mysql.get_client_info().split('.')[:2] ])
        if client_version >= (4, 1):
            client_flag |= CLIENT.MULTI_STATEMENTS
        if client_version >= (5, 0):
            client_flag |= CLIENT.MULTI_RESULTS

        kwargs2['client_flag'] = client_flag

        # PEP-249 requires autocommit to be initially off
        autocommit = kwargs2.pop('autocommit', False)

        super(Connection, self).__init__(*args, **kwargs2)
        self.cursorclass = cursorclass
        self.encoders = dict([ (k, v) for k, v in conv.items()
                               if type(k) is not int ])

        self._server_version = tuple([ numeric_part(n) for n in self.get_server_info().split('.')[:2] ])

        db = proxy(self)
        def _get_string_literal():
            def string_literal(obj, dummy=None):
                return db.string_literal(obj)
            return string_literal

        def _get_unicode_literal():
            def unicode_literal(u, dummy=None):
                return db.literal(u.encode(unicode_literal.charset))
            return unicode_literal

        def _get_string_decoder():
            def string_decoder(s):
                return s.decode(string_decoder.charset)
            return string_decoder

        string_literal = _get_string_literal()
        self.unicode_literal = unicode_literal = _get_unicode_literal()
        self.string_decoder = string_decoder = _get_string_decoder()
        if not charset:
            charset = self.character_set_name()
        self.set_character_set(charset)

        if sql_mode:
            self.set_sql_mode(sql_mode)

        if use_unicode:
            self.converter[FIELD_TYPE.STRING].append((None, string_decoder))
            self.converter[FIELD_TYPE.VAR_STRING].append((None, string_decoder))
            self.converter[FIELD_TYPE.VARCHAR].append((None, string_decoder))
            self.converter[FIELD_TYPE.BLOB].append((None, string_decoder))

        self.encoders[types.StringType] = string_literal
        self.encoders[types.UnicodeType] = unicode_literal
        self._transactional = self.server_capabilities & CLIENT.TRANSACTIONS
        if self._transactional:
            if autocommit is not None:
                self.autocommit(autocommit)
        self.messages = []

    def autocommit(self, on):
        on = bool(on)
        if self.get_autocommit() != on:
            _mysql.connection.autocommit(self, on)

    def cursor(self, cursorclass=None):
        """

        Create a cursor on which queries may be performed. The
        optional cursorclass parameter is used to create the
        Cursor. By default, self.cursorclass=cursors.Cursor is
        used.

        """
        return (cursorclass or self.cursorclass)(self)

    def __enter__(self):
        if self.get_autocommit():
            self.query("BEGIN")
        return self.cursor()

    def __exit__(self, exc, value, tb):
        if exc:
            self.rollback()
        else:
            self.commit()

    def literal(self, o):
        """

        If o is a single object, returns an SQL literal as a string.
        If o is a non-string sequence, the items of the sequence are
        converted and returned as a sequence.

        Non-standard. For internal use; do not use this in your
        applications.

        """
        return self.escape(o, self.encoders)

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

    def set_character_set(self, charset):
        """Set the connection character set to charset. The character
        set can only be changed in MySQL-4.1 and newer. If you try
        to change the character set from the current value in an
        older version, NotSupportedError will be raised."""
        if charset == "utf8mb4":
            py_charset = "utf8"
        else:
            py_charset = charset
        if self.character_set_name() != charset:
            try:
                super(Connection, self).set_character_set(charset)
            except AttributeError:
                if self._server_version < (4, 1):
                    raise NotSupportedError("server is too old to set charset")
                self.query('SET NAMES %s' % charset)
                self.store_result()
        self.string_decoder.charset = py_charset
        self.unicode_literal.charset = py_charset

    def set_sql_mode(self, sql_mode):
        """Set the connection sql_mode. See MySQL documentation for
        legal values."""
        if self._server_version < (4, 1):
            raise NotSupportedError("server is too old to set sql_mode")
        self.query("SET SESSION sql_mode='%s'" % sql_mode)
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
        return warnings

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
