from ConfigParser import SafeConfigParser

def get_metadata_and_options():
    config = SafeConfigParser()
    config.read(['metadata.cfg', 'site.cfg'])

    metadata = dict(config.items('metadata'))
    options = dict(config.items('options'))

    metadata['py_modules'] = filter(None, metadata['py_modules'].split('\n'))
    metadata['classifiers'] = filter(None, metadata['classifiers'].split('\n'))

    return metadata, options

def enabled(options, option):
    value = options[option]
    s = value.lower()
    if s in ('yes','true','1','y'):
        return True
    elif s in ('no', 'false', '0', 'n'):
        return False
    else:
        raise ValueError("Unknown value %s for option %s" % (value, option))

def create_release_file(metadata):
    rel = open("MySQLdb/release.py",'w')
    rel.write("""
__author__ = "%(author)s <%(author_email)s>"
version_info = %(version_info)s
__version__ = "%(version)s"
""" % metadata)
    rel.close()
