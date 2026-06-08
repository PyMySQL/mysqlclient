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


def _assert_thread_id_waits_while(conn, func, min_wait=0.15):
    error = None
    done = threading.Event()
    thread_id_done = threading.Event()
    results = {}

    def run():
        nonlocal error
        try:
            func()
        except Exception as exc:  # pragma: no cover - error checked below
            error = exc
        finally:
            done.set()

    def read_thread_id():
        try:
            results["thread_id"] = conn.thread_id()
        except Exception as exc:  # pragma: no cover - assertion checked below
            results["error"] = exc
        finally:
            thread_id_done.set()

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(0.05)
    assert not done.is_set()

    blocker = threading.Thread(target=read_thread_id)
    blocker.start()

    assert not thread_id_done.wait(min_wait)
    thread.join()
    blocker.join()
    assert error is None
    assert done.is_set()
    assert "error" not in results
    assert isinstance(results["thread_id"], int)


def test_connection_methods_are_serialized():
    conn = connection_factory()
    try:
        def run_query():
            conn.query("SELECT SLEEP(0.2)")
            result = conn.store_result()
            assert result.fetch_row() == ((0,),)

        _assert_thread_id_waits_while(conn, run_query)
    finally:
        conn.close()


def test_result_methods_share_connection_lock():
    conn = connection_factory()
    try:
        conn.query("SELECT 1 UNION ALL SELECT SLEEP(0.2)")
        result = conn.use_result()

        def fetch_all_rows():
            assert result.fetch_row(maxrows=0) == ((1,), (0,))

        _assert_thread_id_waits_while(conn, fetch_all_rows)
    finally:
        conn.close()
