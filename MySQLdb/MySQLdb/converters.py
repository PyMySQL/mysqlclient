"""MySQLdb type conversion module

This module handles all the type conversions for MySQL. If the default
type conversions aren't what you need, you can make your own. The
dictionary conversions maps some kind of type to a conversion function
which returns the corresponding value:

Key: FIELD_TYPE.* (from MySQLdb.constants)
Conversion function:
     Arguments: string
     Returns: Python object

Key: Python type object (from types) or class
Conversion function:
     Arguments: Python object of indicated type or class AND 
                conversion dictionary
     Returns: SQL literal value
     Notes: Most conversion functions can ignore the dictionary, but
            it is a required parameter. It is necessary for converting
            things like sequences and instances.

Don't modify conversions if you can avoid it. Instead, make copies
(with the copy() method), modify the copies, and then pass them to
MySQL.connect().

"""

from _mysql import string_literal, escape_sequence, escape_dict, escape, NULL
from constants import FIELD_TYPE
from time import localtime, strftime
import types

def Thing2Str(s, d):
    """Convert something into a string via str()."""
    return str(s)

# Python 1.5.2 compatibility hack
if str(0L)[-1]=='L':
    def Long2Int(l, d):
        """Convert a long integer to a string, chopping the L."""
        return str(l)[:-1]
else:
    Long2Int = Thing2Str

def None2NULL(o, d):
    """Convert None to NULL."""
    return NULL # duh

def Thing2Literal(o, d):
    
    """Convert something into a SQL string literal.  If using
    MySQL-3.23 or newer, string_literal() is a method of the
    _mysql.MYSQL object, and this function will be overridden with
    that method when the connection is created."""

    return string_literal(o, d)

def Instance2Str(o, d):

    """Convert an Instance to a string representation.  If the
    __str__() method produces acceptable output, then you don't need
    to add the class to conversions; it will be handled by the default
    converter. If the exact class is not found in d, it will use the
    first class it can find for which o is an instance."""

    if d.has_key(o.__class__): return
    d[o.__class__](o, d)
    cl = filter(lambda x,o=o:
                type(x)==types.ClassType and isinstance(o,x), d.keys())
    if not cl:
        return d[types.StringType](o,d)
    d[o.__class__] = d[cl[0]]
    return d[cl[0]](o, d)

conversions = {
    types.IntType: Thing2Str,
    types.LongType: Long2Int,
    types.FloatType: Thing2Str,
    types.NoneType: None2NULL,
    types.TupleType: escape_sequence,
    types.ListType: escape_sequence,
    types.DictType: escape_dict,
    types.InstanceType: Instance2Str,
    types.StringType: Thing2Literal, # default
    FIELD_TYPE.TINY: int,
    FIELD_TYPE.SHORT: int,
    FIELD_TYPE.LONG: long,
    FIELD_TYPE.FLOAT: float,
    FIELD_TYPE.DOUBLE: float,
    FIELD_TYPE.LONGLONG: long,
    FIELD_TYPE.INT24: int,
    FIELD_TYPE.YEAR: int
    }

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

    def mysql_timestamp_converter(s):
        """Convert a MySQL TIMESTAMP to a mx.DateTime.Timestamp."""
	parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],
				       s[8:10],s[10:12],s[12:14])))
	try: return apply(Timestamp, tuple(parts))
        except: return None

    def DateTime_or_None(s):
        try: return ISO.ParseDateTime(s)
        except: return None

    def TimeDelta_or_None(s):
        try: return ISO.ParseTimeDelta(s)
        except: return None

    def Date_or_None(s):
        try: return ISO.ParseDate(s)
        except: return None

    conversions[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
    conversions[FIELD_TYPE.DATETIME] = DateTime_or_None
    conversions[FIELD_TYPE.TIME] = TimeDelta_or_None
    conversions[FIELD_TYPE.DATE] = Date_or_None

    def DateTime2literal(d, c):
        """Format a DateTime object as an ISO timestamp."""
        return escape(format_TIMESTAMP(d),c)
    
    def DateTimeDelta2literal(d, c):
        """Format a DateTimeDelta object as a time."""
        return escape(format_TIME(d),c)

    conversions[DateTimeType] = DateTime2literal
    conversions[DateTimeDeltaType] = DateTimeDelta2literal

except ImportError:
    # no DateTime? We'll muddle through somehow.

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
    
    format_TIME = format_TIMESTAMP = format_DATE

__all__ = [ 'conversions', 'DateFromTicks', 'TimeFromTicks',
            'TimestampFromTicks', 'format_DATE', 'format_TIME',
            'format_TIMESTAMP' ]
