def manage_addZMySQLConnection(self, id, title,
                                connection_string,
                                check=None, REQUEST=None):
    """Add a MySQL connection to a folder.

    Arguments:

        REQUEST -- The current request

        title -- The title of the ZMySQLDA Connection (string)

        id -- The id of the ZMySQLDA Connection (string)

        connection_string -- The connection string is of the form:

        '[*lock] [+/-][database][@host[:port]] [user [password [unix_socket]]]'

        or typically:

                'database user password'

        to use a MySQL server on localhost via the standard UNIX
        socket.  Only specify host if the server is on a remote
        system. You can use a non-standard port, if necessary. If the
        UNIX socket is in a non-standard location, you can specify the
        full path to it after the password. Hint: To use a
        non-standard port on the local system, use 127.0.0.1 for the
        host instead of localhost.
        
        Either a database or a host or both must be specified.     

        A '-' in front of the database tells ZMySQLDA to not use
        Zope's Transaction Manager, even if the server supports
        transactions. A '+' in front of the database tells ZMySQLDA
        that it must use transactions; an exception will be raised if
        they are not supported by the server. If neither '-' or '+'
        are present, then transactions will be enabled if the server
        supports them.  If you are using non-transaction safe tables
        (TSTs) on a server that supports TSTs, use '-'. If you require
        transactions, use '+'. If you aren't sure, don't use either.

        *lock at the begining of the connection string means to
        psuedo-transactional. When the transaction begins, it will
        acquire a lock on the server named lock (i.e. MYLOCK). When
        the transaction commits, the lock will be released. If the
        transaction is aborted and restarted, which can happen due to
        a ConflictError, you'll get an error in the logs, and
        inconsistent data. In this respect, it's equivalent to
        transactions turned off.

        Transactions are highly recommended. Using a named lock in
        conjunctions with transactions is probably pointless.

        """

class Connection:
    """MySQL Connection Object"""

    __constructor__ = manage_addZMySQLConnection


