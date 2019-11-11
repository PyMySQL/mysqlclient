import os
import sys
from distutils.msvccompiler import get_build_version


def get_config():
    from setup_common import get_metadata_and_options, enabled

    metadata, options = get_metadata_and_options()

    connector = options["connector"]

    extra_objects = []

    if enabled(options, 'embedded'):
        client = "mariadbd"
    else:
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

    name = "tiledb-sql"
    metadata['name'] = name

    ext_options = dict(
        library_dirs = library_dirs,
        libraries = libraries,
        extra_compile_args = extra_compile_args,
        extra_link_args = extra_link_args,
        include_dirs = include_dirs,
        extra_objects = extra_objects,
    )
    return metadata, ext_options


if __name__ == "__main__":
    sys.stderr.write(
        """You shouldn't be running this directly; it is used by setup.py."""
    )
