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
from MySQLdb.constants import FIELD_TYPE, FLAG
from MySQLdb.times import *

try:
    from types import IntType, LongType, FloatType, NoneType, TupleType, ListType, DictType, InstanceType, \
        StringType, UnicodeType, ObjectType, BooleanType, ClassType, TypeType
except ImportError:
    # Python 3
    long = int
    IntType, LongType, FloatType, NoneType = int, long, float, type(None)
    TupleType, ListType, DictType, InstanceType = tuple, list, dict, None
    StringType, UnicodeType, ObjectType, BooleanType = bytes, str, object, bool

import array

try:
    ArrayType = array.ArrayType
except AttributeError:
    ArrayType = array.array

try:
    set
except NameError:
    from sets import Set as set

def Bool2Str(s, d): return str(int(s))

def Str2Set(s):
    return set([ i for i in s.split(',') if i ])

def Set2Str(s, d):
    return string_literal(','.join(s), d)
    
def Thing2Str(s, d):
    """Convert something into a string via str()."""
    return str(s)

def Unicode2Str(s, d):
    """Convert a unicode object to a string using the default encoding.
    This is only used as a placeholder for the real function, which
    is connection-dependent."""
    return s.encode()

Long2Int = Thing2Str

def Float2Str(o, d):
    return '%.15g' % o

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

    """

    Convert an Instance to a string representation.  If the __str__()
    method produces acceptable output, then you don't need to add the
    class to conversions; it will be handled by the default
    converter. If the exact class is not found in d, it will use the
    first class it can find for which o is an instance.

    """

    if o.__class__ in d:
        return d[o.__class__](o, d)
    cl = filter(lambda x,o=o:
                type(x) is ClassType
                and isinstance(o, x), d.keys())
    if not cl:
        cl = filter(lambda x,o=o:
                    type(x) is TypeType
                    and isinstance(o, x)
                    and d[x] is not Instance2Str,
                    d.keys())
    if not cl:
        return d[StringType](o,d)
    d[o.__class__] = d[cl[0]]
    return d[cl[0]](o, d)

def char_array(s):
    return array.array('c', s)

def array2Str(o, d):
    return Thing2Literal(o.tostring(), d)

def quote_tuple(t, d):
    return "(%s)" % (','.join(escape_sequence(t, d)))

conversions = {
    IntType: Thing2Str,
    LongType: Long2Int,
    FloatType: Float2Str,
    NoneType: None2NULL,
    TupleType: quote_tuple,
    ListType: quote_tuple,
    DictType: escape_dict,
    InstanceType: Instance2Str,
    ArrayType: array2Str,
    StringType: Thing2Literal, # default
    UnicodeType: Unicode2Str,
    ObjectType: Instance2Str,
    BooleanType: Bool2Str,
    DateTimeType: DateTime2literal,
    DateTimeDeltaType: DateTimeDelta2literal,
    set: Set2Str,
    FIELD_TYPE.TINY: int,
    FIELD_TYPE.SHORT: int,
    FIELD_TYPE.LONG: long,
    FIELD_TYPE.FLOAT: float,
    FIELD_TYPE.DOUBLE: float,
    FIELD_TYPE.DECIMAL: float,
    FIELD_TYPE.NEWDECIMAL: float,
    FIELD_TYPE.LONGLONG: long,
    FIELD_TYPE.INT24: int,
    FIELD_TYPE.YEAR: int,
    FIELD_TYPE.SET: Str2Set,
    FIELD_TYPE.TIMESTAMP: mysql_timestamp_converter,
    FIELD_TYPE.DATETIME: DateTime_or_None,
    FIELD_TYPE.TIME: TimeDelta_or_None,
    FIELD_TYPE.DATE: Date_or_None,
    FIELD_TYPE.BLOB: [
        (FLAG.BINARY, str),
        ],
    FIELD_TYPE.STRING: [
        (FLAG.BINARY, str),
        ],
    FIELD_TYPE.VAR_STRING: [
        (FLAG.BINARY, str),
        ],
    FIELD_TYPE.VARCHAR: [
        (FLAG.BINARY, str),
        ],
    }

try:
    from decimal import Decimal
    conversions[FIELD_TYPE.DECIMAL] = Decimal
    conversions[FIELD_TYPE.NEWDECIMAL] = Decimal
except ImportError:
    pass



