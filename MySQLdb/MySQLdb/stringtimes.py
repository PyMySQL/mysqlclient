"""Use strings to handle date and time columns as a last resort."""

from time import strftime, localtime

DateTimeDeltaType = "DateTimeDeltaType"
DateTimeType = "DateTimeType"

def Date(year, month, day):
    """Construct an ISO date string."""
    return "%04d-%02d-%02d" % (year, month, day)

def Time(hour, min, sec):
    """Construct a TIME string."""
    return "%02d:%02d:%02d" % (hour, min, sec)

def Timestamp(year, month, day, hour, min, sec):
    """Construct an ISO timestamp."""
    return "%04d-%02d-%02d %02d:%02d:%02d" % \
           (year, month, day, hour, min, sec)

def DateFromTicks(ticks):
    """Convert UNIX ticks to ISO date format."""
    return strftime("%Y-%m-%d", localtime(ticks))

def TimeFromTicks(ticks):
    """Convert UNIX ticks to time format."""
    return strftime("%H:%M:%S", localtime(ticks))

def TimestampFromTicks(ticks):
    """Convert UNIX ticks to ISO timestamp format."""
    return strftime("%Y-%m-%d %H:%M:%S", localtime(ticks))

def format_DATE(d):
    """Format a date as a date (does nothing, you don't have mx.DateTime)"""
    return d

format_TIME = format_TIMESTAMP = format_DATE
Time_or_None = TimeDelta_or_None = Date_or_None = DateTime_or_None = format_DATE
