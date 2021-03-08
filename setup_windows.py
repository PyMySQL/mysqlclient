import os
import sys


def get_config():
    from setup_common import get_metadata_and_options, create_release_file

    metadata, options = get_metadata_and_options()

    client = "mariadbclient"
    connector = os.environ.get("MYSQLCLIENT_CONNECTOR", options.get("connector"))
    if not connector:
        connector = os.path.join(
            os.environ["ProgramFiles"], "MariaDB", "MariaDB Connector C"
        )

    extra_objects = []

    library_dirs = [
        os.path.join(connector, "lib", "mariadb"),
        os.path.join(connector, "lib"),
    ]
    libraries = [
        "kernel32",
        "advapi32",
        "wsock32",
        "shlwapi",
        "Ws2_32",
        "crypt32",
        "secur32",
        "bcrypt",
        client,
    ]
    include_dirs = [
        os.path.join(connector, "include", "mariadb"),
        os.path.join(connector, "include"),
    ]

    extra_link_args = ["/MANIFEST"]

    name = "mysqlclient"
    metadata["name"] = name

    define_macros = [
        ("version_info", metadata["version_info"]),
        ("__version__", metadata["version"]),
    ]
    create_release_file(metadata)
    del metadata["version_info"]
    ext_options = dict(
        library_dirs=library_dirs,
        libraries=libraries,
        extra_link_args=extra_link_args,
        include_dirs=include_dirs,
        extra_objects=extra_objects,
        define_macros=define_macros,
    )
    return metadata, ext_options


if __name__ == "__main__":
    sys.stderr.write(
        """You shouldn't be running this directly; it is used by setup.py."""
    )
