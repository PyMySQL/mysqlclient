"""Path-like connection options (#319)."""
import os
from pathlib import Path
from unittest import mock

import MySQLdb


def test_read_default_file_path_converted_via_fspath():
    path = Path("/tmp/does-not-need-to-exist.cnf")
    captured = {}

    def fake_c_init(self, *args, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("stop after c init kwargs captured")

    with mock.patch.object(MySQLdb._mysql.connection, "__init__", fake_c_init):
        with mock.patch.object(MySQLdb.connections.Connection, "_set_attributes"):
            try:
                MySQLdb.connections.Connection(read_default_file=path)
            except RuntimeError as exc:
                assert str(exc) == "stop after c init kwargs captured"

    assert captured["read_default_file"] == os.fspath(path)
    assert isinstance(captured["read_default_file"], str)
