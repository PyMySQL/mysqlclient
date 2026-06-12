import threading
import time

import pytest

from MySQLdb._exceptions import ProgrammingError

from configdb import connection_factory


@pytest.fixture
def conn():
    connection = connection_factory()
    try:
        yield connection
    finally:
        connection.close()


def test_multi_statements_default_true(conn):
    cursor = conn.cursor()

    cursor.execute("select 17; select 2")
    rows = cursor.fetchall()
    assert rows == ((17,),)


def test_multi_statements_false():
    conn = connection_factory(multi_statements=False)
    try:
        cursor = conn.cursor()

        with pytest.raises(ProgrammingError):
            cursor.execute("select 17; select 2")

        cursor.execute("select 17")
        rows = cursor.fetchall()
        assert rows == ((17,),)
    finally:
        conn.close()


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
