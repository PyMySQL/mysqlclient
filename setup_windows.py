import os, sys

def get_config():
    from setup_common import get_metadata_and_options, enabled, create_release_file

    metadata, options = get_metadata_and_options()

    connector = options["connector"]

    extra_objects = []

    if enabled(options, 'embedded'):
        client = "mysqld"
    else:
        client = "mysqlclient"

    library_dirs = [ os.path.join(connector, r'lib\opt') ]
    libraries = [ 'kernel32', 'advapi32', 'wsock32', client ]
    include_dirs = [ os.path.join(connector, r'include') ]
    extra_compile_args = [ '/Zl' ]
    
    name = "MySQL-python"
    if enabled(options, 'embedded'):
        name = name + "-embedded"
    metadata['name'] = name
    
    define_macros = [
        ('version_info', metadata['version_info']),
        ('__version__', metadata['version']),
        ]
    create_release_file(metadata)
    del metadata['version_info']
    ext_options = dict(
        name = "_mysql",
        library_dirs = library_dirs,
        libraries = libraries,
        extra_compile_args = extra_compile_args,
        include_dirs = include_dirs,
        extra_objects = extra_objects,
        define_macros = define_macros,
        )
    return metadata, ext_options

if __name__ == "__main__":
    sys.stderr.write("""You shouldn't be running this directly; it is used by setup.py.""")
    
