import threading
import time

import pytest

from MySQLdb._exceptions import ProgrammingError

from configdb import connection_factory


def test_multi_statements_default_true():
    conn = connection_factory()
    cursor = conn.cursor()

    cursor.execute("select 17; select 2")
    rows = cursor.fetchall()
    assert rows == ((17,),)


def test_multi_statements_false():
    conn = connection_factory(multi_statements=False)
    cursor = conn.cursor()

    with pytest.raises(ProgrammingError):
        cursor.execute("select 17; select 2")

    cursor.execute("select 17")
    rows = cursor.fetchall()
    assert rows == ((17,),)


def test_connection_concurrent_use_raises():
    """While a slow query holds the connection lock, any other access from
    a second thread must raise ProgrammingError immediately (not block)."""
    conn = connection_factory()
    try:
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
    finally:
        conn.close()


def test_result_concurrent_use_raises():
    """While fetch_row holds the connection lock streaming a slow result,
    any other access from a second thread must raise ProgrammingError immediately."""
    conn = connection_factory()
    try:
        conn.query("SELECT 1 UNION ALL SELECT SLEEP(0.5)")
        result = conn.use_result()

        thread_error = None
        done = threading.Event()

        def fetch_all_rows():
            nonlocal thread_error
            try:
                assert result.fetch_row(maxrows=0) == ((1,), (0,))
            except Exception as exc:  # pragma: no cover
                thread_error = exc
            finally:
                done.set()

        thread = threading.Thread(target=fetch_all_rows)
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
    finally:
        conn.close()
