"""Connection reset integration tests (requires COM_RESET_CONNECTION)."""

from pathlib import Path

import pytest
from configdb import connection_factory, connection_kwargs

from MySQLdb import OperationalError, ProgrammingError, _mysql
from MySQLdb.constants import CR


def scalar(conn, sql):
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchone()[0]


def test_reset_session():
    with connection_factory(
        init_command="SET @reset_init = 1", sql_mode="ANSI_QUOTES"
    ) as conn:
        thread_id = conn.thread_id()
        database = scalar(conn, "SELECT DATABASE()")
        assert scalar(conn, "SELECT @reset_init") == 1
        conn.query("CREATE TEMPORARY TABLE reset_temporary (id INT)")
        assert scalar(conn, "SELECT GET_LOCK('mysqlclient_reset_test', 0)") == 1
        conn.messages.append((Warning, "old message"))

        assert conn.reset() is None
        assert conn.messages == []
        assert conn.thread_id() == thread_id
        assert scalar(conn, "SELECT DATABASE()") == database
        assert scalar(conn, "SELECT @reset_init") is None
        assert scalar(conn, "SELECT @@session.sql_mode = @@global.sql_mode") == 1
        assert scalar(conn, "SELECT IS_FREE_LOCK('mysqlclient_reset_test')") == 1
        with pytest.raises(ProgrammingError) as exc:
            conn.query("SELECT * FROM reset_temporary")
        assert exc.value.args[0] == 1146
        assert conn.reset() is None
        assert scalar(conn, "SELECT 42") == 42


def test_reset_rolls_back():
    with connection_factory() as conn:
        conn.query("DROP TABLE IF EXISTS reset_transaction")
        conn.query("CREATE TABLE reset_transaction (id INT) ENGINE=InnoDB")
        try:
            conn.query("INSERT INTO reset_transaction VALUES (1)")
            conn.commit()
            conn.query("INSERT INTO reset_transaction VALUES (2)")
            conn.reset()
            assert scalar(conn, "SELECT COUNT(*) FROM reset_transaction") == 1
            conn.autocommit(False)
            conn.query("INSERT INTO reset_transaction VALUES (3)")
            conn.commit()
            assert scalar(conn, "SELECT COUNT(*) FROM reset_transaction") == 2
        finally:
            conn.query("DROP TABLE reset_transaction")


@pytest.mark.parametrize("autocommit", [False, True, None])
def test_reset_autocommit(autocommit):
    with connection_factory(autocommit=autocommit) as conn:
        default = bool(scalar(conn, "SELECT @@global.autocommit"))
        conn.autocommit(not default)
        conn.reset()
        # Check cached status before another command can update it.
        cached = conn.get_autocommit()
        assert bool(scalar(conn, "SELECT @@session.autocommit")) is default
        if not default and "MariaDB" not in conn.get_server_info() and cached:
            pytest.xfail("MySQL reset reports autocommit ON with global autocommit OFF")
        assert cached is default
        conn.autocommit(not default)
        assert bool(scalar(conn, "SELECT @@session.autocommit")) is not default


@pytest.mark.parametrize(
    "charset, collation, value",
    [
        ("utf8mb4", "utf8mb4_bin", "雪😀'\\"),
        ("latin1", "latin1_bin", "€é'\\"),
        ("gbk", "gbk_bin", "中文'\\"),
    ],
)
@pytest.mark.parametrize("use_unicode", [False, True])
def test_reset_charset(charset, collation, value, use_unicode):
    with connection_factory(charset="utf8mb4", use_unicode=use_unicode) as conn:
        # Preserve the current charset, even when changed since connect().
        conn.set_character_set(charset, collation)
        encoding = conn.encoding
        for _ in range(2):
            assert conn.reset() is None
            assert conn.encoding == encoding
            assert conn.character_set_name() == charset
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT @@character_set_client, @@character_set_connection, "
                    "@@character_set_results, @@collation_connection"
                )
                client, connection, results, actual_collation = cursor.fetchone()
                expected_charset = charset if use_unicode else charset.encode()
                assert client == connection == results == expected_charset
                assert actual_collation != (
                    collation if use_unicode else collation.encode()
                )
                cursor.execute("SELECT %s", (value,))
                expected = value if use_unicode else value.encode(encoding)
                assert cursor.fetchone() == (expected,)


def test_reset_closed():
    conn = connection_factory()
    conn.close()
    for _ in range(2):
        with pytest.raises(OperationalError) as exc:
            conn.reset()
        assert exc.value.args[0] == CR.SERVER_GONE_ERROR


@pytest.mark.parametrize("reconnect", [False, True])
def test_reset_lost_connection_does_not_reconnect(reconnect):
    with connection_factory() as conn, connection_factory() as killer:
        if reconnect:
            with pytest.warns(DeprecationWarning):
                conn.ping(True)
        killer.query(f"KILL CONNECTION {conn.thread_id()}")
        for _ in range(2):
            with pytest.raises(OperationalError) as exc:
                conn.reset()
            assert exc.value.args[0] in (CR.SERVER_GONE_ERROR, CR.SERVER_LOST)


def test_reset_option_file_reconnect(tmp_path):
    if not _mysql.get_client_info().startswith("3."):
        pytest.skip("Connector/C reconnect option file setting")
    config = tmp_path / "reconnect.cnf"
    defaults = connection_kwargs({})["read_default_file"]
    config.write_text(Path(defaults).read_text() + "\n[MySQLdb-tests]\nreconnect=1\n")
    with (
        connection_factory(read_default_file=str(config)) as conn,
        connection_factory() as killer,
    ):
        assert conn.reset() is None
        killer.query(f"KILL CONNECTION {conn.thread_id()}")
        for _ in range(2):
            with pytest.raises(OperationalError) as exc:
                conn.reset()
            assert exc.value.args[0] in (CR.SERVER_GONE_ERROR, CR.SERVER_LOST)


def test_reset_pending_results():
    with connection_factory() as conn:
        conn.query("SELECT 1; SELECT 2")
        with pytest.raises(ProgrammingError, match="pending results"):
            conn.reset()
        assert conn.store_result().fetch_row() == ((1,),)
        with pytest.raises(ProgrammingError, match="pending results"):
            conn.reset()
        assert conn.next_result() == 0
        assert conn.store_result().fetch_row() == ((2,),)
        assert conn.next_result() == -1
        assert conn.reset() is None


def test_reset_streaming_result():
    with connection_factory() as conn:
        conn.query("SELECT 1 UNION ALL SELECT 2")
        result = conn.use_result()
        with pytest.raises(ProgrammingError, match="pending results"):
            conn.reset()
        assert result.fetch_row(0) == ((1,), (2,))
        del result
        assert conn.reset() is None


def test_reset_no_arguments():
    with connection_factory() as conn:
        with pytest.raises(TypeError):
            conn.reset(True)
        with pytest.raises(TypeError):
            conn.reset(reconnect=True)
