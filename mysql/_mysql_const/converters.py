"""MySQLdb type conversion module

This module handles all the type conversions for MySQL. If the default
type conversions aren't what you need, you can make your
own. Dictionaries are used to map "types" to convertor functions:

type_conv -- type conversion dictionary mapping SQL column types
    (FIELD_TYPE) to Python functions. Each function converts a single
    string argument to an appropriate Python data type. By default,
    SQL types not included here are returned as Python strings.

quote_conv -- quoting dictionary mapping Python types to
    functions. Each function takes one argument of the indicated (key)
    type and a mapping argument, and returns an SQL literal,
    i.e. strings will be escaped and quoted. The mapping argument is
    the quoting dictionary itself, and is only used for recursive
    quoting (i.e. when quoting sequences). Most simple converters will
    not need this and can ignore it, but must be prepared to accept
    it. Keys may be either TypeObjects or ClassObjects. Instances will
    be converted by the converter matching the class, if available; or
    the first converter found that is a parent class of the instance;
    or else the str() function will be used converted as a string
    literal.

Don't modify these dictionaries if you can avoid it. Instead, make
copies (with the copy() method), modify the copies, and then pass them
to MySQL.connect().
"""

from _mysql import FIELD_TYPE, string_literal, \
     escape_sequence, escape_dict, NULL
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

    return string_literal(o)

def Instance2Str(o, d):

    """Convert an Instance to a string representation.  If the
    __str__() method produces acceptable output, then you don't need
    to add the class to quote_conv; it will be handled by the default
    converter. If the exact class is not found in d, it will use the
    first class it can find for which o is an instance."""

    if d.has_key(o.__class__): return
    d[o.__class__](o, d)
    cl = filter(lambda x,o=o: type(x)==types.ClassType and isinstance(o,x), d.keys())
    if not cl:
        return d[types.StringType](o,d)
    d[o.__class__] = d[cl[0]]
    return d[cl[0]](o, d)

quote_conv = {
    types.IntType: Thing2Str,
    types.LongType: Long2Int,
    types.FloatType: Thing2Str,
    types.NoneType: None2NULL,
    types.TupleType: escape_sequence,
    types.ListType: escape_sequence,
    types.DictType: escape_dict,
    types.InstanceType: Instance2Str,
    types.StringType: Thing2Literal, # default
    }

type_conv = {
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
        # old packaging
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

    type_conv[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
    type_conv[FIELD_TYPE.DATETIME] = DateTime_or_None
    type_conv[FIELD_TYPE.TIME] = TimeDelta_or_None
    type_conv[FIELD_TYPE.DATE] = Date_or_None

    def DateTime2literal(d, c):
        """Format a DateTime object as an ISO timestamp."""
        return "'%s'" % format_TIMESTAMP(d)
    
    def DateTimeDelta2literal(d, c):
        """Format a DateTimeDelta object as a time."""
        return "'%s'" % format_TIME(d)

    quote_conv[DateTimeType] = DateTime2literal
    quote_conv[DateTimeDeltaType] = DateTimeDelta2literal

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

__all__ = [ 'quote_conv', 'type_conv', 'DateFromTicks', 'TimeFromTicks',
          'TimestampFromTicks', 'format_DATE', 'format_TIME',
          'format_TIMESTAMP' ]
