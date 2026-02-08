#!/usr/bin/env python
import os
import subprocess
import sys

import setuptools
from configparser import ConfigParser


release_info = {}
with open("src/MySQLdb/release.py", encoding="utf-8") as f:
    exec(f.read(), None, release_info)


def find_package_name():
    """Get available pkg-config package name"""
    # Ubuntu uses mariadb.pc, but CentOS uses libmariadb.pc
    packages = ["mysqlclient", "mariadb", "libmariadb", "perconaserverclient"]
    for pkg in packages:
        try:
            cmd = f"pkg-config --exists {pkg}"
            print(f"Trying {cmd}")
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as err:
            print(err)
        else:
            return pkg
    raise Exception(
        "Can not find valid pkg-config name.\n"
        "Specify MYSQLCLIENT_CFLAGS and MYSQLCLIENT_LDFLAGS env vars manually"
    )


def get_config_posix(options=None):
    # allow a command-line option to override the base config file to permit
    # a static build to be created via requirements.txt
    # TODO: find a better way for
    static = False
    if "--static" in sys.argv:
        static = True
        sys.argv.remove("--static")

    ldflags = os.environ.get("MYSQLCLIENT_LDFLAGS")
    cflags = os.environ.get("MYSQLCLIENT_CFLAGS")

    pkg_name = None
    static_opt = " --static" if static else ""
    if not (cflags and ldflags):
        pkg_name = find_package_name()
    if not cflags:
        cflags = subprocess.check_output(
            f"pkg-config{static_opt} --cflags {pkg_name}", encoding="utf-8", shell=True
        )
    if not ldflags:
        ldflags = subprocess.check_output(
            f"pkg-config{static_opt} --libs {pkg_name}", encoding="utf-8", shell=True
        )

    cflags = cflags.split()
    for f in cflags:
        if f.startswith("-std="):
            break
    else:
        cflags += ["-std=c99"]

    ldflags = ldflags.split()

    define_macros = [
        ("version_info", release_info["version_info"]),
        ("__version__", release_info["__version__"]),
    ]

    ext_options = dict(
        extra_compile_args=cflags,
        extra_link_args=ldflags,
        define_macros=define_macros,
    )
    # newer versions of gcc require libstdc++ if doing a static build
    if static:
        ext_options["language"] = "c++"

    return ext_options


def get_config_win32(options):
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
        os.path.join(connector, "include", "mysql"),
        os.path.join(connector, "include"),
    ]

    extra_link_args = ["/MANIFEST"]

    define_macros = [
        ("version_info", release_info["version_info"]),
        ("__version__", release_info["__version__"]),
    ]

    ext_options = dict(
        library_dirs=library_dirs,
        libraries=libraries,
        extra_link_args=extra_link_args,
        include_dirs=include_dirs,
        extra_objects=extra_objects,
        define_macros=define_macros,
    )
    return ext_options


def enabled(options, option):
    value = options[option]
    s = value.lower()
    if s in ("yes", "true", "1", "y"):
        return True
    elif s in ("no", "false", "0", "n"):
        return False
    else:
        raise ValueError(f"Unknown value {value} for option {option}")


def get_options():
    config = ConfigParser()
    config.read(["site.cfg"])
    options = dict(config.items("options"))
    options["static"] = enabled(options, "static")
    return options


if sys.platform == "win32":
    ext_options = get_config_win32(get_options())
else:
    ext_options = get_config_posix(get_options())

print("# Options for building extension module:")
for k, v in ext_options.items():
    print(f"  {k}: {v}")

ext_modules = [
    setuptools.Extension(
        "MySQLdb._mysql",
        sources=["src/MySQLdb/_mysql.c"],
        **ext_options,
    )
]
setuptools.setup(ext_modules=ext_modules)
