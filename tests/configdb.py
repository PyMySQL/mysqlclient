"""Configure database connection for tests."""

from os import environ, path

tests_path = path.dirname(__file__)
conf_file = environ.get("TESTDB", "default.cnf")
conf_path = path.join(tests_path, conf_file)
connect_kwargs = dict(read_default_file = conf_path,read_default_group = "tiledb-sql-tests",)


def connection_kwargs(kwargs):
    db_kwargs = connect_kwargs.copy()
    db_kwargs.update(kwargs)
    return db_kwargs


def connection_factory(**kwargs):
    import tiledb.sql

    db_kwargs = connection_kwargs(kwargs)
    db = tiledb.sql.connect(**db_kwargs)
    return db
