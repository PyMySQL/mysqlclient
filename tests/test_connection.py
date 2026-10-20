import queue
import threading
import time

import pytest
from configdb import connection_factory, connection_kwargs

from MySQLdb.connections import Connection
from MySQLdb._exceptions import ProgrammingError
from MySQLdb.constants import CLIENT


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

    with MultiConnection(
        **connection_kwargs({"executemany_fallback": "loop"})
    ) as conn:
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


def _free_results_in_other_thread(run_owner):
    """Run ``run_owner(hand_off)`` in this thread; every result it passes to
    ``hand_off`` is deallocated in a second thread, as the cyclic GC can do."""
    handoff = queue.Queue()
    stop = threading.Event()

    def free_results():
        while not (stop.is_set() and handoff.empty()):
            try:
                result = handoff.get(timeout=0.05)
            except queue.Empty:
                continue
            del result

    thread = threading.Thread(target=free_results)
    thread.start()
    try:
        run_owner(handoff.put)
    finally:
        stop.set()
        thread.join()


def test_result_dealloc_in_other_thread_does_not_fail_owner(conn):
    """Deallocating a result in another thread must not make the connection's
    own thread fail with "already in use" while it keeps running Python."""

    def run_owner(hand_off):
        for i in range(200):
            conn.query(f"SELECT {i}")
            result = conn.store_result()
            assert result.fetch_row() == ((i,),)
            hand_off(result)
            del result
            # Keep the GIL busy, as an application does between queries.
            end = time.perf_counter() + 0.001
            while time.perf_counter() < end:
                pass

    _free_results_in_other_thread(run_owner)


def test_result_dealloc_waits_for_owner_query(conn):
    """A result deallocated in another thread while the owner is inside a
    query waits for it, and the owner's queries are unaffected."""

    def run_owner(hand_off):
        for i in range(30):
            conn.query(f"SELECT SLEEP(0.02), {i}")
            result = conn.store_result()
            assert result.fetch_row() == ((0, i),)
            hand_off(result)
            del result

    _free_results_in_other_thread(run_owner)
