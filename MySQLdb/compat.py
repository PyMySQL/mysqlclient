import sys

if sys.version_info[0] == 3:
    unicode = str
    unichr = chr
else:
    unicode = unicode
    unichr = unichr
