"""MySQLdb Connections Module

This module implements connections for MySQLdb. Presently there is
only one class: Connection. Others are unlikely. However, you might
want to make your own subclasses. In most cases, you will probably
override Connection.default_cursor with a non-standard Cursor class.

"""
import cursors
from _mysql_exceptions import NotSupportedError, ProgrammingError

class Connection:

    """Create a connection to the database. It is strongly recommended
    that you only use keyword parameters. "NULL pointer" indicates that
    NULL will be passed to mysql_real_connect(); the value in parenthesis
    indicates how MySQL interprets the NULL. Consult the MySQL C API
    documentation for more information.

    host -- string, host to connect to or NULL pointer (localhost)
    user -- string, user to connect as or NULL pointer (your username)
    passwd -- string, password to use or NULL pointer (no password)
    db -- string, database to use or NULL (no DB selected)
    port -- integer, TCP/IP port to connect to or default MySQL port
    unix_socket -- string, location of unix_socket to use or use TCP
    client_flags -- integer, flags to use or 0 (see MySQL docs)
    conv -- conversion dictionary, see MySQLdb.converters
    connect_time -- number of seconds to wait before the connection
            attempt fails.
    compress -- if set, compression is enabled
    init_command -- command which is run once the connection is created
    read_default_file -- see the MySQL documentation for mysql_options()
    read_default_group -- see the MySQL documentation for mysql_options()
    cursorclass -- class object, used to create cursors or cursors.Cursor.
            This parameter MUST be specified as a keyword parameter.

    Returns a Connection object.

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
        self._transactional = self._db.server_capabilities & CLIENT.TRANSACTIONS

    def __del__(self):
        if hasattr(self, '_db'): self.close()
        
    def close(self):
        """Close the connection. No further activity possible."""
        self._db.close()

    def begin(self):
        """Explicitly begin a transaction. Non-standard."""
        self._db.query("BEGIN")
        
    def commit(self):
        """Commit the current transaction."""
        if self._transactional:
            self._db.query("COMMIT")
            
    def rollback(self):
        """Rollback the current transaction."""
        if self._transactional:
            self._db.query("ROLLBACK")
        else:
            raise NotSupportedError, "Not supported by server"
            
    def cursor(self, cursorclass=None):
        
        """Create a cursor on which queries may be performed. The
        optional cursorclass parameter is used to create the
        Cursor. By default, self.cursorclass=cursors.Cursor is
        used."""

        return (cursorclass or self.cursorclass)(self)

    # Non-portable MySQL-specific stuff
    # Methods not included on purpose (use Cursors instead):
    #     query, store_result, use_result

    def affected_rows(self): return self._db.affected_rows()
    def dump_debug_info(self): return self._db.dump_debug_info()
    def escape_string(self, s): return self._db.escape_string(s)
    def get_host_info(self): return self._db.get_host_info()
    def get_proto_info(self): return self._db.get_proto_info()
    def get_server_info(self): return self._db.get_server_info()
    def info(self): return self._db.info()
    def kill(self, p): return self._db.kill(p)
    def field_count(self): return self._db.field_count()
    num_fields = field_count # used prior to MySQL-3.22.24
    def ping(self): return self._db.ping()
    def row_tell(self): return self._db.row_tell()
    def select_db(self, db): return self._db.select_db(db)
    def shutdown(self): return self._db.shutdown()
    def stat(self): return self._db.stat()
    def string_literal(self, s): return self._db.string_literal(s)
    def thread_id(self): return self._db.thread_id()

    def _try_feature(self, feature, *args, **kwargs):
        try:
            return apply(getattr(self._db, feature), args, kwargs)
        except AttributeError:
            raise NotSupportedError, "not supported by MySQL library"
    def character_set_name(self):
        return self._try_feature('character_set_name')
    def change_user(self, *args, **kwargs):
        return apply(self._try_feature, ('change_user',)+args, kwargs)
