## Checks before committing

Run commands from the repository root. Format and lint the source before
committing:

```sh
ruff format src/
ruff check src/
git diff --check
```

## Running the mysqlclient test suite

The CI configuration is in [.github/workflows/tests.yaml](.github/workflows/tests.yaml).
The package is in `src/MySQLdb/` and the tests are in `tests/`.

1. Install a C compiler, Python development headers, `pkg-config`, and MySQL or
   MariaDB client development libraries, as described in [README.md](README.md).
   A running MySQL or MariaDB server is also required for database tests.

2. In a Python virtual environment, install the package and test dependencies:

   ```sh
   python -m pip install -v .
   python -m pip install -r requirements.txt
   python -m pip install "SQLAlchemy>=2,<3"
   ```

   SQLAlchemy is needed to run `tests/test_sqlalchemy.py`; those tests are
   skipped if it is not installed.

3. Start the database server using the service manager available in your
   environment. In containers without a service manager, run `mysqld` in a
   separate, long-lived terminal with an initialized data directory and writable
   socket and PID file locations.

   Create a dedicated test database using an administrator connection, for example:

   ```sh
   mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS mysqldb_test"
   ```

   Ensure the test user can create, alter, and drop tables, and create, execute,
   and drop stored procedures in that database.
   `tests/actions.cnf` uses `127.0.0.1:3306`, user `root`, password `root`, and
   database `mysqldb_test`. For different credentials, create a separate MySQL
   option file with a `[MySQLdb-tests]` group, using `tests/actions.cnf` as a
   template.

4. Run the same pytest command as CI:

   ```sh
   TESTDB=actions.cnf pytest --cov=MySQLdb tests
   ```

   `TESTDB` selects a filename under `tests/` or an absolute path to an option
   file. Without it, `tests/default.cnf` is used. The tests create and drop
   tables, so use the dedicated test database.

CI also runs the Django test suite in a separate job. Refer to
`.github/workflows/tests.yaml` for its dependencies, database setup, and
`test_mysql_executemany_multi` settings.

## Releases

Follow [notes/release.md](notes/release.md) for version updates, release CI,
tagging, and publication.
