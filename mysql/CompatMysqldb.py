#author: James Henstridge <james@daa.com.au>
#adapted to _mysql by Andy Dustman <andy@dustman.net>
#under no circumstances should you bug James about this!!!

"""This is a class that implements an interface to mySQL databases, conforming
to the API published by the Python db-sig at
http://www.python.org/sigs/db-sig/DatabaseAPI.html

It is really just a wrapper for an older python interface to mySQL databases
called mySQL, which I modified to facilitate use of a cursor.  That module was
Joseph Skinner's port of the mSQL module by David Gibson, which was a modified
version of Anthony Baxter's msql module.

As an example, to add some extra (unprivelledged) users to your database system,
and delete them again:

>>> import Mysqldb
>>> conn = Mysqldb.mysqldb('mysql@localhost root rootpasswd')
>>> curs = conn.cursor()
>>> curs.execute("insert into user (host, user) values ('%s', '%s')",
... [('localhost', 'linus'), ('somewhere.com.au', 'james')])
2
>>> curs.execute("select * from user")
>>> curs.fetchall()
 -- record listing --
>>> curs.execute("delete from user where host = 'somewhere.com.au' or user = 'linus'")
2
>>> curs.close()
>>> conn.close()

The argument to mysqldb.mysqldb is of the form 'db@host user pass',
'db@host user', 'db@host', 'db', 'db user pass' or 'db user'.

As always, the source is a good manual :-)

James Henstridge <james@daa.com.au>
"""

import _mysql
MySQL = _mysql
from string import upper, split, join

error = 'mysqldb.error'

from _mysql import FIELD_TYPE
_type_conv = { FIELD_TYPE.TINY: int,
               FIELD_TYPE.SHORT: int,
               FIELD_TYPE.LONG: long,
               FIELD_TYPE.FLOAT: float,
               FIELD_TYPE.DOUBLE: float,
               FIELD_TYPE.LONGLONG: long,
               FIELD_TYPE.INT24: int,
               FIELD_TYPE.YEAR: int }

def isDDL(q):
	return upper(split(q)[0]) in ('CREATE', 'ALTER', 'GRANT', 'REVOKE',
		'DROP', 'SET')
def isDML(q):
	return upper(split(q)[0]) in ('DELETE', 'INSERT', 'UPDATE', 'LOAD')
def isDQL(q):
	return upper(split(q)[0]) in ('SELECT', 'SHOW', 'DESC', 'DESCRIBE')

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

_Set = DBAPITypeObject

STRING    = _Set(FIELD_TYPE.CHAR, FIELD_TYPE.ENUM, FIELD_TYPE.INTERVAL,
                 FIELD_TYPE.SET, FIELD_TYPE.STRING, FIELD_TYPE.VAR_STRING)
BINARY    = _Set(FIELD_TYPE.BLOB, FIELD_TYPE.LONG_BLOB, FIELD_TYPE.MEDIUM_BLOB,
                 FIELD_TYPE.TINY_BLOB)
NUMBER    = _Set(FIELD_TYPE.DECIMAL, FIELD_TYPE.DOUBLE, FIELD_TYPE.FLOAT,
	         FIELD_TYPE.INT24, FIELD_TYPE.LONG, FIELD_TYPE.LONGLONG,
	         FIELD_TYPE.TINY, FIELD_TYPE.YEAR)
DATE      = _Set(FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE)
TIME      = _Set(FIELD_TYPE.TIME)
TIMESTAMP = _Set(FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME)
ROWID     = _Set()

class Connection:
	"""This is the connection object for the mySQL database interface."""
	def __init__(self, host, user, passwd, db):
		from _mysql import CLIENT
		kwargs = {}
		kwargs['conv'] = _type_conv
		if host: kwargs['host'] = host
		if user: kwargs['user'] = user
		if passwd: kwargs['passwd'] = passwd
		if db: kwargs['db'] = db
		try:
			self.__conn = apply(MySQL.connect, (), kwargs)
		except MySQL.Error, msg:
			raise error, msg
		self.__curs = Cursor(self.__conn)
		self.__transactional = self.__conn.server_capabilities & CLIENT.TRANSACTIONS

	def __del__(self):
		self.close()

	def __getattr__(self, key):
		return getattr(self.__curs, key)

	def __setattr__(self, key, val):
		if key in ('arraysize', 'description', 'insert_id'):
			setattr(self.__curs, key, val)
		else:
			self.__dict__[key] = val

	def close(self):
		self.__conn = None

	def cursor(self):
		if self.__conn == None: raise error, "Connection is closed."
		return Cursor(self.__conn)

	def commit(self):
		"""Commit the current transaction."""
		if self.__transactional:
			 self.__conn.query("COMMIT")

	def rollback(self):
		"""Rollback the current transaction."""
		if self.__transactional:
			 self.__conn.query("ROLLBACK")
		else: raise error, "Not supported by server"

	def callproc(self, params=None): pass

	# These functions are just here so that every action that is
	# covered by mySQL is covered by mysqldb.  They are not standard
	# DB API.  The list* methods are not included, since they can be
	# done with the SQL SHOW command.
	def create(self, dbname):
		"""This is not a standard part of Python DB API."""
		self.__conn.query("CREATE DATABASE %s" % dbname)
		self.__conn.store_result()
		return None
	def drop(self, dbname):
		"""This is not a standard part of Python DB API."""
		self.__conn.query("DROP DATABASE %s" % dbname)
		self.__conn.store_result()
		return None
	def reload(self):
		"""This is not a standard part of Python DB API."""
		self.__conn.query("RELOAD TABLES")
		self.__conn.store_result()
		return None
	def shutdown(self):
                """This is not a standard part of Python DB API."""
		return self.__conn.shutdown()


class Cursor:
	"""A cursor object for use with connecting to mySQL databases."""
	def __init__(self, conn):
		self.__conn = conn
		self.__res = None
		self.arraysize = 1
		self.__dict__['description'] = None
		self.__open = 1
		self.insert_id = 0

	def __del__(self):
		self.close()

	def __setattr__(self, key, val):
		if key == 'description':
			raise error, "description is a read-only attribute."
		else:
			self.__dict__[key] = val

	def __delattr__(self, key):
		if key in ('description', 'arraysize', 'insert_id'):
			raise error, "%s can't be deleted." % (key,)
		else:
			del self.__dict__[key]

	def close(self):
		self.__conn = None
		self.__res = None
		self.__open = 0

	def execute(self, op, params=None):
		if not self.__open: raise error, "Cursor has been closed."
		if params:
			if type(params[0]) not in (type(()), type([])):
				params = [params]
			if isDDL(op):
				self.__dict__['description'] = None
				try:
					for x in params:
						self.__res = \
						self.__conn.query(op % x)
					self.insert_id = self.__res.insert_id()
				except MySQL.Error, msg:
					raise error, msg
				return 1
			if isDML(op):
				self.__dict__['description'] = None
				af = 0
				try:
					for x in params:
						self.__res = \
						self.__conn.query(op % x)
						af =af+self.__res.affectedrows()
					self.insert_id = self.__res.insert_id()
				except MySQL.Error, msg:
					raise error, msg
				return af
			if isDQL(op):
				try:
					self.__res = self.__conn.query(
						op % params[-1])
					self.insert_id = self.__res.insert_id()
				except MySQL.Error, msg:
					raise error, msg
				self.__dict__['description'] = self.__res.describe()
				return None
		else:
			try:
				self.__conn.query(op)
				self.__res = self.__conn.store_result()
				self.insert_id = self.__conn.insert_id()
			except MySQL.Error, msg:
				raise error, msg
			self.__dict__['description'] = None
			if isDDL(op):
				return 1
			elif self.__conn.affected_rows() != -1:
				return self.__conn.affected_rows()
			else:
				self.__dict__['description'] = self.__res.describe()
				return None
	def fetchone(self):
		if not self.__res: raise error, "no query made yet."
		try:
			return self.__res.fetch_row(1)[0]
		except MySQL.Error, msg:
			raise error, msg

	def fetchmany(self, size=None):
		if not self.__res: raise error, "no query made yet."
		try:
			return self.__res.fetch_row(size or self.arraysize)
		except MySQL.Error, msg:
			raise error, msg

	def fetchall(self):
		if not self.__res: raise error, "no query made yet."
		try:
			return self.__res.fetch_row(0)
		except MySQL.Error, msg:
			raise error, msg

	def fetchoneDict(self):
		"""This is not a standard part of Python DB API."""
		if not self.__res: raise error, "no query made yet."
		try:
			return  self.__res.fetch_row(1, 2)[0]
		except MySQL.Error, msg:
			raise error, msg

	def fetchmanyDict(self, size=None):
		"""This is not a standard part of Python DB API."""
		if not self.__res: raise error, "no query made yet."
		try:
			return  self.__res.fetch_row(size or self.arraysize, 2)
		except MySQL.Error, msg:
			raise error, msg

	def fetchallDict(self):
		"""This is not a standard part of Python DB API."""
		if not self.__res: raise error, "no query made yet."
		try:
			return self.__res.fetch_row(0,2)
		except MySQL.Error, msg:
			raise error, msg

	def setinputsizes(self, sizes): pass
	def setoutputsize(self, size, col=None): pass


def mysqldb(connect_string):
	"""Makes a connection to the MySQL server.  The Argument should be of
	the form 'db@host user pass' or 'db@host user' or 'db@host' or 'db'
	or 'db user pass' or 'db user', where db is the database name, host
	is the server's host name, user is your user name, and pass is your
	password."""
	val = split(connect_string)
	if len(val) == 0: raise error, "no database specified"
	while len(val) < 3: val.append('')
	dh = split(val[0], '@')
	if len(dh) == 0: raise error, "no database specified"
	while len(dh) < 2: dh.append('')
	return Connection(dh[1], val[1], val[2], dh[0])

