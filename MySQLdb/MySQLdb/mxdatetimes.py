"""Use mx.DateTime to handle date and time columns."""

from time import strftime, localtime

try:
    # new packaging
    from mx.DateTime import Date, Time, Timestamp, ISO, \
        DateTimeType, DateTimeDeltaType
except ImportError:
    # old packaging, deprecated
    from DateTime import Date, Time, Timestamp, ISO, \
        DateTimeType, DateTimeDeltaType

def DateFromTicks(ticks):
    """Convert UNIX ticks into a mx.DateTime.Date."""
    return apply(Date, localtime(ticks)[:3])

def TimeFromTicks(ticks):
    """Convert UNIX ticks into a mx.DateTime.Time."""
    return apply(Time, localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    """Convert UNIX ticks into a mx.DateTime.Timestamp."""
    return apply(Timestamp, localtime(ticks)[:6])

def format_DATE(d):
    """Format a DateTime object as an ISO date."""
    return d.strftime("%Y-%m-%d")

def format_TIME(d):
    """Format a DateTime object as a time value."""
    return d.strftime("%d %H:%M:%S")

def format_TIMESTAMP(d):
    """Format a DateTime object as an ISO timestamp."""
    return d.strftime("%Y-%m-%d %H:%M:%S")

def DateTime_or_None(s):
    try: return ISO.ParseDateTime(s)
    except: return None

def TimeDelta_or_None(s):
    try: return ISO.ParseTimeDelta(s)
    except: return None

Time_or_None = TimeDelta_or_None

def Date_or_None(s):
    try: return ISO.ParseDate(s)
    except: return None
