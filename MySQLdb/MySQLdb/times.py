"""times module

This module provides some Date and Time classes for dealing with MySQL data.
"""

from time import strftime, localtime
from _mysql import string_literal

try:
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
        return d.strftime("%H:%M:%S")
    
    def format_TIMESTAMP(d):
        """Format a DateTime object as an ISO timestamp."""
        return d.strftime("%Y-%m-%d %H:%M:%S")

    def DateTime_or_None(s):
        try: return ISO.ParseDateTime(s)
        except: return None

    def TimeDelta_or_None(s):
        try: return ISO.ParseTimeDelta(s)
        except: return None

    def Date_or_None(s):
        try: return ISO.ParseDate(s)
        except: return None


except ImportError:
    # no DateTime? We'll muddle through somehow.
    
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
        """Format a date as a date (does nothing, you don't have mx.DateTime)."""
        return d

    format_TIME = format_TIMESTAMP = format_DATE = \
                  TimeDelta_or_None = Date_or_None

def DateTime2literal(d, c):
    """Format a DateTime object as an ISO timestamp."""
    return string_literal(format_TIMESTAMP(d),c)
    
def DateTimeDelta2literal(d, c):
    """Format a DateTimeDelta object as a time."""
    return string_literal(format_TIME(d),c)

def mysql_timestamp_converter(s):
    """Convert a MySQL TIMESTAMP to a Timestamp object."""
    s = s + "0"*(14-len(s)) # padding
    parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
                                   s[8:10],s[10:12],s[12:14])))
    try: return apply(Timestamp, tuple(parts))
    except: return None
