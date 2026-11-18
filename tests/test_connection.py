import enum
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from configdb import connection_factory, connection_kwargs

from MySQLdb._exceptions import ProgrammingError
from MySQLdb.connections import Connection
from MySQLdb.constants import CLIENT, FIELD_TYPE


@pytest.fixture
def conn():
    connection = connection_factory()
    try:
        yield connection
    finally:
        connection.close()


@pytest.mark.parametrize("sql_mode", ["", "NO_BACKSLASH_ESCAPES"])
def test_literal_str_enum(conn, sql_mode):
    class Foo(str, enum.Enum):
        BAR = "BAR"
        BAZ = "BAZ"

    conn.set_sql_mode(sql_mode)
    assert conn.literal(Foo.BAR) == b"'BAR'"
    assert conn.literal((Foo.BAR, Foo.BAZ)) == b"('BAR','BAZ')"
    cursor = conn.cursor()
    cursor.execute("SELECT %s", (Foo.BAR,))
    assert cursor.fetchone() == ("BAR",)


@pytest.mark.parametrize("value", ["BAR", b"BAR"])
@pytest.mark.parametrize("binary_prefix", [False, True])
def test_literal_string_subclass(value, binary_prefix):
    class Subclass(type(value)):
        pass

    with connection_factory(binary_prefix=binary_prefix) as conn:
        assert conn.literal(Subclass(value)) == conn.literal(value)


@pytest.mark.parametrize("binary_prefix", [False, True])
def test_literal_bytearray_subclass(binary_prefix):
    class Subclass(bytearray):
        pass

    data = b"A'\x00\\B"
    value = Subclass(data)
    with connection_factory(binary_prefix=binary_prefix) as conn:
        assert conn.literal(value) == conn.literal(data)
        cursor = conn.cursor()
        cursor.execute("SELECT %s", (value,))
        expected = data if binary_prefix else data.decode(conn.encoding)
        assert cursor.fetchone() == (expected,)


@pytest.mark.parametrize("container_type", [tuple, list, set, frozenset])
def test_literal_container_subclass_converter(conn, container_type):
    class Subclass(container_type):
        pass

    conn.encoders[Subclass] = lambda value, mapping: b"'custom'"
    cursor = conn.cursor()
    cursor.execute("SELECT %s", (Subclass(["BAR"]),))
    assert cursor.fetchone() == ("custom",)


@pytest.mark.parametrize("set_type", [set, frozenset])
@pytest.mark.parametrize("sql_mode", ["", "NO_BACKSLASH_ESCAPES"])
@pytest.mark.parametrize("charset", ["utf8mb4", "latin1"])
def test_literal_set_escaping(set_type, sql_mode, charset):
    value = "é' OR 1=1 -- \\"
    with connection_factory(charset=charset, sql_mode=sql_mode) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT %s", (set_type([value]),))
        assert cursor.fetchone() == (value,)
        with pytest.raises(TypeError, match="set elements must be strings"):
            conn.literal(set_type([1]))


def test_multi_statements_default_true(conn):
    cursor = conn.cursor()

    cursor.execute("select 17; select 2")
    assert conn.more_results() is True
    rows = cursor.fetchall()
    assert rows == ((17,),)
    assert cursor.nextset() == 1
    assert conn.more_results() is False


def test_multi_statements_false():
    conn = connection_factory(multi_statements=False)
    try:
        cursor = conn.cursor()
        assert not conn.client_flag & CLIENT.MULTI_STATEMENTS

        with pytest.raises(ProgrammingError):
            cursor.execute("select 17; select 2")

        cursor.execute("select 17")
        rows = cursor.fetchall()
        assert rows == ((17,),)
    finally:
        conn.close()


def test_executemany_fallback_option():
    with connection_factory() as conn:
        assert conn.executemany_fallback == "loop"

    with connection_factory(executemany_fallback="multi") as conn:
        assert conn.executemany_fallback == "multi"

    with pytest.raises(ValueError, match="executemany_fallback"):
        connection_factory(executemany_fallback="invalid")


def test_executemany_fallback_connection_subclass_default():
    class MultiConnection(Connection):
        executemany_fallback = "multi"

    with MultiConnection(**connection_kwargs({})) as conn:
        assert conn.executemany_fallback == "multi"

    with MultiConnection(**connection_kwargs({"executemany_fallback": "loop"})) as conn:
        assert conn.executemany_fallback == "loop"


def test_ping_false_warns(conn):
    with pytest.warns(DeprecationWarning, match="reconnect parameter"):
        conn.ping(False)


def test_connection_concurrent_use_raises(conn):
    """While a slow query holds the connection lock, any other access from
    a second thread must raise ProgrammingError immediately (not block)."""
    thread_error = None
    done = threading.Event()

    def run_slow_query():
        nonlocal thread_error
        try:
            conn.query("SELECT SLEEP(0.5)")
            result = conn.store_result()
            result.fetch_row()
        except Exception as exc:  # pragma: no cover
            thread_error = exc
        finally:
            done.set()

    thread = threading.Thread(target=run_slow_query)
    thread.start()

    # Give the background thread time to acquire the lock and enter SLEEP.
    time.sleep(0.1)

    start = time.monotonic()
    with pytest.raises(ProgrammingError, match="already in use"):
        conn.thread_id()
    # Should fail immediately, not wait for the SLEEP to finish.
    assert time.monotonic() - start < 0.1

    done.wait()
    thread.join()
    assert thread_error is None


@pytest.mark.parametrize("use", [False, True])
def test_result_rejects_reinitialization(conn, use):
    conn.query("SELECT 1 UNION ALL SELECT 2 ORDER BY 1")
    result = conn.use_result() if use else conn.store_result()
    with pytest.raises(ProgrammingError, match="already initialized"):
        result.__init__(conn, not use)

    assert result.fetch_row() == ((1,),)
    del result  # Leave the second row for cleanup.
    conn.query("SELECT 3")
    assert conn.store_result().fetch_row() == ((3,),)


def test_stored_result_dealloc_while_connection_locked(conn):
    stored = []

    def store_result():
        conn.query("SELECT 1")
        stored.append(conn.store_result())

    with ThreadPoolExecutor(max_workers=1) as executor:
        # On free-threaded CPython, drop the last reference on its owning thread.
        executor.submit(store_result).result()

        def convert(value):
            # fetch_row holds the connection lock while calling this converter.
            executor.submit(stored.clear).result(timeout=5)
            return int(value)

        conn.converter[FIELD_TYPE.NEWDECIMAL] = convert
        conn.query("SELECT CAST(2 AS DECIMAL(1,0))")
        assert conn.use_result().fetch_row() == ((2,),)
        assert not stored


def test_result_concurrent_use_raises(conn):
    """While fetch_row holds the connection lock streaming a slow result,
    any other access from a second thread must raise ProgrammingError immediately."""
    conn.query(
        "SELECT 1 FROM information_schema.tables a "
        "CROSS JOIN information_schema.tables b LIMIT 20000"
    )
    result = conn.use_result()

    thread_error = None
    done = threading.Event()
    started = threading.Event()

    def fetch_all_rows():
        nonlocal thread_error
        try:
            started.set()
            rows = result.fetch_row(maxrows=0)
            assert rows
        except Exception as exc:  # pragma: no cover
            thread_error = exc
        finally:
            done.set()

    thread = threading.Thread(target=fetch_all_rows)
    thread.start()

    assert started.wait(timeout=1.0)

    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        try:
            conn.thread_id()
        except ProgrammingError as exc:
            assert "already in use" in str(exc)
            break
        time.sleep(0.01)
    else:  # pragma: no cover
        pytest.fail("expected ProgrammingError while result.fetch_row() is running")

    done.wait()
    thread.join()
    assert thread_error is None
