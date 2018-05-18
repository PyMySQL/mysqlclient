import os, sys
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    # Probably running Python 3.x
    from configparser import ConfigParser as SafeConfigParser

# This dequote() business is required for some older versions
# of mysql_config

def dequote(s):
    if not s:
        raise Exception("Wrong MySQL configuration: maybe https://bugs.mysql.com/bug.php?id=86971 ?")
    if s[0] in "\"'" and s[0] == s[-1]:
        s = s[1:-1]
    return s

def mysql_config(what):
    from os import popen

    f = popen("%s --%s" % (mysql_config.path, what))
    data = f.read().strip().split()
    ret = f.close()
    if ret:
        if ret/256:
            data = []
        if ret/256 > 1:
            raise EnvironmentError("%s not found" % (mysql_config.path,))
    return data
mysql_config.path = "mysql_config"

def get_config():
    from setup_common import get_metadata_and_options, enabled, create_release_file

    metadata, options = get_metadata_and_options()

    if 'mysql_config' in options:
        mysql_config.path = options['mysql_config']

    extra_objects = []
    static = enabled(options, 'static')

    # allow a command-line option to override the base config file to permit
    # a static build to be created via requirements.txt
    #
    if '--static' in sys.argv:
        static = True
        sys.argv.remove('--static')

    if enabled(options, 'embedded'):
        libs = mysql_config("libmysqld-libs")
    elif enabled(options, 'threadsafe'):
        libs = mysql_config("libs_r")
        if not libs:
            libs = mysql_config("libs")
    else:
        libs = mysql_config("libs")

    library_dirs = [dequote(i[2:]) for i in libs if i.startswith('-L')]
    libraries = [dequote(i[2:]) for i in libs if i.startswith('-l')]
    extra_link_args = [x for x in libs if not x.startswith(('-l', '-L'))]

    removable_compile_args = ('-I', '-L', '-l')
    extra_compile_args = [i.replace("%", "%%") for i in mysql_config("cflags")
                          if i[:2] not in removable_compile_args]

    # Copy the arch flags for linking as well
    for i in range(len(extra_compile_args)):
        if extra_compile_args[i] == '-arch':
            extra_link_args += ['-arch', extra_compile_args[i + 1]]

    include_dirs = [dequote(i[2:])
                    for i in mysql_config('include') if i.startswith('-I')]


    # properly handle mysql client libraries that are not called libmysqlclient
    client = None
    CLIENT_LIST = ['mysqlclient', 'mysqlclient_r', 'mysqld',
                   'perconaserverclient', 'perconaserverclient_r']
    for c in CLIENT_LIST:
        if c in libraries:
            client = c
            break

    if static:
        extra_objects.append(os.path.join(library_dirs[0], 'lib%s.a' % client))
        if client in libraries:
            libraries.remove(client)

    name = "mysqlclient"
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
        extra_link_args = extra_link_args,
        include_dirs = include_dirs,
        extra_objects = extra_objects,
        define_macros = define_macros,
        )

    # newer versions of gcc require libstdc++ if doing a static build
    if static:
        ext_options['language'] = 'c++'

    return metadata, ext_options

if __name__ == "__main__":
    sys.stderr.write("""You shouldn't be running this directly; it is used by setup.py.""")
