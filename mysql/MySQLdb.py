import _mysql
from _mysql import *
from DateTime import Date, Time, Timestamp, ISO
from time import localtime
import re

threadsafety = 1
apllevel = "2.0"
paramstyle = "format"

def DateFromTicks(ticks):
    return apply(Date, localtime(ticks)[:3])

def TimeFromTicks(ticks):
    return apply(Time, localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    return apply(Timestamp, localtime(ticks)[:6])


class DBAPITypeObject:
    
    def __init__(self,*values):
        self.values = values
        
    def __cmp__(self,other):
        if other in self.values:
            return 0
        if other < self.values:
            return 1
        else:
            return -1


Set = DBAPITypeObject

STRING    = Set(FIELD_TYPE.CHAR, FIELD_TYPE.ENUM, FIELD_TYPE.INTERVAL,
                FIELD_TYPE.SET, FIELD_TYPE.STRING, FIELD_TYPE.VAR_STRING)
BINARY    = Set(FIELD_TYPE.BLOB, FIELD_TYPE.LONG_BLOB, FIELD_TYPE.MEDIUM_BLOB,
                FIELD_TYPE.TINY_BLOB)
NUMBER    = Set(FIELD_TYPE.DECIMAL, FIELD_TYPE.DOUBLE, FIELD_TYPE.FLOAT,
	        FIELD_TYPE.INT24, FIELD_TYPE.LONG, FIELD_TYPE.LONGLONG,
	        FIELD_TYPE.TINY, FIELD_TYPE.YEAR)
DATE      = Set(FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE)
TIME      = Set(FIELD_TYPE.TIME)
TIMESTAMP = Set(FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME)
ROWID     = Set()

def Binary(x): return str(x)

def format_DATE(d):      return d.Format("%Y-%m-%d")
def format_TIME(d):      return d.Format("%H:%M:%S")
def format_TIMESTAMP(d): return d.Format("%Y-%m-%d %H:%M:%S")

def mysql_timestamp_converter(s):
    parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],s[8:10],s[10:12],s[12:14])))
    return apply(Timestamp, tuple(parts))
    
type_conv[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
type_conv[FIELD_TYPE.DATETIME] = ISO.ParseDateTime
type_conv[FIELD_TYPE.TIME] = ISO.ParseTime
type_conv[FIELD_TYPE.DATE] = ISO.ParseDate

insert_values = re.compile(r'values\s(\(.+\))', re.IGNORECASE)

def escape_dict(d):
    d2 = {}
    for k,v in d.items(): d2[k] = "'%s'" % escape_string(str(v))
    return d2

class Cursor:

    def __init__(self, connection, name='', use=0, warnings=1):
        self.connection = connection
        self.name = name
        self.description = None
        self.rowcount = -1
        self.result = None
        self.arraysize = None
        self.warnings = warnings
	self.use = use
        
    def setinputsizes(self, *args): pass
      
    def setoutputsizes(self, *args): pass
         
    def execute(self, query, args=None):
        from types import ListType, TupleType
        from string import rfind, join, split, atoi
        if not args:
            self._query(query)
        elif type(args) is ListType and type(args[0]) is TupleType:
 	    self.executemany(query, args) # deprecated
 	else:
            try:
                self._query(query % escape_row(args))
            except TypeError:
                self._query(query % escape_dict(args))

    def executemany(self, query, args=None):
        from string import join
        m = insert_values(query)
        if not m: raise ProgrammingError, "can't find values"
        p = m.start(1)
        n = len(args)-1
        escape = escape_row
        try:
	    q = [query % escape(args[0])]
	except TypeError:
	    escape = escape_dict
	    q = [query % escape(args[0])]
        qv = query[p:]
        for a in args[1:]: q.append(qv % escape(a))
        self._query(join(q, ',\n'))

    def _query(self, q):
        from string import split, atoi
        db = self.connection.db
        db.query(q)
        if self.use: self.result = db.use_result()
        else:        self.result = db.store_result()
	if self.result:
     	    self.description = self.result.describe()
     	    self.rowcount = self.result.num_rows()
     	else:
     	    self.description = None
     	    self.rowcount = -1
     	if self.warnings:
     	    w = db.info()
     	    if w:
     	        warnings = atoi(split(w)[-1])
     	        if warnings:
     	            raise Warning, w

    def fetchone(self):
        try:
            return self.result.fetch_row()
        except AttributeError:
            raise ProgrammingError, "no query executed yet"
             
    def fetchmany(self, size=None):
        size = size or self.inputsizes or 1
        return self.result.fetch_rows(size)
         
    def fetchall(self): return self.result.fetch_all_rows()
         
    def nextset(self): return None
     
     
class Connection:
    
    CursorClass = Cursor
    
    def __init__(self, **kwargs):
        self.db = apply(_mysql.connect, (), kwargs)
     
    def close(self):
        self.db.close()
         
    def commit(self): pass
    
    def cursor(self, name=''):
        return self.CursorClass(self, name)


Connect = connect = Connection
