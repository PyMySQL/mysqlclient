import pytest

from MySQLdb import _mysql
from MySQLdb.connections import Connection


def test_result_type():
    with pytest.raises(TypeError):
        _mysql.result(b"xyz")


@pytest.mark.parametrize("connection_type", [_mysql.connection, Connection])
@pytest.mark.parametrize("name", [5, None, b"closed", [], {}])
def test_connection_getattribute_non_string(connection_type, name):
    conn = connection_type.__new__(connection_type)
    with pytest.raises(TypeError):
        conn.__getattribute__(name)


@pytest.mark.parametrize("connection_type", [_mysql.connection, Connection])
@pytest.mark.parametrize("name", ["missing", "closed\x00suffix", "\ud800"])
def test_connection_getattribute_missing(connection_type, name):
    conn = connection_type.__new__(connection_type)
    with pytest.raises(AttributeError):
        conn.__getattribute__(name)


@pytest.mark.parametrize("connection_type", [_mysql.connection, Connection])
def test_connection_getattribute(connection_type):
    class AttributeName(str):
        pass

    conn = connection_type.__new__(connection_type)
    assert conn.closed == 1
    assert conn.__getattribute__(AttributeName("closed")) == 1
    assert conn.__class__ is connection_type
