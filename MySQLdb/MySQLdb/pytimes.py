"""Use Python datetime module to handle date and time columns."""

# datetime is only in Python 2.3 or newer, so it is safe to use
# string methods.

from time import localtime
from datetime import date, datetime, time, timedelta

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

def format_TIMESTAMP(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def DateTime_or_None(s):
    if ' ' in s:
        sep = ' '
    elif 'T' in s:
        sep = 'T'
    else:
        return Date_or_None(s)

    try:
        d, t = s.split(sep, 1)
        return datetime(*[ int(x) for x in d.split('-')+t.split(':') ])
    except:
        return Date_or_None(s)

def TimeDelta_or_None(s):
    from math import modf
    try:
        h, m, s = s.split(':')
        td = timedelta(hours=int(h), minutes=int(m), seconds=int(s),
                       microseconds=int(modf(float(s))[0])*1000000)
        if h < 0:
            return -td
        else:
            return td
    except:
        return None

def Time_or_None(s):
    from math import modf
    try:
        h, m, s = s.split(':')
        return time(hour=int(h), minute=int(m), second=int(s),
                    microsecond=int(modf(float(s))[0])*1000000)
    except:
        return None

def Date_or_None(s):
    try: return date(*[ int(x) for x in s.split('-',2)])
    except: return None
