"""data module

This module provides some useful classes for dealing with MySQL data.
"""

from time import strftime, localtime
from _mysql import string_literal

class Set:

    """A simple class for handling sets. Sets are immutable in the same
    way numbers are."""
    
    def __init__(self, *values):
        """Use values to initialize the Set."""
        self._values = values

    def contains(self, value):
        """Returns true if the value is contained within the Set."""
        return value in self._values

    def __str__(self):
        """Returns the values as a comma-separated string."""
        from string import join
        return join(map(str, self._values),',')

    def __repr__(self):
        return "Set%s" % `self._values`
    
    def __add__(self, other):
        """Union."""
        if isinstance(other, Set):
            for v in other._values:
                self = self + v
        elif other not in self._values:
            self = apply(Set, self._values+(other,))
        return self

    def __sub__(self, other):
        if isinstance(other, Set):
            for v in other._values:
                if v in self:
                    self = self - v
        elif other in self:
            values = list(self._values)
            values.remove(other)
            return apply(Set, tuple(values))
        return self

    def __mul__(self, other):
        "Intersection."
        intersection = Set()
        if isinstance(other, Set):
            union = self + other
            intersection = union
            for v in union._values:
                if v not in self or v not in other:
                    intersection = intersection - v
        elif other in self:
            intersection = apply(Set, (other,))
        return intersection

    def __mod__(self, other):
        "Disjoint."
        return (self+other)-(self*other)

    def __getitem__(self, n):
        return self._values[n]

    def __len__(self):
        return len(self._values)
    
    def __hash__(self):
        return hash(self._values)
    
    def __cmp__(self, other):
        if isinstance(other, Set):
            d = self % other
            if d._values:
                return 1
            else:
                return 0
        if other in self._values:
            return 0
        return -1

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
