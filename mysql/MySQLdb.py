import _mysql
from _mysql import *
from DateTime import Date, Time, Timestamp, ISO
from types import StringType, ListType, TupleType

threadsafety = 1
apllevel = "1.1"

def mysql_timestamp_converter(s):
    parts = map(int, filter(None, (s[:4],s[4:6],s[6:8],s[8:10],s[10:12],s[12:14])))
    return apply(Timestamp, tuple(parts))
    
type_conv[FIELD_TYPE.TIMESTAMP] = mysql_timestamp_converter
type_conv[FIELD_TYPE.DATETIME] = ISO.ParseDateTime
type_conv[FIELD_TYPE.TIME] = ISO.ParseTime
type_conv[FIELD_TYPE.DATE] = ISO.ParseDate

class Cursor:

    def __init__(self, connection, name=''):
        self.connection = connection
        self.name = name
        self.description = None
        self.rowcount = -1
        self.result = None
        self.arraysize = None
        self.warnings = 1
     
    def setinputsizes(self, size): pass
      
    def setoutputsizes(self, size): pass
         
    def execute(self, query, args=None):
        from types import ListType, TupleType
        from string import rfind, join, split, atoi
        db = self.connection.db
        if not args:
            db.query(query)
        elif type(args) is not ListType:
            db.query(query % escape_row(args))
        else:
            p = rfind(query, '(')
            if p == -1: raise ProgrammingError, "can't find values"
            n = len(args)-1
            q = [query % escape_row(args[0])]
            qv = query[p:]
            for a in args[1:]: q.append(qv % escape_row(a))
            q = join(q, ',\n')
            print q
            db.query(q)
        self.result = db.store_result()
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
        rows = []
        for i in range(size):
            row = self.fetchone()
            if not row: break
            rows.append(row)
        return rows
         
    def fetchall(self):
        rows = []
        while 1:
            row = self.fetchone()
            if not row: break
            rows.append(row)
        return rows
         
    def nextset(self): pass
     
     
def Raw(s): return s 

STRING = FIELD_TYPE.STRING
NUMBER = FIELD_TYPE.LONG
TIME = FIELD_TYPE.TIME
TIMESTAMP = FIELD_TYPE.TIMESTAMP
ROW_ID = FIELD_TYPE.LONG
            
class Connection:
    
    CursorClass = Cursor
    
    def __init__(self, dsn=None, user=None, password=None,
                 host=None, database=None, **kwargs):
        newargs = {}
        if user: newargs['user'] = user
        if password: newargs['passwd'] = password
        if host: newargs['host'] = host
        if database: newargs['db'] = database
        newargs.update(kwargs)
        self.db = apply(_mysql.connect, (), newargs)
     
    def close(self):
        self.db.close()
         
    def commit(self): pass
     
    def cursor(self, name=''):
        return self.CursorClass(self, name)
 
Connect = connect = Connection
