class DB:

    """This is the ZMySQLDA Database Connection Object."""

    def __init__(self,connection):
        """
            connection
               blah blah
        """
        
    def tables(self, rdb=0,
               _care=('TABLE', 'VIEW')):
        """Returns a list of tables in the current database."""

    def columns(self, table_name):
        """Returns a list of column descriptions for 'table_name'."""

    def query(self,query_string, max_rows=1000):
        """Execute 'query_string' and return at most 'max_rows'."""

    def _begin(self, *ignored):
        """Begin a transaction (when TM is enabled)."""
        
    def _finish(self, *ignored):
        """Commit a transaction (when TM is enabled)."""

    def _abort(self, *ignored):
        """Rollback a transaction (when TM is enabled)."""
