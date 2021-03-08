import os
import sys
from distutils.msvccompiler import get_build_version


def get_default_connector(client):
    if client == "mariadbclient":
        return os.path.join(
            os.environ["ProgramFiles"], "MariaDB", "MariaDB Connector C"
        )
    elif client == "mysqlclient":
        return os.path.join(
            os.environ["ProgramFiles"], "MySQL", "MySQL Connector C 6.1"
        )
    else:
        raise ValueError("Unknown client library")


def find_library(client, connector=None):
    if not connector:
        connector = get_default_connector(client)
    paths = []
    if client == "mariadbclient":
        paths.append(os.path.join(connector, "lib", "mariadb", client + ".lib"))
        paths.append(os.path.join(connector, "lib", client + ".lib"))
    elif client == "mysqlclient":
        vcversion = int(get_build_version())
        paths.append(os.path.join(connector, "lib", "vs%d" % vcversion))
    else:
        raise ValueError("Unknown client library")
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def get_config():
    from setup_common import get_metadata_and_options, create_release_file

    metadata, options = get_metadata_and_options()

    client = os.environ.get("MYSQLCLIENT_CLIENT", options.get("client"))
    connector = os.environ.get("MYSQLCLIENT_CONNECTOR", options.get("connector"))

    if not client:
        for client in ("mariadbclient", "mysqlclient"):
            if find_library(client, connector):
                break
        else:
            raise RuntimeError("Couldn't find MySQL or MariaDB Connector")

    if not connector:
        connector = get_default_connector(client)

    extra_objects = []

    vcversion = int(get_build_version())
    if client == "mariadbclient":
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
    elif client == "mysqlclient":
        library_dirs = [
            os.path.join(connector, r"lib\vs%d" % vcversion),
            os.path.join(connector, "lib"),
        ]
        libraries = ["kernel32", "advapi32", "wsock32", client]
        include_dirs = [os.path.join(connector, r"include")]
    else:
        raise ValueError("Unknown client library")

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
