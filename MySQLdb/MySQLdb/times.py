"""times module

This module provides some Date and Time classes for dealing with MySQL data.
"""

from _mysql import string_literal

try:
    from pytimes import *

except ImportError:
    try:
        from mxdatetimes import *

    except ImportError:
        # no DateTime? We'll muddle through somehow.
        from stringtimes import *

def DateTime2literal(d, c):
    """Format a DateTime object as an ISO timestamp."""
    return string_literal(format_TIMESTAMP(d),c)
    
def DateTimeDelta2literal(d, c):
    """Format a DateTimeDelta object as a time."""
    return string_literal(format_TIME(d),c)

def mysql_timestamp_converter(s):
    """Convert a MySQL TIMESTAMP to a Timestamp object."""
    # MySQL>4.1 returns TIMESTAMP in the same format as DATETIME
    if s[4] == '-': return DateTime_or_None(s)
    s = s + "0"*(14-len(s)) # padding
    parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
                                   s[8:10],s[10:12],s[12:14])))
    try: return Timestamp(*parts)
    except: return None
