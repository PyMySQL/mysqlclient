"""Use Python datetime module to handle date and time columns."""

# datetime is only in Python 2.3 or newer, so it is safe to use
# string methods. However, have to use apply(func, args) instead
# of func(*args) because 1.5.2 will reject the syntax.

from time import localtime
from datetime import date, datetime, time, timedelta

Date = date
Time = time
Timestamp = datetime

DateTimeDeltaType = type(timedelta)
DateTimeType = type(datetime)

def DateFromTicks(ticks):
    """Convert UNIX ticks into a date instance."""
    return apply(date, localtime(ticks)[:3])

def TimeFromTicks(ticks):
    """Convert UNIX ticks into a time instance."""
    return apply(time, localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    """Convert UNIX ticks into a datetime instance."""
    return apply(datetime, localtime(ticks)[:6])

format_TIME = format_TIMESTAMP = format_DATE = str

def DateTime_or_None(s):
    if ' ' in s:
        sep = ' '
    elif 'T' in s:
        sep = 'T'
    else:
        return None

    try:
        d, t = s.split(sep, 1)
        return apply(datetime, tuple(d.split('-')+t.split(':')))
    except:
        return None

def TimeDelta_or_None(s):
    try:
        h, m, s = map(float, s.split(':'))
        if h < 0:
            return -timedelta(hours=h, minutes=m, seconds=s)
        else:
            return timedelta(hours=h, minutes=m, seconds=s)
    except:
        return None

def Date_or_None(s):
    try: return apply(date, tuple(s.split('-',2)))
    except: return None
