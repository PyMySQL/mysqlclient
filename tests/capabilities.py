#!/usr/bin/env python -O
""" Script to test database capabilities and the DB-API interface
    for functionality and memory leaks.

    Adapted from a script by M-A Lemburg.

"""
from time import time
import unittest
from configdb import connection_factory


class DatabaseTest(unittest.TestCase):

    db_module = None
    connect_args = ()
    connect_kwargs = dict()
    create_table_extra = ""
    rows = 10
    debug = False

    def setUp(self):

        db = connection_factory(**self.connect_kwargs)
        self.connection = db
        self.cursor = db.cursor()
        self.BLOBUText = "".join([chr(i) for i in range(16384)])
        self.BLOBBinary = self.db_module.Binary(
            ("".join([chr(i) for i in range(256)] * 16)).encode("latin1")
        )

    leak_test = True

    def tearDown(self):
        if self.leak_test:
            import gc

            del self.cursor
            orphans = gc.collect()
            self.failIf(
                orphans, "%d orphaned objects found after deleting cursor" % orphans
            )

            del self.connection
            orphans = gc.collect()
            self.failIf(
                orphans, "%d orphaned objects found after deleting connection" % orphans
            )

    def table_exists(self, name):
        try:
            self.cursor.execute("select * from %s where 1=0" % name)
        except Exception:
            return False
        else:
            return True

    def quote_identifier(self, ident):
        return '"%s"' % ident

    def new_table_name(self):
        i = id(self.cursor)
        while True:
            name = self.quote_identifier("tb%08x" % i)
            if not self.table_exists(name):
                return name
            i = i + 1

    def create_table(self, columndefs):

        """Create a table using a list of column definitions given in
        columndefs.

        generator must be a function taking arguments (row_number,
        col_number) returning a suitable data object for insertion
        into the table.

        """
        self.table = self.new_table_name()
        self.cursor.execute(
            "CREATE TABLE %s (%s) %s"
            % (self.table, ",\n".join(columndefs), self.create_table_extra)
        )

    def check_data_integrity(self, columndefs, generator):
        # insert
        self.create_table(columndefs)
        insert_statement = "INSERT INTO %s VALUES (%s)" % (
            self.table,
            ",".join(["%s"] * len(columndefs)),
        )
        data = [
            [generator(i, j) for j in range(len(columndefs))] for i in range(self.rows)
        ]
        self.cursor.executemany(insert_statement, data)
        self.connection.commit()
        # verify
        self.cursor.execute("select * from %s" % self.table)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), self.rows)
        try:
            for i in range(self.rows):
                for j in range(len(columndefs)):
                    self.assertEqual(res[i][j], generator(i, j))
        finally:
            if not self.debug:
                self.cursor.execute("drop table %s" % (self.table))

    def test_transactions(self):
        columndefs = ("col1 INT", "col2 VARCHAR(255)")

        def generator(row, col):
            if col == 0:
                return row
            else:
                return ("%i" % (row % 10)) * 255

        self.create_table(columndefs)
        insert_statement = "INSERT INTO %s VALUES (%s)" % (
            self.table,
            ",".join(["%s"] * len(columndefs)),
        )
        data = [
            [generator(i, j) for j in range(len(columndefs))] for i in range(self.rows)
        ]
        self.cursor.executemany(insert_statement, data)
        # verify
        self.connection.commit()
        self.cursor.execute("select * from %s" % self.table)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), self.rows)
        for i in range(self.rows):
            for j in range(len(columndefs)):
                self.assertEqual(res[i][j], generator(i, j))
        delete_statement = "delete from %s where col1=%%s" % self.table
        self.cursor.execute(delete_statement, (0,))
        self.cursor.execute("select col1 from %s where col1=%s" % (self.table, 0))
        res = self.cursor.fetchall()
        self.assertFalse(res, "DELETE didn't work")
        self.connection.rollback()
        self.cursor.execute("select col1 from %s where col1=%s" % (self.table, 0))
        res = self.cursor.fetchall()
        self.assertTrue(len(res) == 1, "ROLLBACK didn't work")
        self.cursor.execute("drop table %s" % (self.table))

    def test_truncation(self):
        columndefs = ("col1 INT", "col2 VARCHAR(255)")

        def generator(row, col):
            if col == 0:
                return row
            else:
                return ("%i" % (row % 10)) * ((255 - self.rows // 2) + row)

        self.create_table(columndefs)
        insert_statement = "INSERT INTO %s VALUES (%s)" % (
            self.table,
            ",".join(["%s"] * len(columndefs)),
        )

        try:
            self.cursor.execute(insert_statement, (0, "0" * 256))
        except self.connection.DataError:
            pass
        else:
            self.fail(
                "Over-long column did not generate warnings/exception with single insert"  # noqa: E501
            )

        self.connection.rollback()

        try:
            for i in range(self.rows):
                data = []
                for j in range(len(columndefs)):
                    data.append(generator(i, j))
                self.cursor.execute(insert_statement, tuple(data))
        except self.connection.DataError:
            pass
        else:
            self.fail(
                "Over-long columns did not generate warnings/exception with execute()"  # noqa: E501
            )

        self.connection.rollback()

        try:
            data = [
                [generator(i, j) for j in range(len(columndefs))]
                for i in range(self.rows)
            ]
            self.cursor.executemany(insert_statement, data)
        except self.connection.DataError:
            pass
        else:
            self.fail(
                "Over-long columns did not generate warnings/exception with executemany()"  # noqa: E501
            )

        self.connection.rollback()
        self.cursor.execute("drop table %s" % (self.table))

    def test_CHAR(self):
        # Character data
        def generator(row, col):
            return ("%i" % ((row + col) % 10)) * 255

        self.check_data_integrity(("col1 char(255)", "col2 char(255)"), generator)

    def test_INT(self):
        # Number data
        def generator(row, col):
            return row * row

        self.check_data_integrity(("col1 INT",), generator)

    def test_DECIMAL(self):
        # DECIMAL
        from decimal import Decimal

        def generator(row, col):
            return Decimal("%d.%02d" % (row, col))

        self.check_data_integrity(("col1 DECIMAL(5,2)",), generator)

        val = Decimal("1.11111111111111119E-7")
        self.cursor.execute("SELECT %s", (val,))
        result = self.cursor.fetchone()[0]
        self.assertEqual(result, val)
        self.assertIsInstance(result, Decimal)

        self.cursor.execute("SELECT %s + %s", (Decimal("0.1"), Decimal("0.2")))
        result = self.cursor.fetchone()[0]
        self.assertEqual(result, Decimal("0.3"))
        self.assertIsInstance(result, Decimal)

    def test_DATE(self):
        ticks = time()

        def generator(row, col):
            return self.db_module.DateFromTicks(ticks + row * 86400 - col * 1313)

        self.check_data_integrity(("col1 DATE",), generator)

    def test_TIME(self):
        ticks = time()

        def generator(row, col):
            return self.db_module.TimeFromTicks(ticks + row * 86400 - col * 1313)

        self.check_data_integrity(("col1 TIME",), generator)

    def test_DATETIME(self):
        ticks = time()

        def generator(row, col):
            return self.db_module.TimestampFromTicks(ticks + row * 86400 - col * 1313)

        self.check_data_integrity(("col1 DATETIME",), generator)

    def test_TIMESTAMP(self):
        ticks = time()

        def generator(row, col):
            return self.db_module.TimestampFromTicks(ticks + row * 86400 - col * 1313)

        self.check_data_integrity(("col1 TIMESTAMP",), generator)

    def test_fractional_TIMESTAMP(self):
        ticks = time()

        def generator(row, col):
            return self.db_module.TimestampFromTicks(
                ticks + row * 86400 - col * 1313 + row * 0.7 * col / 3.0
            )

        self.check_data_integrity(("col1 TIMESTAMP",), generator)

    def test_LONG(self):
        def generator(row, col):
            if col == 0:
                return row
            else:
                return self.BLOBUText  # 'BLOB Text ' * 1024

        self.check_data_integrity(("col1 INT", "col2 LONG"), generator)

    def test_TEXT(self):
        def generator(row, col):
            return self.BLOBUText  # 'BLOB Text ' * 1024

        self.check_data_integrity(("col2 TEXT",), generator)

    def test_LONG_BYTE(self):
        def generator(row, col):
            if col == 0:
                return row
            else:
                return self.BLOBBinary  # 'BLOB\000Binary ' * 1024

        self.check_data_integrity(("col1 INT", "col2 LONG BYTE"), generator)

    def test_BLOB(self):
        def generator(row, col):
            if col == 0:
                return row
            else:
                return self.BLOBBinary  # 'BLOB\000Binary ' * 1024

        self.check_data_integrity(("col1 INT", "col2 BLOB"), generator)

    def test_DOUBLE(self):
        for val in (18014398509481982.0, 0.1):
            self.cursor.execute("SELECT %s", (val,))
            result = self.cursor.fetchone()[0]
            self.assertEqual(result, val)
            self.assertIsInstance(result, float)
