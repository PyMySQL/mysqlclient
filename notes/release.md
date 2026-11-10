# Release procedure

The examples below release **2.3.1** after **2.3.0**. Replace the version
numbers and release date as needed. Run commands from the repository root.

Ensure the PyPI Trusted Publisher for `mysqlclient` is configured with
repository `PyMySQL/mysqlclient`, workflow `windows.yaml`, and no required
environment name.

## 1. Update the release notes

Review the changes since the previous release:

```sh
git log v2.3.0..HEAD --oneline
git diff v2.3.0..HEAD --stat
```

Add a `What's new in 2.3.1` section at the top of
[HISTORY.rst](../HISTORY.rst), with `Release: YYYY-MM-DD` set to the release
date. Document changes, fixes, and deprecations that affect users.

## 2. Update the version and create a release PR

Update both version fields in
[src/MySQLdb/release.py](../src/MySQLdb/release.py):

```python
__version__ = "2.3.1"
version_info = (2, 3, 1, "final", 0)
```

Format the source and run the checks:

```sh
ruff format src/
ruff check src/
git diff --check
```

Review the diff, commit it as `release v2.3.1`, and open a PR targeting
`main` in `PyMySQL/mysqlclient`.

## 3. Verify CI for the release commit

Once the PR checks pass, merge it into `main`. Verify that all of the
following workflows pass for the merged commit:

- `Lint`
- `Test`, including MySQL, MariaDB, and Django tests
- `Build windows wheels`

To run the tests locally, install the package and the dependencies in
`requirements.txt`, prepare the database, and run the command used by the
[test workflow](../.github/workflows/tests.yaml). Adjust `TESTDB` to use
the configuration for your database:

```sh
TESTDB=actions.cnf pytest --cov=MySQLdb tests
```

Verify that the [Windows workflow](../.github/workflows/windows.yaml)
produces both `win-wheels-AMD64` and `win-wheels-ARM64` artifacts. The AMD64
artifact also contains the source distribution (sdist).

Record the release commit SHA.

## 4. Create and push the release tag

Replace `RELEASE_SHA` with the commit SHA verified in step 3. Fetch the
commit, create a lightweight tag, and push it:

```sh
git fetch upstream main --tags
git tag v2.3.1 RELEASE_SHA
git push upstream refs/tags/v2.3.1
```

Pushing the new `v*` tag starts a build of the tagged commit. Once both
Windows builds succeed, the `Publish to PyPI` job combines their artifacts
and publishes the wheels and sdist using Trusted Publishing.
Publishing is restricted to push events that create a new `v*` tag.

## 5. Verify publication and create the GitHub Release

Check the tag-triggered `Build windows wheels` workflow and confirm that
both builds and the `Publish to PyPI` job succeed. Then create the GitHub
Release:

```sh
gh release create v2.3.1 -R PyMySQL/mysqlclient \
  --verify-tag --title v2.3.1 \
  --generate-notes --notes-start-tag v2.3.0
```

## 6. Verify the published release

Check that PyPI lists the sdist and wheels for both architectures. Install
`mysqlclient==2.3.1` in a fresh environment and verify the import and version:

```sh
python -c 'import MySQLdb; print(MySQLdb.version_info)'
```

The expected output is `(2, 3, 1, 'final', 0)`.
