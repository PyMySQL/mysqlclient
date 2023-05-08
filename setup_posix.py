import os
import sys
import subprocess


def find_package_name():
    """Get available pkg-config package name"""
    packages = ["mysqlclient", "mariadb"]
    for pkg in packages:
        try:
            cmd = f"pkg-config --exists {pkg}"
            print(f"Trying {cmd}")
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as err:
            print(err)
        else:
            return pkg
    raise Exception("Can not find valid pkg-config")


def get_config():
    from setup_common import get_metadata_and_options, enabled, create_release_file
    metadata, options = get_metadata_and_options()

    static = enabled(options, "static")
    # allow a command-line option to override the base config file to permit
    # a static build to be created via requirements.txt
    #
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
        cflags = subprocess.check_output(f"pkg-config{static_opt} --cflags {pkg_name}", encoding="utf-8", shell=True)
    if not ldflags:
        ldflags = subprocess.check_output(f"pkg-config{static_opt} --libs {pkg_name}", encoding="utf-8", shell=True)

    cflags = cflags.split()
    for f in cflags:
        if f.startswith("-std="):
            break
    else:
        cflags += ["-std=c99"]

    ldflags = ldflags.split()

    define_macros = [
        ("version_info", metadata["version_info"]),
        ("__version__", metadata["version"]),
    ]

    # print(f"{cflags = }")
    # print(f"{ldflags = }")
    # print(f"{define_macros = }")

    ext_options = dict(
        extra_compile_args=cflags,
        extra_link_args=ldflags,
        define_macros=define_macros,
    )
    # newer versions of gcc require libstdc++ if doing a static build
    if static:
        ext_options["language"] = "c++"

    print("Options for building extention module:")
    for k, v in ext_options.items():
        print(f"  {k}: {v}")

    create_release_file(metadata)
    del metadata["version_info"]

    return metadata, ext_options


if __name__ == "__main__":
    from pprint import pprint
    metadata, config = get_config()
    print("# Metadata")
    pprint(metadata, sort_dicts=False, compact=True)
    print("\n# Extention options")
    pprint(config, sort_dicts=False, compact=True)
