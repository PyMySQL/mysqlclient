import os
import sys
from distutils.msvccompiler import get_build_version


def get_config():
    from setup_common import get_metadata_and_options, create_release_file

    metadata, options = get_metadata_and_options()

    connector = options["connector"]

    extra_objects = []

    # client = "mysqlclient"
    client = "mariadbclient"

    vcversion = int(get_build_version())
    if client == "mariadbclient":
        library_dirs = [os.path.join(connector, "lib", "mariadb")]
        libraries = ["kernel32", "advapi32", "wsock32", "shlwapi", "Ws2_32", client]
        include_dirs = [os.path.join(connector, "include", "mariadb")]
    else:
        library_dirs = [
            os.path.join(connector, r"lib\vs%d" % vcversion),
            os.path.join(connector, "lib"),
        ]
        libraries = ["kernel32", "advapi32", "wsock32", client]
        include_dirs = [os.path.join(connector, r"include")]

    extra_compile_args = ["/Zl", "/D_CRT_SECURE_NO_WARNINGS"]
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
        extra_compile_args=extra_compile_args,
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
