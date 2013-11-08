"""times module

This module provides some Date and Time classes for dealing with MySQL data.

Use Python datetime module to handle date and time columns."""

import math
from time import localtime
from datetime import date, datetime, time, timedelta
from _mysql import string_literal

Date = date
Time = time
TimeDelta = timedelta
Timestamp = datetime

DateTimeDeltaType = timedelta
DateTimeType = datetime

def DateFromTicks(ticks):
    """Convert UNIX ticks into a date instance."""
    return date(*localtime(ticks)[:3])

def TimeFromTicks(ticks):
    """Convert UNIX ticks into a time instance."""
    return time(*localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    """Convert UNIX ticks into a datetime instance."""
    return datetime(*localtime(ticks)[:6])

format_TIME = format_DATE = str

def format_TIMEDELTA(v):
    seconds = int(v.seconds) % 60
    minutes = int(v.seconds / 60) % 60
    hours = int(v.seconds / 3600) % 24
    return '%d %d:%d:%d' % (v.days, hours, minutes, seconds)

def format_TIMESTAMP(d):
    return d.isoformat(" ")


def DateTime_or_None(s):
    if ' ' in s:
        sep = ' '
    elif 'T' in s:
        sep = 'T'
    else:
        return Date_or_None(s)

    try:
        d, t = s.split(sep, 1)
        if '.' in t:
            t, ms = t.split('.',1)
            ms = ms.ljust(6, '0')
        else:
            ms = 0
        return datetime(*[ int(x) for x in d.split('-')+t.split(':')+[ms] ])
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        return Date_or_None(s)

def TimeDelta_or_None(s):
    try:
        h, m, s = s.split(':')
        if '.' in s:
            s, ms = s.split('.')
            ms = ms.ljust(6, '0')
        else:
            ms = 0
        h, m, s, ms = int(h), int(m), int(s), int(ms)
        td = timedelta(hours=abs(h), minutes=m, seconds=s,
                       microseconds=ms)
        if h < 0:
            return -td
        else:
            return td
    except ValueError:
        # unpacking or int/float conversion failed
        return None

def Time_or_None(s):
    try:
        h, m, s = s.split(':')
        if '.' in s:
            s, ms = s.split('.')
            ms = ms.ljust(6, '0')
        else:
            ms = 0
        h, m, s, ms = int(h), int(m), int(s), int(ms)
        return time(hour=h, minute=m, second=s,
                    microsecond=ms)
    except ValueError:
        return None

def Date_or_None(s):
    try:
        return date(*[ int(x) for x in s.split('-',2)])
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        return None

def DateTime2literal(d, c):
    """Format a DateTime object as an ISO timestamp."""
    return string_literal(format_TIMESTAMP(d),c)
    
def DateTimeDelta2literal(d, c):
    """Format a DateTimeDelta object as a time."""
    return string_literal(format_TIMEDELTA(d),c)

def mysql_timestamp_converter(s):
    """Convert a MySQL TIMESTAMP to a Timestamp object."""
    # MySQL>4.1 returns TIMESTAMP in the same format as DATETIME
    if s[4] == '-': return DateTime_or_None(s)
    s = s + "0"*(14-len(s)) # padding
    parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
                                   s[8:10],s[10:12],s[12:14])))
    try:
        return Timestamp(*parts)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        return None
