/*
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2, or (at your option)
any later version. Alternatively, you may use the original license
reproduced below.

Copyright 1999 by Comstar.net, Inc., Atlanta, GA, US.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the name of Comstar.net, Inc.
or COMSTAR not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior permission.

COMSTAR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
EVENT SHALL COMSTAR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
*/

#include "mysql.h"
#include "mysqld_error.h"

#include "Python.h"
#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#define PyInt_FromLong(n) PyLong_FromLong(n)
#define PyInt_Check(n) PyLong_Check(n)
#define PyInt_AS_LONG(n) PyLong_AS_LONG(n)
#define PyString_FromString(s) PyUnicode_FromString(s)
#endif

#include "bytesobject.h"
#include "structmember.h"
#include "errmsg.h"

#define MyAlloc(s,t) (s *) t.tp_alloc(&t,0)
#define MyFree(o) Py_TYPE(o)->tp_free((PyObject*)o)

static PyObject *_mysql_MySQLError;
static PyObject *_mysql_Warning;
static PyObject *_mysql_Error;
static PyObject *_mysql_DatabaseError;
static PyObject *_mysql_InterfaceError; 
static PyObject *_mysql_DataError;
static PyObject *_mysql_OperationalError; 
static PyObject *_mysql_IntegrityError; 
static PyObject *_mysql_InternalError; 
static PyObject *_mysql_ProgrammingError;
static PyObject *_mysql_NotSupportedError;

typedef struct {
	PyObject_HEAD
	MYSQL connection;
	int open;
	PyObject *converter;
} _mysql_ConnectionObject;

#define check_connection(c) if (!(c->open)) return _mysql_Exception(c)
#define result_connection(r) ((_mysql_ConnectionObject *)r->conn)
#define check_result_connection(r) check_connection(result_connection(r))

extern PyTypeObject _mysql_ConnectionObject_Type;

typedef struct {
	PyObject_HEAD
	PyObject *conn;
	MYSQL_RES *result;
	int nfields;
	int use;
	char has_next;
	PyObject *converter;
} _mysql_ResultObject;

extern PyTypeObject _mysql_ResultObject_Type;

static int _mysql_server_init_done = 0;
#define check_server_init(x) if (!_mysql_server_init_done) { if (mysql_server_init(0, NULL, NULL)) { _mysql_Exception(NULL); return x; } else { _mysql_server_init_done = 1;} }

#if MYSQL_VERSION_ID >= 50500
#define HAVE_OPENSSL 1
#endif

/* According to https://dev.mysql.com/doc/refman/5.1/en/mysql-options.html
   The MYSQL_OPT_READ_TIMEOUT apear in the version 5.1.12 */
#if MYSQL_VERSION_ID > 50112
#define HAVE_MYSQL_OPT_TIMEOUTS 1
#endif

PyObject *
_mysql_Exception(_mysql_ConnectionObject *c)
{
	PyObject *t, *e;
	int merr;

	if (!(t = PyTuple_New(2))) return NULL;
	if (!_mysql_server_init_done) {
		e = _mysql_InternalError;
		PyTuple_SET_ITEM(t, 0, PyInt_FromLong(-1L));
		PyTuple_SET_ITEM(t, 1, PyString_FromString("server not initialized"));
		PyErr_SetObject(e, t);
		Py_DECREF(t);
		return NULL;
	}
	merr = mysql_errno(&(c->connection));
	switch (merr) {
	case 0:
		e = _mysql_InterfaceError;
		break;
	case CR_COMMANDS_OUT_OF_SYNC:
	case ER_DB_CREATE_EXISTS:
	case ER_SYNTAX_ERROR:
	case ER_PARSE_ERROR:
	case ER_NO_SUCH_TABLE:
	case ER_WRONG_DB_NAME:
	case ER_WRONG_TABLE_NAME:
	case ER_FIELD_SPECIFIED_TWICE:
	case ER_INVALID_GROUP_FUNC_USE:
	case ER_UNSUPPORTED_EXTENSION:
	case ER_TABLE_MUST_HAVE_COLUMNS:
#ifdef ER_CANT_DO_THIS_DURING_AN_TRANSACTION
	case ER_CANT_DO_THIS_DURING_AN_TRANSACTION:
#endif
		e = _mysql_ProgrammingError;
		break;
#ifdef WARN_DATA_TRUNCATED
	case WARN_DATA_TRUNCATED:
#ifdef WARN_NULL_TO_NOTNULL
	case WARN_NULL_TO_NOTNULL:
#endif
#ifdef ER_WARN_DATA_OUT_OF_RANGE
	case ER_WARN_DATA_OUT_OF_RANGE:
#endif
#ifdef ER_NO_DEFAULT
	case ER_NO_DEFAULT:
#endif
#ifdef ER_PRIMARY_CANT_HAVE_NULL
	case ER_PRIMARY_CANT_HAVE_NULL:
#endif
#ifdef ER_DATA_TOO_LONG
	case ER_DATA_TOO_LONG:
#endif
#ifdef ER_DATETIME_FUNCTION_OVERFLOW
	case ER_DATETIME_FUNCTION_OVERFLOW:
#endif
		e = _mysql_DataError;
		break;
#endif
	case ER_DUP_ENTRY:
#ifdef ER_DUP_UNIQUE
	case ER_DUP_UNIQUE:
#endif
#ifdef ER_NO_REFERENCED_ROW
	case ER_NO_REFERENCED_ROW:
#endif
#ifdef ER_NO_REFERENCED_ROW_2
	case ER_NO_REFERENCED_ROW_2:
#endif
#ifdef ER_ROW_IS_REFERENCED
	case ER_ROW_IS_REFERENCED:
#endif
#ifdef ER_ROW_IS_REFERENCED_2
	case ER_ROW_IS_REFERENCED_2:
#endif
#ifdef ER_CANNOT_ADD_FOREIGN
	case ER_CANNOT_ADD_FOREIGN:
#endif
#ifdef ER_NO_DEFAULT_FOR_FIELD
	case ER_NO_DEFAULT_FOR_FIELD:
#endif
		e = _mysql_IntegrityError;
		break;
#ifdef ER_WARNING_NOT_COMPLETE_ROLLBACK
	case ER_WARNING_NOT_COMPLETE_ROLLBACK:
#endif
#ifdef ER_NOT_SUPPORTED_YET
	case ER_NOT_SUPPORTED_YET:
#endif
#ifdef ER_FEATURE_DISABLED
	case ER_FEATURE_DISABLED:
#endif
#ifdef ER_UNKNOWN_STORAGE_ENGINE
	case ER_UNKNOWN_STORAGE_ENGINE:
#endif
		e = _mysql_NotSupportedError;
		break;
	default:
		if (merr < 1000)
			e = _mysql_InternalError;
		else
			e = _mysql_OperationalError;
		break;
	}
	PyTuple_SET_ITEM(t, 0, PyInt_FromLong((long)merr));
	PyTuple_SET_ITEM(t, 1, PyString_FromString(mysql_error(&(c->connection))));
	PyErr_SetObject(e, t);
	Py_DECREF(t);
	return NULL;
}

static char _mysql_server_init__doc__[] =
"Initialize embedded server. If this client is not linked against\n\
the embedded server library, this function does nothing.\n\
\n\
args -- sequence of command-line arguments\n\
groups -- sequence of groups to use in defaults files\n\
";

static PyObject *_mysql_server_init(
	PyObject *self,
	PyObject *args,
	PyObject *kwargs) {
	static char *kwlist[] = {"args", "groups", NULL};
	char **cmd_args_c=NULL, **groups_c=NULL, *s;
	int cmd_argc=0, i, groupc;
	PyObject *cmd_args=NULL, *groups=NULL, *ret=NULL, *item;

	if (_mysql_server_init_done) {
		PyErr_SetString(_mysql_ProgrammingError,
				"already initialized");
		return NULL;
	}

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OO", kwlist,
					 &cmd_args, &groups))
		return NULL;

	if (cmd_args) {
		if (!PySequence_Check(cmd_args)) {
			PyErr_SetString(PyExc_TypeError,
					"args must be a sequence");
			goto finish;
		}
		cmd_argc = PySequence_Size(cmd_args);
		if (cmd_argc == -1) {
			PyErr_SetString(PyExc_TypeError,
					"args could not be sized");
			goto finish;
		}
		cmd_args_c = (char **) PyMem_Malloc(cmd_argc*sizeof(char *));
		for (i=0; i< cmd_argc; i++) {
			item = PySequence_GetItem(cmd_args, i);
#ifdef IS_PY3K
			s = PyUnicode_AsUTF8(item);
#else
			s = PyString_AsString(item);
#endif

			Py_DECREF(item);
			if (!s) {
				PyErr_SetString(PyExc_TypeError,
						"args must contain strings");
				goto finish;
			}
			cmd_args_c[i] = s;
		}
	}
	if (groups) {
		if (!PySequence_Check(groups)) {
			PyErr_SetString(PyExc_TypeError,
					"groups must be a sequence");
			goto finish;
		}
		groupc = PySequence_Size(groups);
		if (groupc == -1) {
			PyErr_SetString(PyExc_TypeError,
					"groups could not be sized");
			goto finish;
		}
		groups_c = (char **) PyMem_Malloc((1+groupc)*sizeof(char *));
		for (i=0; i< groupc; i++) {
			item = PySequence_GetItem(groups, i);
#ifdef IS_PY3K
			s = PyUnicode_AsUTF8(item);
#else
			s = PyString_AsString(item);
#endif
			Py_DECREF(item);
			if (!s) {
				PyErr_SetString(PyExc_TypeError,
						"groups must contain strings");
				goto finish;
			}
			groups_c[i] = s;
		}
		groups_c[groupc] = (char *)NULL;
	}
	/* even though this may block, don't give up the interpreter lock
	   so that the server can't be initialized multiple times. */
	if (mysql_server_init(cmd_argc, cmd_args_c, groups_c)) {
		_mysql_Exception(NULL);
		goto finish;
	}
	ret = Py_None;
	Py_INCREF(Py_None);
	_mysql_server_init_done = 1;
  finish:
	PyMem_Free(groups_c);
	PyMem_Free(cmd_args_c);
	return ret;
}

static char _mysql_server_end__doc__[] =
"Shut down embedded server. If not using an embedded server, this\n\
does nothing.";

static PyObject *_mysql_server_end(
	PyObject *self,
	PyObject *args) {
	if (_mysql_server_init_done) {
		mysql_server_end();
		_mysql_server_init_done = 0;
		Py_INCREF(Py_None);
		return Py_None;
	}
	return _mysql_Exception(NULL);
}

static char _mysql_thread_safe__doc__[] =
"Indicates whether the client is compiled as thread-safe.";

static PyObject *_mysql_thread_safe(
	PyObject *self,
	PyObject *noargs)
{
	PyObject *flag;
	check_server_init(NULL);
	if (!(flag=PyInt_FromLong((long)mysql_thread_safe()))) return NULL;
	return flag;
}

static char _mysql_ResultObject__doc__[] =
"result(connection, use=0, converter={}) -- Result set from a query.\n\
\n\
Creating instances of this class directly is an excellent way to\n\
shoot yourself in the foot. If using _mysql.connection directly,\n\
use connection.store_result() or connection.use_result() instead.\n\
If using MySQLdb.Connection, this is done by the cursor class.\n\
Just forget you ever saw this. Forget... FOR-GET...";

static int
_mysql_ResultObject_Initialize(
	_mysql_ResultObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	static char *kwlist[] = {"connection", "use", "converter", NULL};
	MYSQL_RES *result; 
	_mysql_ConnectionObject *conn=NULL;
	int use=0; 
	PyObject *conv=NULL;
	int n, i;
	MYSQL_FIELD *fields;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O!|iO", kwlist,
					 &_mysql_ConnectionObject_Type, &conn, &use, &conv))
		return -1;
	if (!conv) {
		if (!(conv = PyDict_New()))
			return -1;
	}
	else
		Py_INCREF(conv);

	self->conn = (PyObject *) conn;
	Py_INCREF(conn);
	self->use = use;
	Py_BEGIN_ALLOW_THREADS ;
	if (use)
		result = mysql_use_result(&(conn->connection));
	else
		result = mysql_store_result(&(conn->connection));
	self->result = result;
	self->has_next = (char)mysql_more_results(&(conn->connection));
	Py_END_ALLOW_THREADS ;
	if (!result) {
		if (mysql_errno(&(conn->connection))) {
		    _mysql_Exception(conn);
		    return -1;
		}
		self->converter = PyTuple_New(0);
		Py_DECREF(conv);
		return 0;
	}
	n = mysql_num_fields(result);
	self->nfields = n;
	if (!(self->converter = PyTuple_New(n))) {
		Py_DECREF(conv);
		return -1;
	}
	fields = mysql_fetch_fields(result);
	for (i=0; i<n; i++) {
		PyObject *tmp, *fun;
		tmp = PyInt_FromLong((long) fields[i].type);
		if (!tmp) {
			Py_DECREF(conv);
			return -1;
		}
		fun = PyObject_GetItem(conv, tmp);
		Py_DECREF(tmp);
		if (!fun) {
			if (PyErr_Occurred()) {
				if (!PyErr_ExceptionMatches(PyExc_KeyError)) {
					Py_DECREF(conv);
					return -1;
				}
				PyErr_Clear();
			}
			fun = Py_None;
			Py_INCREF(Py_None);
		}
		else if (PySequence_Check(fun)) {
			long flags = fields[i].flags;
			PyObject *fun2=NULL;
			int j, n2=PySequence_Size(fun);
			if (fields[i].charsetnr != 63) { /* maaagic */
				flags &= ~BINARY_FLAG;
			}
			for (j=0; j<n2; j++) {
				PyObject *t = PySequence_GetItem(fun, j);
				if (!t) {
					Py_DECREF(fun);
					Py_DECREF(conv);
					return -1;
				}
				if (PyTuple_Check(t) && PyTuple_GET_SIZE(t) == 2) {
					long mask;
					PyObject *pmask=NULL;
					pmask = PyTuple_GET_ITEM(t, 0);
					fun2 = PyTuple_GET_ITEM(t, 1);
					Py_XINCREF(fun2);
					if (PyInt_Check(pmask)) {
						mask = PyInt_AS_LONG(pmask);
						if (mask & flags) {
							Py_DECREF(t);
							break;
						}
						else {
							fun2 = NULL;
						}
					} else {
						Py_DECREF(t);
						break;
					}
				}
				Py_DECREF(t);
			}
			if (!fun2) {
				fun2 = Py_None;
				Py_INCREF(fun2);
			}
			Py_DECREF(fun);
			fun = fun2;
		}
		PyTuple_SET_ITEM(self->converter, i, fun);
	}

	Py_DECREF(conv);
	return 0;
}

static int _mysql_ResultObject_traverse(
	_mysql_ResultObject *self,
	visitproc visit,
	void *arg)
{
	int r;
	if (self->converter) {
		if (!(r = visit(self->converter, arg))) return r;
	}
	if (self->conn)
		return visit(self->conn, arg);
	return 0;
}

static int _mysql_ResultObject_clear(_mysql_ResultObject *self)
{
	Py_CLEAR(self->converter);
	Py_CLEAR(self->conn);
	return 0;
}

static int
_mysql_ConnectionObject_Initialize(
	_mysql_ConnectionObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	MYSQL *conn = NULL;
	PyObject *conv = NULL;
	PyObject *ssl = NULL;
#if HAVE_OPENSSL
	char *key = NULL, *cert = NULL, *ca = NULL,
		 *capath = NULL, *cipher = NULL;
	PyObject *ssl_keepref[5] = {NULL};
	int n_ssl_keepref = 0;
#endif
	char *host = NULL, *user = NULL, *passwd = NULL,
		 *db = NULL, *unix_socket = NULL;
	unsigned int port = 0;
	unsigned int client_flag = 0;
	static char *kwlist[] = { "host", "user", "passwd", "db", "port",
				  "unix_socket", "conv",
				  "connect_timeout", "compress",
				  "named_pipe", "init_command",
				  "read_default_file", "read_default_group",
				  "client_flag", "ssl",
				  "local_infile",
#ifdef HAVE_MYSQL_OPT_TIMEOUTS
				  "read_timeout",
				  "write_timeout",
#endif
				  NULL } ;
	int connect_timeout = 0;
#ifdef HAVE_MYSQL_OPT_TIMEOUTS
	int read_timeout = 0;
	int write_timeout = 0;
#endif
	int compress = -1, named_pipe = -1, local_infile = -1;
	char *init_command=NULL,
	     *read_default_file=NULL,
	     *read_default_group=NULL;

	self->converter = NULL;
	self->open = 0;
	check_server_init(-1);

	if (!PyArg_ParseTupleAndKeywords(args, kwargs,
#ifdef HAVE_MYSQL_OPT_TIMEOUTS
                                         "|ssssisOiiisssiOiii:connect",
#else
                                         "|ssssisOiiisssiOi:connect",
#endif
					 kwlist,
					 &host, &user, &passwd, &db,
					 &port, &unix_socket, &conv,
					 &connect_timeout,
					 &compress, &named_pipe,
					 &init_command, &read_default_file,
					 &read_default_group,
					 &client_flag, &ssl,
                     &local_infile
#ifdef HAVE_MYSQL_OPT_TIMEOUTS
                     , &read_timeout
                     , &write_timeout
#endif
	))
		return -1;

#ifdef IS_PY3K
#define _stringsuck(d,t,s) {t=PyMapping_GetItemString(s,#d);\
        if(t){d=PyUnicode_AsUTF8(t);ssl_keepref[n_ssl_keepref++]=t;}\
        PyErr_Clear();}
#else
#define _stringsuck(d,t,s) {t=PyMapping_GetItemString(s,#d);\
        if(t){d=PyString_AsString(t);ssl_keepref[n_ssl_keepref++]=t;}\
        PyErr_Clear();}
#endif

	if (ssl) {
#if HAVE_OPENSSL
		PyObject *value = NULL;
		_stringsuck(ca, value, ssl);
		_stringsuck(capath, value, ssl);
		_stringsuck(cert, value, ssl);
		_stringsuck(key, value, ssl);
		_stringsuck(cipher, value, ssl);
#else
		PyErr_SetString(_mysql_NotSupportedError,
				"client library does not have SSL support");
		return -1;
#endif
	}

	Py_BEGIN_ALLOW_THREADS ;
	conn = mysql_init(&(self->connection));
	if (connect_timeout) {
		unsigned int timeout = connect_timeout;
		mysql_options(&(self->connection), MYSQL_OPT_CONNECT_TIMEOUT, 
				(char *)&timeout);
	}
#ifdef HAVE_MYSQL_OPT_TIMEOUTS
	if (read_timeout) {
		unsigned int timeout = read_timeout;
		mysql_options(&(self->connection), MYSQL_OPT_READ_TIMEOUT,
				(char *)&timeout);
	}
	if (write_timeout) {
		unsigned int timeout = write_timeout;
		mysql_options(&(self->connection), MYSQL_OPT_WRITE_TIMEOUT,
				(char *)&timeout);
	}
#endif
	if (compress != -1) {
		mysql_options(&(self->connection), MYSQL_OPT_COMPRESS, 0);
		client_flag |= CLIENT_COMPRESS;
	}
	if (named_pipe != -1)
		mysql_options(&(self->connection), MYSQL_OPT_NAMED_PIPE, 0);
	if (init_command != NULL)
		mysql_options(&(self->connection), MYSQL_INIT_COMMAND, init_command);
	if (read_default_file != NULL)
		mysql_options(&(self->connection), MYSQL_READ_DEFAULT_FILE, read_default_file);
	if (read_default_group != NULL)
		mysql_options(&(self->connection), MYSQL_READ_DEFAULT_GROUP, read_default_group);

	if (local_infile != -1)
		mysql_options(&(self->connection), MYSQL_OPT_LOCAL_INFILE, (char *) &local_infile);

#if HAVE_OPENSSL
	if (ssl) {
		mysql_ssl_set(&(self->connection), key, cert, ca, capath, cipher);
	}
#endif

	conn = mysql_real_connect(&(self->connection), host, user, passwd, db,
				  port, unix_socket, client_flag);

	Py_END_ALLOW_THREADS ;

#if HAVE_OPENSSL
	if (ssl) {
		int i;
		for (i=0; i<n_ssl_keepref; i++) {
			Py_DECREF(ssl_keepref[i]);
			ssl_keepref[i] = NULL;
		}
	}
#endif

	if (!conn) {
		_mysql_Exception(self);
		return -1;
	}

	/* Internal references to python-land objects */
	if (!conv)
		conv = PyDict_New();
	else
		Py_INCREF(conv);

	if (!conv)
		return -1;
	self->converter = conv;

	/*
	  PyType_GenericAlloc() automatically sets up GC allocation and
	  tracking for GC objects, at least in 2.2.1, so it does not need to
	  be done here. tp_dealloc still needs to call PyObject_GC_UnTrack(),
	  however.
	*/
	self->open = 1;
	return 0;
}

static char _mysql_connect__doc__[] =
"Returns a MYSQL connection object. Exclusive use of\n\
keyword parameters strongly recommended. Consult the\n\
MySQL C API documentation for more details.\n\
\n\
host\n\
  string, host to connect\n\
\n\
user\n\
  string, user to connect as\n\
\n\
passwd\n\
  string, password to use\n\
\n\
db\n\
  string, database to use\n\
\n\
port\n\
  integer, TCP/IP port to connect to\n\
\n\
unix_socket\n\
  string, location of unix_socket (UNIX-ish only)\n\
\n\
conv\n\
  mapping, maps MySQL FIELD_TYPE.* to Python functions which\n\
  convert a string to the appropriate Python type\n\
\n\
connect_timeout\n\
  number of seconds to wait before the connection\n\
  attempt fails.\n\
\n\
compress\n\
  if set, gzip compression is enabled\n\
\n\
named_pipe\n\
  if set, connect to server via named pipe (Windows only)\n\
\n\
init_command\n\
  command which is run once the connection is created\n\
\n\
read_default_file\n\
  see the MySQL documentation for mysql_options()\n\
\n\
read_default_group\n\
  see the MySQL documentation for mysql_options()\n\
\n\
client_flag\n\
  client flags from MySQLdb.constants.CLIENT\n\
\n\
load_infile\n\
  int, non-zero enables LOAD LOCAL INFILE, zero disables\n\
\n\
";

static PyObject *
_mysql_connect(
	PyObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	_mysql_ConnectionObject *c=NULL;

	c = MyAlloc(_mysql_ConnectionObject, _mysql_ConnectionObject_Type);
	if (c == NULL) return NULL;
	if (_mysql_ConnectionObject_Initialize(c, args, kwargs)) {
		Py_DECREF(c);
		c = NULL;
	}
	return (PyObject *) c;
}

static int _mysql_ConnectionObject_traverse(
	_mysql_ConnectionObject *self,
	visitproc visit,
	void *arg)
{
	if (self->converter)
		return visit(self->converter, arg);
	return 0;
}

static int _mysql_ConnectionObject_clear(
	_mysql_ConnectionObject *self)
{
	Py_XDECREF(self->converter);
	self->converter = NULL;
	return 0;
}

static char _mysql_ConnectionObject_fileno__doc__[] =
"Return underlaying fd for connection";

static PyObject *
_mysql_ConnectionObject_fileno(
	_mysql_ConnectionObject *self)
{
	return PyInt_FromLong(self->connection.net.fd);
}

static char _mysql_ConnectionObject_close__doc__[] =
"Close the connection. No further activity possible.";

static PyObject *
_mysql_ConnectionObject_close(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	if (self->open) {
		Py_BEGIN_ALLOW_THREADS
		mysql_close(&(self->connection));
		Py_END_ALLOW_THREADS
		self->open = 0;
	} else {
		PyErr_SetString(_mysql_ProgrammingError,
				"closing a closed connection");
		return NULL;
	}
	_mysql_ConnectionObject_clear(self);
	Py_RETURN_NONE;
}

static char _mysql_ConnectionObject_affected_rows__doc__ [] =
"Return number of rows affected by the last query.\n\
Non-standard. Use Cursor.rowcount.\n\
";

static PyObject *
_mysql_ConnectionObject_affected_rows(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	my_ulonglong ret;
	check_connection(self);
	ret = mysql_affected_rows(&(self->connection));
	if (ret == (my_ulonglong)-1)
		return PyInt_FromLong(-1);
	return PyLong_FromUnsignedLongLong(ret);
}

static char _mysql_debug__doc__[] =
"Does a DBUG_PUSH with the given string.\n\
mysql_debug() uses the Fred Fish debug library.\n\
To use this function, you must compile the client library to\n\
support debugging.\n\
";
static PyObject *
_mysql_debug(
	PyObject *self,
	PyObject *args)
{
	char *debug;
	if (!PyArg_ParseTuple(args, "s", &debug)) return NULL;
	mysql_debug(debug);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_dump_debug_info__doc__[] =
"Instructs the server to write some debug information to the\n\
log. The connected user must have the process privilege for\n\
this to work. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_dump_debug_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int err;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	err = mysql_dump_debug_info(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_autocommit__doc__[] =
"Set the autocommit mode. True values enable; False value disable.\n\
";
static PyObject *
_mysql_ConnectionObject_autocommit(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int flag, err;
	if (!PyArg_ParseTuple(args, "i", &flag)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_autocommit(&(self->connection), flag);
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_get_autocommit__doc__[] =
"Get the autocommit mode. True when enable; False when disable.\n";

static PyObject *
_mysql_ConnectionObject_get_autocommit(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (self->connection.server_status & SERVER_STATUS_AUTOCOMMIT) {
		Py_RETURN_TRUE;
	}
	Py_RETURN_FALSE;
}

static char _mysql_ConnectionObject_commit__doc__[] =
"Commits the current transaction\n\
";
static PyObject *
_mysql_ConnectionObject_commit(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int err;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_commit(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_rollback__doc__[] =
"Rolls backs the current transaction\n\
";
static PyObject *
_mysql_ConnectionObject_rollback(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int err;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_rollback(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}		

static char _mysql_ConnectionObject_next_result__doc__[] =
"If more query results exist, next_result() reads the next query\n\
results and returns the status back to application.\n\
\n\
After calling next_result() the state of the connection is as if\n\
you had called query() for the next query. This means that you can\n\
now call store_result(), warning_count(), affected_rows()\n\
, and so forth. \n\
\n\
Returns 0 if there are more results; -1 if there are no more results\n\
\n\
Non-standard.\n\
";
static PyObject *
_mysql_ConnectionObject_next_result(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int err;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_next_result(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err > 0) return _mysql_Exception(self);
	return PyInt_FromLong(err);
}		


static char _mysql_ConnectionObject_set_server_option__doc__[] =
"set_server_option(option) -- Enables or disables an option\n\
for the connection.\n\
\n\
Non-standard.\n\
";
static PyObject *
_mysql_ConnectionObject_set_server_option(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int err, flags=0;
	if (!PyArg_ParseTuple(args, "i", &flags))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_set_server_option(&(self->connection), flags);
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	return PyInt_FromLong(err);
}		

static char _mysql_ConnectionObject_sqlstate__doc__[] =
"Returns a string containing the SQLSTATE error code\n\
for the last error. The error code consists of five characters.\n\
'00000' means \"no error.\" The values are specified by ANSI SQL\n\
and ODBC. For a list of possible values, see section 23\n\
Error Handling in MySQL in the MySQL Manual.\n\
\n\
Note that not all MySQL errors are yet mapped to SQLSTATE's.\n\
The value 'HY000' (general error) is used for unmapped errors.\n\
\n\
Non-standard.\n\
";
static PyObject *
_mysql_ConnectionObject_sqlstate(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	return PyString_FromString(mysql_sqlstate(&(self->connection)));
}

static char _mysql_ConnectionObject_warning_count__doc__[] =
"Returns the number of warnings generated during execution\n\
of the previous SQL statement.\n\
\n\
Non-standard.\n\
";
static PyObject *
_mysql_ConnectionObject_warning_count(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	return PyInt_FromLong(mysql_warning_count(&(self->connection)));
}		

static char _mysql_ConnectionObject_errno__doc__[] =
"Returns the error code for the most recently invoked API function\n\
that can succeed or fail. A return value of zero means that no error\n\
occurred.\n\
";

static PyObject *
_mysql_ConnectionObject_errno(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyInt_FromLong((long)mysql_errno(&(self->connection)));
}

static char _mysql_ConnectionObject_error__doc__[] =
"Returns the error message for the most recently invoked API function\n\
that can succeed or fail. An empty string ("") is returned if no error\n\
occurred.\n\
";

static PyObject *
_mysql_ConnectionObject_error(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyString_FromString(mysql_error(&(self->connection)));
}

static char _mysql_escape_string__doc__[] =
"escape_string(s) -- quote any SQL-interpreted characters in string s.\n\
\n\
Use connection.escape_string(s), if you use it at all.\n\
_mysql.escape_string(s) cannot handle character sets. You are\n\
probably better off using connection.escape(o) instead, since\n\
it will escape entire sequences as well as strings.";

static PyObject *
_mysql_escape_string(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	PyObject *str;
	char *in, *out;
	int len, size;
	if (!PyArg_ParseTuple(args, "s#:escape_string", &in, &size)) return NULL;
	str = PyBytes_FromStringAndSize((char *) NULL, size*2+1);
	if (!str) return PyErr_NoMemory();
	out = PyBytes_AS_STRING(str);
	check_server_init(NULL);

	if (self && PyModule_Check((PyObject*)self))
		self = NULL;
	if (self && self->open) {
#if MYSQL_VERSION_ID >= 50707 && !defined(MARIADB_BASE_VERSION) && !defined(MARIADB_VERSION_ID)
		len = mysql_real_escape_string_quote(&(self->connection), out, in, size, '\'');
#else
		len = mysql_real_escape_string(&(self->connection), out, in, size);
#endif
	} else {
		len = mysql_escape_string(out, in, size);
	}
	if (_PyBytes_Resize(&str, len) < 0) return NULL;
	return (str);
}

static char _mysql_string_literal__doc__[] =
"string_literal(obj) -- converts object obj into a SQL string literal.\n\
This means, any special SQL characters are escaped, and it is enclosed\n\
within single quotes. In other words, it performs:\n\
\n\
\"'%s'\" % escape_string(str(obj))\n\
\n\
Use connection.string_literal(obj), if you use it at all.\n\
_mysql.string_literal(obj) cannot handle character sets.";

static PyObject *
_mysql_string_literal(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	PyObject *str, *s, *o, *d;
	char *in, *out;
	int len, size;
	if (self && PyModule_Check((PyObject*)self))
		self = NULL;
	if (!PyArg_ParseTuple(args, "O|O:string_literal", &o, &d)) return NULL;
	if (PyBytes_Check(o)) {
		s = o;
		Py_INCREF(s);
	} else {
		s = PyObject_Str(o);
		if (!s) return NULL;
#ifdef IS_PY3K
		{
			PyObject *t = PyUnicode_AsASCIIString(s);
			Py_DECREF(s);
			if (!t) return NULL;
			s = t;
		}
#endif
	}
	in = PyBytes_AsString(s);
	size = PyBytes_GET_SIZE(s);
	str = PyBytes_FromStringAndSize((char *) NULL, size*2+3);
	if (!str) {
		Py_DECREF(s);
		return PyErr_NoMemory();
	}
	out = PyBytes_AS_STRING(str);
	check_server_init(NULL);
	if (self && self->open) {
#if MYSQL_VERSION_ID >= 50707 && !defined(MARIADB_BASE_VERSION) && !defined(MARIADB_VERSION_ID)
		len = mysql_real_escape_string_quote(&(self->connection), out+1, in, size, '\'');
#else
		len = mysql_real_escape_string(&(self->connection), out+1, in, size);
#endif
	} else {
		len = mysql_escape_string(out+1, in, size);
	}
	*out = *(out+len+1) = '\'';
	if (_PyBytes_Resize(&str, len+2) < 0) return NULL;
	Py_DECREF(s);
	return (str);
}

static PyObject *_mysql_NULL;

static PyObject *
_escape_item(
	PyObject *item,
	PyObject *d)
{
	PyObject *quoted=NULL, *itemtype, *itemconv;
	if (!(itemtype = PyObject_Type(item)))
		goto error;
	itemconv = PyObject_GetItem(d, itemtype);
	Py_DECREF(itemtype);
	if (!itemconv) {
		PyErr_Clear();
		itemconv = PyObject_GetItem(d,
#ifdef IS_PY3K
				 (PyObject *) &PyUnicode_Type);
#else
				 (PyObject *) &PyString_Type);
#endif
	}
	if (!itemconv) {
		PyErr_SetString(PyExc_TypeError,
				"no default type converter defined");
		goto error;
	}
	Py_INCREF(d);
	quoted = PyObject_CallFunction(itemconv, "OO", item, d);
	Py_DECREF(d);
	Py_DECREF(itemconv);
error:
	return quoted;
}

static char _mysql_escape__doc__[] =
"escape(obj, dict) -- escape any special characters in object obj\n\
using mapping dict to provide quoting functions for each type.\n\
Returns a SQL literal string.";
static PyObject *
_mysql_escape(
	PyObject *self,
	PyObject *args)
{
	PyObject *o=NULL, *d=NULL;
	if (!PyArg_ParseTuple(args, "O|O:escape", &o, &d))
		return NULL;
	if (d) {
		if (!PyMapping_Check(d)) {
			PyErr_SetString(PyExc_TypeError,
					"argument 2 must be a mapping");
			return NULL;
		}
		return _escape_item(o, d);
	} else {
		if (!self) {
			PyErr_SetString(PyExc_TypeError,
					"argument 2 must be a mapping");
			return NULL;
		}
		return _escape_item(o,
			   ((_mysql_ConnectionObject *) self)->converter);
	}
}

static char _mysql_escape_sequence__doc__[] =
"escape_sequence(seq, dict) -- escape any special characters in sequence\n\
seq using mapping dict to provide quoting functions for each type.\n\
Returns a tuple of escaped items.";
static PyObject *
_mysql_escape_sequence(
	PyObject *self,
	PyObject *args)
{
	PyObject *o=NULL, *d=NULL, *r=NULL, *item, *quoted; 
	int i, n;
	if (!PyArg_ParseTuple(args, "OO:escape_sequence", &o, &d))
		goto error;
	if (!PyMapping_Check(d)) {
              PyErr_SetString(PyExc_TypeError,
                              "argument 2 must be a mapping");
              return NULL;
        }
	if ((n = PyObject_Length(o)) == -1) goto error;
	if (!(r = PyTuple_New(n))) goto error;
	for (i=0; i<n; i++) {
		item = PySequence_GetItem(o, i);
		if (!item) goto error;
		quoted = _escape_item(item, d);
		Py_DECREF(item);
		if (!quoted) goto error;
		PyTuple_SET_ITEM(r, i, quoted);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static char _mysql_escape_dict__doc__[] =
"escape_sequence(d, dict) -- escape any special characters in\n\
dictionary d using mapping dict to provide quoting functions for each type.\n\
Returns a dictionary of escaped items.";
static PyObject *
_mysql_escape_dict(
	PyObject *self,
	PyObject *args)
{
	PyObject *o=NULL, *d=NULL, *r=NULL, *item, *quoted, *pkey; 
	Py_ssize_t ppos = 0;
	if (!PyArg_ParseTuple(args, "O!O:escape_dict", &PyDict_Type, &o, &d))
		goto error;
	if (!PyMapping_Check(d)) {
		PyErr_SetString(PyExc_TypeError,
				"argument 2 must be a mapping");
		return NULL;
	}
	if (!(r = PyDict_New())) goto error;
	while (PyDict_Next(o, &ppos, &pkey, &item)) {
		quoted = _escape_item(item, d);
		if (!quoted) goto error;
		if (PyDict_SetItem(r, pkey, quoted)==-1) goto error;
		Py_DECREF(quoted);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static char _mysql_ResultObject_describe__doc__[] =
"Returns the sequence of 7-tuples required by the DB-API for\n\
the Cursor.description attribute.\n\
";

static PyObject *
_mysql_ResultObject_describe(
	_mysql_ResultObject *self,
	PyObject *noargs)
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	check_result_connection(self);
	n = mysql_num_fields(self->result);
	fields = mysql_fetch_fields(self->result);
	if (!(d = PyTuple_New(n))) return NULL;
	for (i=0; i<n; i++) {
		PyObject *t;
		t = Py_BuildValue("(siiiiii)",
				  fields[i].name,
				  (long) fields[i].type,
				  (long) fields[i].max_length,
				  (long) fields[i].length,
				  (long) fields[i].length,
				  (long) fields[i].decimals,
				  (long) !(IS_NOT_NULL(fields[i].flags)));
		if (!t) goto error;
		PyTuple_SET_ITEM(d, i, t);
	}
	return d;
  error:
	Py_XDECREF(d);
	return NULL;
}

static char _mysql_ResultObject_field_flags__doc__[] =
"Returns a tuple of field flags, one for each column in the result.\n\
" ;

static PyObject *
_mysql_ResultObject_field_flags(
	_mysql_ResultObject *self,
	PyObject *noargs)
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	check_result_connection(self);
	n = mysql_num_fields(self->result);
	fields = mysql_fetch_fields(self->result);
	if (!(d = PyTuple_New(n))) return NULL;
	for (i=0; i<n; i++) {
		PyObject *f;
		if (!(f = PyInt_FromLong((long)fields[i].flags))) goto error;
		PyTuple_SET_ITEM(d, i, f);
	}
	return d;
  error:
	Py_XDECREF(d);
	return NULL;
}

static PyObject *
_mysql_field_to_python(
	PyObject *converter,
	char *rowitem,
	unsigned long length,
	MYSQL_FIELD *field)
{
	PyObject *v;
#ifdef IS_PY3K
	int field_type = field->type;
	// Return bytes for binary and string types.
	int binary = 0;
	if (field_type == FIELD_TYPE_TINY_BLOB ||
		field_type == FIELD_TYPE_MEDIUM_BLOB ||
		field_type == FIELD_TYPE_LONG_BLOB ||
		field_type == FIELD_TYPE_BLOB ||
		field_type == FIELD_TYPE_VAR_STRING ||
		field_type == FIELD_TYPE_STRING ||
		field_type == FIELD_TYPE_GEOMETRY ||
		field_type == FIELD_TYPE_BIT) {
			binary = 1;
	}
#endif
	if (rowitem) {
		if (converter != Py_None) {
			v = PyObject_CallFunction(converter,
#ifdef IS_PY3K
						  binary ? "y#" : "s#",
#else
						  "s#",
#endif
						  rowitem,
						  (int)length);
		} else {
#ifdef IS_PY3K
			if (!binary) {
				v = PyUnicode_FromStringAndSize(rowitem, (int)length);
			} else
#endif
			v = PyBytes_FromStringAndSize(rowitem, (int)length);
		}
		if (!v)
			return NULL;
	} else {
		Py_INCREF(Py_None);
		v = Py_None;
	}
	return v;
}

static PyObject *
_mysql_row_to_tuple(
	_mysql_ResultObject *self,
	MYSQL_ROW row)
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r, *c;
	MYSQL_FIELD *fields;

	n = mysql_num_fields(self->result);
	if (!(r = PyTuple_New(n))) return NULL;
	length = mysql_fetch_lengths(self->result);
	fields = mysql_fetch_fields(self->result);
	for (i=0; i<n; i++) {
		PyObject *v;
		c = PyTuple_GET_ITEM(self->converter, i);
		v = _mysql_field_to_python(c, row[i], length[i], &fields[i]);
		if (!v) goto error;
		PyTuple_SET_ITEM(r, i, v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static PyObject *
_mysql_row_to_dict(
	_mysql_ResultObject *self,
	MYSQL_ROW row)
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r, *c;
	MYSQL_FIELD *fields;

	n = mysql_num_fields(self->result);
	if (!(r = PyDict_New())) return NULL;
	length = mysql_fetch_lengths(self->result);
	fields = mysql_fetch_fields(self->result);
	for (i=0; i<n; i++) {
		PyObject *v;
		c = PyTuple_GET_ITEM(self->converter, i);
		v = _mysql_field_to_python(c, row[i], length[i], &fields[i]);
		if (!v) goto error;
		if (!PyMapping_HasKeyString(r, fields[i].name)) {
			PyMapping_SetItemString(r, fields[i].name, v);
		} else {
			int len;
			char buf[256];
			strncpy(buf, fields[i].table, 256);
			len = strlen(buf);
			strncat(buf, ".", 256-len);
			len = strlen(buf);
			strncat(buf, fields[i].name, 256-len);
			PyMapping_SetItemString(r, buf, v);
		}
		Py_DECREF(v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static PyObject *
_mysql_row_to_dict_old(
	_mysql_ResultObject *self,
	MYSQL_ROW row)
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r, *c;
        MYSQL_FIELD *fields;

	n = mysql_num_fields(self->result);
	if (!(r = PyDict_New())) return NULL;
	length = mysql_fetch_lengths(self->result);
	fields = mysql_fetch_fields(self->result);
	for (i=0; i<n; i++) {
		PyObject *v;
		c = PyTuple_GET_ITEM(self->converter, i);
		v = _mysql_field_to_python(c, row[i], length[i], &fields[i]);
		if (!v) goto error;
		{
			int len=0;
			char buf[256]="";
			if (strlen(fields[i].table)) {
				strncpy(buf, fields[i].table, 256);
				len = strlen(buf);
				strncat(buf, ".", 256-len);
				len = strlen(buf);
			}
			strncat(buf, fields[i].name, 256-len);
			PyMapping_SetItemString(r, buf, v);
		}
		Py_DECREF(v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

typedef PyObject *_PYFUNC(_mysql_ResultObject *, MYSQL_ROW);

int
_mysql__fetch_row(
	_mysql_ResultObject *self,
	PyObject **r,
	int skiprows,
	int maxrows,
	_PYFUNC *convert_row)
{
	int i;
	MYSQL_ROW row;

	for (i = skiprows; i<(skiprows+maxrows); i++) {
		PyObject *v;
		if (!self->use)
			row = mysql_fetch_row(self->result);
		else {
			Py_BEGIN_ALLOW_THREADS;
			row = mysql_fetch_row(self->result);
			Py_END_ALLOW_THREADS;
		}
		if (!row && mysql_errno(&(((_mysql_ConnectionObject *)(self->conn))->connection))) {
			_mysql_Exception((_mysql_ConnectionObject *)self->conn);
			goto error;
		}
		if (!row) {
			if (_PyTuple_Resize(r, i) == -1) goto error;
			break;
		}
		v = convert_row(self, row);
		if (!v) goto error;
		PyTuple_SET_ITEM(*r, i, v);
	}
	return i-skiprows;
  error:
	return -1;
}

static char _mysql_ResultObject_fetch_row__doc__[] =
"fetch_row([maxrows, how]) -- Fetches up to maxrows as a tuple.\n\
The rows are formatted according to how:\n\
\n\
    0 -- tuples (default)\n\
    1 -- dictionaries, key=column or table.column if duplicated\n\
    2 -- dictionaries, key=table.column\n\
";

static PyObject *
_mysql_ResultObject_fetch_row(
	_mysql_ResultObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	typedef PyObject *_PYFUNC(_mysql_ResultObject *, MYSQL_ROW);
	static char *kwlist[] = { "maxrows", "how", NULL };
	static _PYFUNC *row_converters[] =
	{
		_mysql_row_to_tuple,
		_mysql_row_to_dict,
		_mysql_row_to_dict_old
	};
	_PYFUNC *convert_row;
	int maxrows=1, how=0, skiprows=0, rowsadded;
	PyObject *r=NULL;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii:fetch_row", kwlist,
					 &maxrows, &how))
		return NULL;
	check_result_connection(self);
	if (how >= (int)sizeof(row_converters)) {
		PyErr_SetString(PyExc_ValueError, "how out of range");
		return NULL;
	}
	convert_row = row_converters[how];
	if (maxrows) {
		if (!(r = PyTuple_New(maxrows))) goto error;
		rowsadded = _mysql__fetch_row(self, &r, skiprows, maxrows, 
				convert_row);
		if (rowsadded == -1) goto error;
	} else {
		if (self->use) {
			maxrows = 1000;
			if (!(r = PyTuple_New(maxrows))) goto error;
			while (1) {
				rowsadded = _mysql__fetch_row(self, &r, skiprows,
						maxrows, convert_row);
				if (rowsadded == -1) goto error;
				skiprows += rowsadded;
				if (rowsadded < maxrows) break;
				if (_PyTuple_Resize(&r, skiprows+maxrows) == -1)
				        goto error;
			}
		} else {
			/* XXX if overflow, maxrows<0? */
			maxrows = (int) mysql_num_rows(self->result);
			if (!(r = PyTuple_New(maxrows))) goto error;
			rowsadded = _mysql__fetch_row(self, &r, 0,
					maxrows, convert_row);
			if (rowsadded == -1) goto error;
		}
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static char _mysql_ConnectionObject_change_user__doc__[] =
"Changes the user and causes the database specified by db to\n\
become the default (current) database on the connection\n\
specified by mysql. In subsequent queries, this database is\n\
the default for table references that do not include an\n\
explicit database specifier.\n\
\n\
This function was introduced in MySQL Version 3.23.3.\n\
\n\
Fails unless the connected user can be authenticated or if he\n\
doesn't have permission to use the database. In this case the\n\
user and database are not changed.\n\
\n\
The db parameter may be set to None if you don't want to have\n\
a default database.\n\
";

static PyObject *
_mysql_ConnectionObject_change_user(
	_mysql_ConnectionObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	char *user, *pwd=NULL, *db=NULL;
	int r;
        static char *kwlist[] = { "user", "passwd", "db", NULL } ;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|ss:change_user",
					 kwlist, &user, &pwd, &db))
		return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
		r = mysql_change_user(&(self->connection), user, pwd, db);
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_character_set_name__doc__[] =
"Returns the default character set for the current connection.\n\
Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_character_set_name(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	const char *s;
	check_connection(self);
	s = mysql_character_set_name(&(self->connection));
	return PyString_FromString(s);
}

static char _mysql_ConnectionObject_set_character_set__doc__[] =
"Sets the default character set for the current connection.\n\
Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_set_character_set(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	const char *s;
	int err;
	if (!PyArg_ParseTuple(args, "s", &s)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	err = mysql_set_character_set(&(self->connection), s);
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

#if MYSQL_VERSION_ID >= 50010
static char _mysql_ConnectionObject_get_character_set_info__doc__[] =
"Returns a dict with information about the current character set:\n\
\n\
collation\n\
    collation name\n\
name\n\
    character set name\n\
comment\n\
    comment or descriptive name\n\
dir\n\
    character set directory\n\
mbminlen\n\
    min. length for multibyte string\n\
mbmaxlen\n\
    max. length for multibyte string\n\
\n\
Not all keys may be present, particularly dir.\n\
\n\
Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_get_character_set_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	PyObject *result;
	MY_CHARSET_INFO cs;

	check_connection(self);
	mysql_get_character_set_info(&(self->connection), &cs);
	if (!(result = PyDict_New())) return NULL;
	if (cs.csname)
		PyDict_SetItemString(result, "name", PyString_FromString(cs.csname));
	if (cs.name)
		PyDict_SetItemString(result, "collation", PyString_FromString(cs.name));
	if (cs.comment)
		PyDict_SetItemString(result, "comment", PyString_FromString(cs.comment));
	if (cs.dir)
		PyDict_SetItemString(result, "dir", PyString_FromString(cs.dir));
	PyDict_SetItemString(result, "mbminlen", PyInt_FromLong(cs.mbminlen));
	PyDict_SetItemString(result, "mbmaxlen", PyInt_FromLong(cs.mbmaxlen));
	return result;
}
#endif

static char _mysql_get_client_info__doc__[] =
"get_client_info() -- Returns a string that represents\n\
the client library version.";
static PyObject *
_mysql_get_client_info(
	PyObject *self,
	PyObject *noargs)
{
	check_server_init(NULL);
	return PyString_FromString(mysql_get_client_info());
}

static char _mysql_ConnectionObject_get_host_info__doc__[] =
"Returns a string that represents the MySQL client library\n\
version. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_get_host_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyString_FromString(mysql_get_host_info(&(self->connection)));
}

static char _mysql_ConnectionObject_get_proto_info__doc__[] =
"Returns an unsigned integer representing the protocol version\n\
used by the current connection. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_get_proto_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyInt_FromLong((long)mysql_get_proto_info(&(self->connection)));
}

static char _mysql_ConnectionObject_get_server_info__doc__[] =
"Returns a string that represents the server version number.\n\
Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_get_server_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyString_FromString(mysql_get_server_info(&(self->connection)));
}

static char _mysql_ConnectionObject_info__doc__[] =
"Retrieves a string providing information about the most\n\
recently executed query. Non-standard. Use messages or\n\
Cursor.messages.\n\
";

static PyObject *
_mysql_ConnectionObject_info(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	const char *s;
	check_connection(self);
	s = mysql_info(&(self->connection));
	if (s) return PyString_FromString(s);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_insert_id__doc__[] =
"Returns the ID generated for an AUTO_INCREMENT column by the previous\n\
query. Use this function after you have performed an INSERT query into a\n\
table that contains an AUTO_INCREMENT field.\n\
\n\
Note that this returns 0 if the previous query does not\n\
generate an AUTO_INCREMENT value. If you need to save the value for\n\
later, be sure to call this immediately after the query\n\
that generates the value.\n\
\n\
The ID is updated after INSERT and UPDATE statements that generate\n\
an AUTO_INCREMENT value or that set a column value to\n\
LAST_INSERT_ID(expr). See section 6.3.5.2 Miscellaneous Functions\n\
in the MySQL documentation.\n\
\n\
Also note that the value of the SQL LAST_INSERT_ID() function always\n\
contains the most recently generated AUTO_INCREMENT value, and is not\n\
reset between queries because the value of that function is maintained\n\
in the server.\n\
" ;

static PyObject *
_mysql_ConnectionObject_insert_id(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	my_ulonglong r;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyLong_FromUnsignedLongLong(r);
}

static char _mysql_ConnectionObject_kill__doc__[] =
"Asks the server to kill the thread specified by pid.\n\
Non-standard.";

static PyObject *
_mysql_ConnectionObject_kill(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	unsigned long pid;
	int r;
	if (!PyArg_ParseTuple(args, "k:kill", &pid)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_kill(&(self->connection), pid);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_field_count__doc__[] =
"Returns the number of columns for the most recent query on the\n\
connection. Non-standard. Will probably give you bogus results\n\
on most cursor classes. Use Cursor.rowcount.\n\
";

static PyObject *
_mysql_ConnectionObject_field_count(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	check_connection(self);
	return PyInt_FromLong((long)mysql_field_count(&(self->connection)));
}	

static char _mysql_ResultObject_num_fields__doc__[] =
"Returns the number of fields (column) in the result." ;

static PyObject *
_mysql_ResultObject_num_fields(
	_mysql_ResultObject *self,
	PyObject *noargs)
{
	check_result_connection(self);
	return PyInt_FromLong((long)mysql_num_fields(self->result));
}	

static char _mysql_ResultObject_num_rows__doc__[] =
"Returns the number of rows in the result set. Note that if\n\
use=1, this will not return a valid value until the entire result\n\
set has been read.\n\
";

static PyObject *
_mysql_ResultObject_num_rows(
	_mysql_ResultObject *self,
	PyObject *noargs)
{
	check_result_connection(self);
	return PyLong_FromUnsignedLongLong(mysql_num_rows(self->result));
}	

static char _mysql_ConnectionObject_ping__doc__[] =
"Checks whether or not the connection to the server is\n\
working. If it has gone down, an automatic reconnection is\n\
attempted.\n\
\n\
This function can be used by clients that remain idle for a\n\
long while, to check whether or not the server has closed the\n\
connection and reconnect if necessary.\n\
\n\
New in 1.2.2: Accepts an optional reconnect parameter. If True,\n\
then the client will attempt reconnection. Note that this setting\n\
is persistent. By default, this is on in MySQL<5.0.3, and off\n\
thereafter.\n\
\n\
Non-standard. You should assume that ping() performs an\n\
implicit rollback; use only when starting a new transaction.\n\
You have been warned.\n\
";

static PyObject *
_mysql_ConnectionObject_ping(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int r, reconnect = -1;
	if (!PyArg_ParseTuple(args, "|I", &reconnect)) return NULL;
	check_connection(self);
	if (reconnect != -1) {
		my_bool recon = reconnect;
		mysql_options(&self->connection, MYSQL_OPT_RECONNECT, &recon);
	}
	Py_BEGIN_ALLOW_THREADS
	r = mysql_ping(&(self->connection));
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_query__doc__[] =
"Execute a query. store_result() or use_result() will get the\n\
result set, if any. Non-standard. Use cursor() to create a cursor,\n\
then cursor.execute().\n\
" ;

static PyObject *
_mysql_ConnectionObject_query(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	char *query;
	int len, r;
	if (!PyArg_ParseTuple(args, "s#:query", &query, &len)) return NULL;
	check_connection(self);

	Py_BEGIN_ALLOW_THREADS
	r = mysql_real_query(&(self->connection), query, len);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}


static char _mysql_ConnectionObject_send_query__doc__[] =
"Send a query. Same to query() except not wait response.\n\n\
Use read_query_result() before calling store_result() or use_result()\n";

static PyObject *
_mysql_ConnectionObject_send_query(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	char *query;
	int len, r;
	MYSQL *mysql = &(self->connection);
	if (!PyArg_ParseTuple(args, "s#:query", &query, &len)) return NULL;
	check_connection(self);

	Py_BEGIN_ALLOW_THREADS
	r = mysql_send_query(mysql, query, len);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}


static char _mysql_ConnectionObject_read_query_result__doc__[] =
"Read result of query sent by send_query().\n";

static PyObject *
_mysql_ConnectionObject_read_query_result(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int r;
	MYSQL *mysql = &(self->connection);
	check_connection(self);

	Py_BEGIN_ALLOW_THREADS
	r = (int)mysql_read_query_result(mysql);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_select_db__doc__[] =
"Causes the database specified by db to become the default\n\
(current) database on the connection specified by mysql. In subsequent\n\
queries, this database is the default for table references that do not\n\
include an explicit database specifier.\n\
\n\
Fails unless the connected user can be authenticated as having\n\
permission to use the database.\n\
\n\
Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_select_db(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	char *db;
	int r;
	if (!PyArg_ParseTuple(args, "s:select_db", &db)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_select_db(&(self->connection), db);
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_shutdown__doc__[] =
"Asks the database server to shut down. The connected user must\n\
have shutdown privileges. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_shutdown(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	int r;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_shutdown(&(self->connection), SHUTDOWN_DEFAULT);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ConnectionObject_stat__doc__[] =
"Returns a character string containing information similar to\n\
that provided by the mysqladmin status command. This includes\n\
uptime in seconds and the number of running threads,\n\
questions, reloads, and open tables. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_stat(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	const char *s;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	s = mysql_stat(&(self->connection));
	Py_END_ALLOW_THREADS
	if (!s) return _mysql_Exception(self);
	return PyString_FromString(s);
}

static char _mysql_ConnectionObject_store_result__doc__[] =
"Returns a result object acquired by mysql_store_result\n\
(results stored in the client). If no results are available,\n\
None is returned. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_store_result(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	PyObject *arglist=NULL, *kwarglist=NULL, *result=NULL;
	_mysql_ResultObject *r=NULL;

	check_connection(self);
	arglist = Py_BuildValue("(OiO)", self, 0, self->converter);
	if (!arglist) goto error;
	kwarglist = PyDict_New();
	if (!kwarglist) goto error;
	r = MyAlloc(_mysql_ResultObject, _mysql_ResultObject_Type);
	if (!r) goto error;
	if (_mysql_ResultObject_Initialize(r, arglist, kwarglist))
		goto error;
	result = (PyObject *) r;
	if (!(r->result)) {
		Py_DECREF(result);
		Py_INCREF(Py_None);
		result = Py_None;
	}
  error:
	Py_XDECREF(arglist);
	Py_XDECREF(kwarglist);
	return result;
}

static char _mysql_ConnectionObject_thread_id__doc__[] =
"Returns the thread ID of the current connection. This value\n\
can be used as an argument to kill() to kill the thread.\n\
\n\
If the connection is lost and you reconnect with ping(), the\n\
thread ID will change. This means you should not get the\n\
thread ID and store it for later. You should get it when you\n\
need it.\n\
\n\
Non-standard.";

static PyObject *
_mysql_ConnectionObject_thread_id(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	unsigned long pid;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	pid = mysql_thread_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyInt_FromLong((long)pid);
}

static char _mysql_ConnectionObject_use_result__doc__[] =
"Returns a result object acquired by mysql_use_result\n\
(results stored in the server). If no results are available,\n\
None is returned. Non-standard.\n\
";

static PyObject *
_mysql_ConnectionObject_use_result(
	_mysql_ConnectionObject *self,
	PyObject *noargs)
{
	PyObject *arglist=NULL, *kwarglist=NULL, *result=NULL;
	_mysql_ResultObject *r=NULL;

	check_connection(self);
	arglist = Py_BuildValue("(OiO)", self, 1, self->converter);
	if (!arglist) return NULL;
	kwarglist = PyDict_New();
	if (!kwarglist) goto error;
	r = MyAlloc(_mysql_ResultObject, _mysql_ResultObject_Type);
	if (!r) goto error;
	result = (PyObject *) r;
	if (_mysql_ResultObject_Initialize(r, arglist, kwarglist))
		goto error;
	if (!(r->result)) {
		Py_DECREF(result);
		Py_INCREF(Py_None);
		result = Py_None;
	}
  error:
	Py_DECREF(arglist);
	Py_XDECREF(kwarglist);
	return result;
}

static void
_mysql_ConnectionObject_dealloc(
	_mysql_ConnectionObject *self)
{
	PyObject_GC_UnTrack(self);
	if (self->open) {
		mysql_close(&(self->connection));
		self->open = 0;
	}
	Py_CLEAR(self->converter);
	MyFree(self);
}

static PyObject *
_mysql_ConnectionObject_repr(
	_mysql_ConnectionObject *self)
{
	char buf[300];
	if (self->open)
		sprintf(buf, "<_mysql.connection open to '%.256s' at %lx>",
			self->connection.host,
			(long)self);
	else
		sprintf(buf, "<_mysql.connection closed at %lx>",
			(long)self);
	return PyString_FromString(buf);
}

static char _mysql_ResultObject_data_seek__doc__[] =
"data_seek(n) -- seek to row n of result set";
static PyObject *
_mysql_ResultObject_data_seek(
     _mysql_ResultObject *self,
     PyObject *args)
{
	unsigned int row;
	if (!PyArg_ParseTuple(args, "i:data_seek", &row)) return NULL;
	check_result_connection(self);
	mysql_data_seek(self->result, row);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ResultObject_row_seek__doc__[] =
"row_seek(n) -- seek by offset n rows of result set";
static PyObject *
_mysql_ResultObject_row_seek(
     _mysql_ResultObject *self,
     PyObject *args)
{
	int offset;
        MYSQL_ROW_OFFSET r;
	if (!PyArg_ParseTuple(args, "i:row_seek", &offset)) return NULL;
	check_result_connection(self);
	if (self->use) {
		PyErr_SetString(_mysql_ProgrammingError,
				"cannot be used with connection.use_result()");
		return NULL;
	}
	r = mysql_row_tell(self->result);
	mysql_row_seek(self->result, r+offset);
	Py_INCREF(Py_None);
	return Py_None;
}

static char _mysql_ResultObject_row_tell__doc__[] =
"row_tell() -- return the current row number of the result set.";
static PyObject *
_mysql_ResultObject_row_tell(
	_mysql_ResultObject *self,
	PyObject *noargs)
{
	MYSQL_ROW_OFFSET r;
	check_result_connection(self);
	if (self->use) {
		PyErr_SetString(_mysql_ProgrammingError,
				"cannot be used with connection.use_result()");
		return NULL;
	}
	r = mysql_row_tell(self->result);
	return PyInt_FromLong(r-self->result->data->data);
}

static void
_mysql_ResultObject_dealloc(
	_mysql_ResultObject *self)
{
	PyObject_GC_UnTrack((PyObject *)self);
	mysql_free_result(self->result);
	_mysql_ResultObject_clear(self);
	MyFree(self);
}

static PyObject *
_mysql_ResultObject_repr(
	_mysql_ResultObject *self)
{
	char buf[300];
	sprintf(buf, "<_mysql.result object at %lx>", (long)self);
	return PyString_FromString(buf);
}

static PyMethodDef _mysql_ConnectionObject_methods[] = {
	{
		"affected_rows",
		(PyCFunction)_mysql_ConnectionObject_affected_rows,
		METH_NOARGS,
		_mysql_ConnectionObject_affected_rows__doc__
	},
	{
		"autocommit",
		(PyCFunction)_mysql_ConnectionObject_autocommit,
		METH_VARARGS,
		_mysql_ConnectionObject_autocommit__doc__
	},
	{
		"get_autocommit",
		(PyCFunction)_mysql_ConnectionObject_get_autocommit,
		METH_NOARGS,
		_mysql_ConnectionObject_get_autocommit__doc__
	},
	{
		"commit",
		(PyCFunction)_mysql_ConnectionObject_commit,
		METH_NOARGS,
		_mysql_ConnectionObject_commit__doc__
	},
	{
		"rollback",
		(PyCFunction)_mysql_ConnectionObject_rollback,
		METH_NOARGS,
		_mysql_ConnectionObject_rollback__doc__
	},
	{
		"next_result",
		(PyCFunction)_mysql_ConnectionObject_next_result,
		METH_NOARGS,
		_mysql_ConnectionObject_next_result__doc__
	},
	{
		"set_server_option",
		(PyCFunction)_mysql_ConnectionObject_set_server_option,
		METH_VARARGS,
		_mysql_ConnectionObject_set_server_option__doc__
	},
	{
		"sqlstate",
		(PyCFunction)_mysql_ConnectionObject_sqlstate,
		METH_NOARGS,
		_mysql_ConnectionObject_sqlstate__doc__
	},
	{
		"warning_count",
		(PyCFunction)_mysql_ConnectionObject_warning_count,
		METH_NOARGS,
		_mysql_ConnectionObject_warning_count__doc__
	},
	{
		"change_user",
		(PyCFunction)_mysql_ConnectionObject_change_user,
		METH_VARARGS | METH_KEYWORDS,
		_mysql_ConnectionObject_change_user__doc__
	},
	{
		"character_set_name",
		(PyCFunction)_mysql_ConnectionObject_character_set_name,
		METH_NOARGS,
		_mysql_ConnectionObject_character_set_name__doc__
	},
	{
		"set_character_set",
		(PyCFunction)_mysql_ConnectionObject_set_character_set,
		METH_VARARGS,
		_mysql_ConnectionObject_set_character_set__doc__
	},
#if MYSQL_VERSION_ID >= 50010
	{
		"get_character_set_info",
		(PyCFunction)_mysql_ConnectionObject_get_character_set_info,
		METH_NOARGS,
		_mysql_ConnectionObject_get_character_set_info__doc__
	},
#endif
	{
		"close",
		(PyCFunction)_mysql_ConnectionObject_close,
		METH_NOARGS,
		_mysql_ConnectionObject_close__doc__
	},
	{
		"fileno",
		(PyCFunction)_mysql_ConnectionObject_fileno,
		METH_NOARGS,
		_mysql_ConnectionObject_fileno__doc__
	},
	{
		"dump_debug_info",
		(PyCFunction)_mysql_ConnectionObject_dump_debug_info,
		METH_NOARGS,
		_mysql_ConnectionObject_dump_debug_info__doc__
	},
	{
		"escape",
		(PyCFunction)_mysql_escape,
		METH_VARARGS,
		_mysql_escape__doc__
	},
	{
		"escape_string",
		(PyCFunction)_mysql_escape_string,
		METH_VARARGS,
		_mysql_escape_string__doc__
	},
	{
		"error",
		(PyCFunction)_mysql_ConnectionObject_error,
		METH_NOARGS,
		_mysql_ConnectionObject_error__doc__
	},
	{
		"errno",
		(PyCFunction)_mysql_ConnectionObject_errno,
		METH_NOARGS,
		_mysql_ConnectionObject_errno__doc__
	},
	{
		"field_count",
		(PyCFunction)_mysql_ConnectionObject_field_count,
		METH_NOARGS,
		_mysql_ConnectionObject_field_count__doc__
	}, 
	{
		"get_host_info",
		(PyCFunction)_mysql_ConnectionObject_get_host_info,
		METH_NOARGS,
		_mysql_ConnectionObject_get_host_info__doc__
	},
	{
		"get_proto_info",
		(PyCFunction)_mysql_ConnectionObject_get_proto_info,
		METH_NOARGS,
		_mysql_ConnectionObject_get_proto_info__doc__
	},
	{
		"get_server_info",
		(PyCFunction)_mysql_ConnectionObject_get_server_info,
		METH_NOARGS,
		_mysql_ConnectionObject_get_server_info__doc__
	},
	{
		"info",
		(PyCFunction)_mysql_ConnectionObject_info,
		METH_NOARGS,
		_mysql_ConnectionObject_info__doc__
	},
	{
		"insert_id",
		(PyCFunction)_mysql_ConnectionObject_insert_id,
		METH_NOARGS,
		_mysql_ConnectionObject_insert_id__doc__
	},
	{
		"kill",
		(PyCFunction)_mysql_ConnectionObject_kill,
		METH_VARARGS,
		_mysql_ConnectionObject_kill__doc__
	},
	{
		"ping",
		(PyCFunction)_mysql_ConnectionObject_ping,
		METH_VARARGS,
		_mysql_ConnectionObject_ping__doc__
	},
	{
		"query",
		(PyCFunction)_mysql_ConnectionObject_query,
		METH_VARARGS,
		_mysql_ConnectionObject_query__doc__
	},
	{
		"send_query",
		(PyCFunction)_mysql_ConnectionObject_send_query,
		METH_VARARGS,
		_mysql_ConnectionObject_send_query__doc__,
	},
	{
		"read_query_result",
		(PyCFunction)_mysql_ConnectionObject_read_query_result,
		METH_NOARGS,
		_mysql_ConnectionObject_read_query_result__doc__,
	},
	{
		"select_db",
		(PyCFunction)_mysql_ConnectionObject_select_db,
		METH_VARARGS,
		_mysql_ConnectionObject_select_db__doc__
	},
	{
		"shutdown",
		(PyCFunction)_mysql_ConnectionObject_shutdown,
		METH_NOARGS,
		_mysql_ConnectionObject_shutdown__doc__
	},
	{
		"stat",
		(PyCFunction)_mysql_ConnectionObject_stat,
		METH_NOARGS,
		_mysql_ConnectionObject_stat__doc__
	},
	{
		"store_result",
		(PyCFunction)_mysql_ConnectionObject_store_result,
		METH_NOARGS,
		_mysql_ConnectionObject_store_result__doc__
	},
	{
		"string_literal",
		(PyCFunction)_mysql_string_literal,
		METH_VARARGS,
		_mysql_string_literal__doc__},
	{
		"thread_id",
		(PyCFunction)_mysql_ConnectionObject_thread_id,
		METH_NOARGS,
		_mysql_ConnectionObject_thread_id__doc__
	},
	{
		"use_result",
		(PyCFunction)_mysql_ConnectionObject_use_result,
		METH_NOARGS,
		_mysql_ConnectionObject_use_result__doc__
	},
	{NULL,              NULL} /* sentinel */
};

static struct PyMemberDef _mysql_ConnectionObject_memberlist[] = {
	{
		"open",
		T_INT,
		offsetof(_mysql_ConnectionObject,open),
		READONLY,
		"True if connection is open"
	},
	{
		"converter",
		T_OBJECT,
		offsetof(_mysql_ConnectionObject,converter),
		0,
		"Type conversion mapping"
	},
	{
		"server_capabilities",
		T_UINT,
		offsetof(_mysql_ConnectionObject,connection.server_capabilities),
		READONLY,
		"Capabilities of server; consult MySQLdb.constants.CLIENT"
	},
	{
		"port",
		T_UINT,
		offsetof(_mysql_ConnectionObject,connection.port),
		READONLY,
		"TCP/IP port of the server connection"
	},
	{
		"client_flag",
		T_UINT,
		READONLY,
		offsetof(_mysql_ConnectionObject,connection.client_flag),
		"Client flags; refer to MySQLdb.constants.CLIENT"
	},
	{NULL} /* Sentinel */
};

static PyMethodDef _mysql_ResultObject_methods[] = {
	{
		"data_seek",
		(PyCFunction)_mysql_ResultObject_data_seek,
		METH_VARARGS,
		_mysql_ResultObject_data_seek__doc__
	},
	{
		"row_seek",
		(PyCFunction)_mysql_ResultObject_row_seek,
		METH_VARARGS,
		_mysql_ResultObject_row_seek__doc__
	},
	{
		"row_tell",
		(PyCFunction)_mysql_ResultObject_row_tell,
		METH_NOARGS,
		_mysql_ResultObject_row_tell__doc__
	},
	{
		"describe",
		(PyCFunction)_mysql_ResultObject_describe,
		METH_NOARGS,
		_mysql_ResultObject_describe__doc__
	},
	{
		"fetch_row",
		(PyCFunction)_mysql_ResultObject_fetch_row,
		METH_VARARGS | METH_KEYWORDS,
		_mysql_ResultObject_fetch_row__doc__
	},
	{
		"field_flags",
		(PyCFunction)_mysql_ResultObject_field_flags,
		METH_NOARGS,
		_mysql_ResultObject_field_flags__doc__
	},
	{
		"num_fields",
		(PyCFunction)_mysql_ResultObject_num_fields,
		METH_NOARGS,
		_mysql_ResultObject_num_fields__doc__
	},
	{
		"num_rows",
		(PyCFunction)_mysql_ResultObject_num_rows,
		METH_NOARGS,
		_mysql_ResultObject_num_rows__doc__
	},
	{NULL,              NULL} /* sentinel */
};

static struct PyMemberDef _mysql_ResultObject_memberlist[] = {
	{
		"converter",
		T_OBJECT,
		offsetof(_mysql_ResultObject,converter),
		READONLY,
		"Type conversion mapping"
	},
	{
		"has_next",
		T_BOOL,
		offsetof(_mysql_ResultObject, has_next),
		READONLY,
		"Has next result"
	},
	{NULL} /* Sentinel */
};

static PyObject *
_mysql_ConnectionObject_getattro(
	_mysql_ConnectionObject *self,
	PyObject *name)
{
	char *cname;
#ifdef IS_PY3K
	cname = PyUnicode_AsUTF8(name);
#else
	cname = PyString_AsString(name);
#endif
	if (strcmp(cname, "closed") == 0)
		return PyInt_FromLong((long)!(self->open));

	return PyObject_GenericGetAttr((PyObject *)self, name);
}

static int
_mysql_ConnectionObject_setattro(
	_mysql_ConnectionObject *self,
	PyObject *name,
	PyObject *v)
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError,
				"can't delete connection attributes");
		return -1;
	}
	return PyObject_GenericSetAttr((PyObject *)self, name, v);
}

static int
_mysql_ResultObject_setattro(
	_mysql_ResultObject *self,
	PyObject *name,
	PyObject *v)
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError,
				"can't delete connection attributes");
		return -1;
	}
	return PyObject_GenericSetAttr((PyObject *)self, name, v);
}

PyTypeObject _mysql_ConnectionObject_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
	"_mysql.connection", /* (char *)tp_name For printing */
	sizeof(_mysql_ConnectionObject),
	0,
	(destructor)_mysql_ConnectionObject_dealloc, /* tp_dealloc */
	0, /*tp_print*/
	0, /* tp_getattr */
	0, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_ConnectionObject_repr, /* tp_repr */

	/* Method suites for standard classes */

	0, /* (PyNumberMethods *) tp_as_number */
	0, /* (PySequenceMethods *) tp_as_sequence */
	0, /* (PyMappingMethods *) tp_as_mapping */

	/* More standard operations (here for binary compatibility) */

	0, /* (hashfunc) tp_hash */
	0, /* (ternaryfunc) tp_call */
	0, /* (reprfunc) tp_str */
	(getattrofunc)_mysql_ConnectionObject_getattro, /* tp_getattro */
	(setattrofunc)_mysql_ConnectionObject_setattro, /* tp_setattro */

	/* Functions to access object as input/output buffer */
	0, /* (PyBufferProcs *) tp_as_buffer */

	/* (tp_flags) Flags to define presence of optional/expanded features */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE,
	_mysql_connect__doc__, /* (char *) tp_doc Documentation string */

	/* call function for all accessible objects */
	(traverseproc) _mysql_ConnectionObject_traverse, /* tp_traverse */

	/* delete references to contained objects */
	(inquiry) _mysql_ConnectionObject_clear, /* tp_clear */

	/* rich comparisons */
	0, /* (richcmpfunc) tp_richcompare */

	/* weak reference enabler */
	0, /* (long) tp_weaklistoffset */

	/* Iterators */
	0, /* (getiterfunc) tp_iter */
	0, /* (iternextfunc) tp_iternext */

	/* Attribute descriptor and subclassing stuff */
	(struct PyMethodDef *)_mysql_ConnectionObject_methods, /* tp_methods */
	(struct PyMemberDef *)_mysql_ConnectionObject_memberlist, /* tp_members */
	0, /* (struct getsetlist *) tp_getset; */
	0, /* (struct _typeobject *) tp_base; */
	0, /* (PyObject *) tp_dict */
	0, /* (descrgetfunc) tp_descr_get */
	0, /* (descrsetfunc) tp_descr_set */
	0, /* (long) tp_dictoffset */
	(initproc)_mysql_ConnectionObject_Initialize, /* tp_init */
	NULL, /* tp_alloc */
	NULL, /* tp_new */
	NULL, /* tp_free Low-level free-memory routine */ 
	0, /* (PyObject *) tp_bases */
	0, /* (PyObject *) tp_mro method resolution order */
	0, /* (PyObject *) tp_defined */
} ;

PyTypeObject _mysql_ResultObject_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
	"_mysql.result",
	sizeof(_mysql_ResultObject),
	0,
	(destructor)_mysql_ResultObject_dealloc, /* tp_dealloc */
	0, /*tp_print*/
	0, /* tp_getattr */
	0, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_ResultObject_repr, /* tp_repr */

	/* Method suites for standard classes */

	0, /* (PyNumberMethods *) tp_as_number */
	0, /* (PySequenceMethods *) tp_as_sequence */
	0, /* (PyMappingMethods *) tp_as_mapping */

	/* More standard operations (here for binary compatibility) */

	0, /* (hashfunc) tp_hash */
	0, /* (ternaryfunc) tp_call */
	0, /* (reprfunc) tp_str */
	(getattrofunc)PyObject_GenericGetAttr, /* tp_getattro */
	(setattrofunc)_mysql_ResultObject_setattro, /* tp_setattr */

	/* Functions to access object as input/output buffer */
	0, /* (PyBufferProcs *) tp_as_buffer */

	/* Flags to define presence of optional/expanded features */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE,

	_mysql_ResultObject__doc__, /* (char *) tp_doc Documentation string */

	/* call function for all accessible objects */
	(traverseproc) _mysql_ResultObject_traverse, /* tp_traverse */

	/* delete references to contained objects */
	(inquiry) _mysql_ResultObject_clear, /* tp_clear */

	/* rich comparisons */
	0, /* (richcmpfunc) tp_richcompare */

	/* weak reference enabler */
	0, /* (long) tp_weaklistoffset */

	/* Iterators */
	0, /* (getiterfunc) tp_iter */
	0, /* (iternextfunc) tp_iternext */

	/* Attribute descriptor and subclassing stuff */
	(struct PyMethodDef *) _mysql_ResultObject_methods, /* tp_methods */
	(struct PyMemberDef *) _mysql_ResultObject_memberlist, /*tp_members */
	0, /* (struct getsetlist *) tp_getset; */
	0, /* (struct _typeobject *) tp_base; */
	0, /* (PyObject *) tp_dict */
	0, /* (descrgetfunc) tp_descr_get */
	0, /* (descrsetfunc) tp_descr_set */
	0, /* (long) tp_dictoffset */
	(initproc)_mysql_ResultObject_Initialize, /* tp_init */
	NULL, /* tp_alloc */
	NULL, /* tp_new */
	NULL, /* tp_free Low-level free-memory routine */
	0, /* (PyObject *) tp_bases */
	0, /* (PyObject *) tp_mro method resolution order */
	0, /* (PyObject *) tp_defined */
};

static PyMethodDef
_mysql_methods[] = {
	{ 
		"connect",
		(PyCFunction)_mysql_connect,
		METH_VARARGS | METH_KEYWORDS,
		_mysql_connect__doc__
	},
	{ 
		"debug",
		(PyCFunction)_mysql_debug, 
		METH_VARARGS,
		_mysql_debug__doc__
	},
	{
		"escape", 
		(PyCFunction)_mysql_escape, 
		METH_VARARGS,
		_mysql_escape__doc__
	},
	{
		// deprecated.
		"escape_sequence",
		(PyCFunction)_mysql_escape_sequence,
		METH_VARARGS,
		_mysql_escape_sequence__doc__
	},
	{
		// deprecated.
		"escape_dict",
		(PyCFunction)_mysql_escape_dict,
		METH_VARARGS,
		_mysql_escape_dict__doc__
	},
	{ 
		"escape_string",
		(PyCFunction)_mysql_escape_string,
		METH_VARARGS,
		_mysql_escape_string__doc__
	},
	{ 
		"string_literal",
		(PyCFunction)_mysql_string_literal,
		METH_VARARGS,
		_mysql_string_literal__doc__
	},
	{
		"get_client_info",
		(PyCFunction)_mysql_get_client_info,
		METH_NOARGS,
		_mysql_get_client_info__doc__
	},
	{
		"thread_safe",
		(PyCFunction)_mysql_thread_safe,
		METH_NOARGS,
		_mysql_thread_safe__doc__
	},
	{
		"server_init",
		(PyCFunction)_mysql_server_init,
		METH_VARARGS | METH_KEYWORDS,
		_mysql_server_init__doc__
	},
	{
		"server_end",
		(PyCFunction)_mysql_server_end,
		METH_VARARGS,
		_mysql_server_end__doc__
	},
	{NULL, NULL} /* sentinel */
};

static PyObject *
_mysql_NewException(
	PyObject *dict,
	PyObject *edict,
	char *name)
{
	PyObject *e;
	if (!(e = PyDict_GetItemString(edict, name)))
		return NULL;
	if (PyDict_SetItemString(dict, name, e))
		return NULL;
	Py_INCREF(e);
	return e;
}

#define QUOTE(X) _QUOTE(X)
#define _QUOTE(X) #X

static char _mysql___doc__[] =
"an adaptation of the MySQL C API (mostly)\n\
\n\
You probably are better off using MySQLdb instead of using this\n\
module directly.\n\
\n\
In general, renaming goes from mysql_* to _mysql.*. _mysql.connect()\n\
returns a connection object (MYSQL). Functions which expect MYSQL * as\n\
an argument are now methods of the connection object. A number of things\n\
return result objects (MYSQL_RES). Functions which expect MYSQL_RES * as\n\
an argument are now methods of the result object. Deprecated functions\n\
(as of 3.23) are NOT implemented.\n\
";

#ifdef IS_PY3K
static struct PyModuleDef _mysqlmodule = {
   PyModuleDef_HEAD_INIT,
   "_mysql",   /* name of module */
   _mysql___doc__, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   _mysql_methods
};

PyMODINIT_FUNC
PyInit__mysql(void)
#else
DL_EXPORT(void)
init_mysql(void)
#endif
{
	PyObject *dict, *module, *emod, *edict;

#ifndef IS_PY3K
	_mysql_ConnectionObject_Type.ob_type = &PyType_Type;
	_mysql_ResultObject_Type.ob_type = &PyType_Type;
#endif
#if PY_VERSION_HEX >= 0x02020000
	_mysql_ConnectionObject_Type.tp_alloc = PyType_GenericAlloc;
	_mysql_ConnectionObject_Type.tp_new = PyType_GenericNew;
	_mysql_ResultObject_Type.tp_alloc = PyType_GenericAlloc;
	_mysql_ResultObject_Type.tp_new = PyType_GenericNew;
#endif
#ifdef IS_PY3K
	if (PyType_Ready(&_mysql_ConnectionObject_Type) < 0)
		return NULL;
	if (PyType_Ready(&_mysql_ResultObject_Type) < 0)
		return NULL;

	module = PyModule_Create(&_mysqlmodule);
	if (!module) return module; /* this really should never happen */
#else
	_mysql_ConnectionObject_Type.tp_free = _PyObject_GC_Del;
	_mysql_ResultObject_Type.tp_free = _PyObject_GC_Del;
	module = Py_InitModule4("_mysql", _mysql_methods, _mysql___doc__,
				(PyObject *)NULL, PYTHON_API_VERSION);
	if (!module) return; /* this really should never happen */
#endif

	if (!(dict = PyModule_GetDict(module))) goto error;
	if (PyDict_SetItemString(dict, "version_info",
			       PyRun_String(QUOTE(version_info), Py_eval_input,
				       dict, dict)))
		goto error;
	if (PyDict_SetItemString(dict, "__version__",
			       PyString_FromString(QUOTE(__version__))))
		goto error;
	if (PyDict_SetItemString(dict, "connection",
			       (PyObject *)&_mysql_ConnectionObject_Type))
		goto error;
	Py_INCREF(&_mysql_ConnectionObject_Type);
	if (PyDict_SetItemString(dict, "result",
			       (PyObject *)&_mysql_ResultObject_Type))
		goto error;	
	Py_INCREF(&_mysql_ResultObject_Type);
	if (!(emod = PyImport_ImportModule("_mysql_exceptions"))) {
	    PyErr_Print();
		goto error;
	}
	if (!(edict = PyModule_GetDict(emod))) goto error;
	if (!(_mysql_MySQLError =
	      _mysql_NewException(dict, edict, "MySQLError")))
		goto error;
	if (!(_mysql_Warning =
	      _mysql_NewException(dict, edict, "Warning")))
		goto error;
	if (!(_mysql_Error =
	      _mysql_NewException(dict, edict, "Error")))
		goto error;
	if (!(_mysql_InterfaceError =
	      _mysql_NewException(dict, edict, "InterfaceError")))
		goto error;
	if (!(_mysql_DatabaseError =
	      _mysql_NewException(dict, edict, "DatabaseError")))
		goto error;
	if (!(_mysql_DataError =
	      _mysql_NewException(dict, edict, "DataError")))
		goto error;
	if (!(_mysql_OperationalError =
	      _mysql_NewException(dict, edict, "OperationalError")))
		goto error;
	if (!(_mysql_IntegrityError =
	      _mysql_NewException(dict, edict, "IntegrityError")))
		goto error;
	if (!(_mysql_InternalError =
	      _mysql_NewException(dict, edict, "InternalError")))
		goto error;
	if (!(_mysql_ProgrammingError =
	      _mysql_NewException(dict, edict, "ProgrammingError")))
		goto error;
	if (!(_mysql_NotSupportedError =
	      _mysql_NewException(dict, edict, "NotSupportedError")))
		goto error;
	Py_DECREF(emod);
	if (!(_mysql_NULL = PyString_FromString("NULL")))
		goto error;
	if (PyDict_SetItemString(dict, "NULL", _mysql_NULL)) goto error;
  error:
	if (PyErr_Occurred()) {
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
		module = NULL;
    }
#ifdef IS_PY3K
    return module;
#endif
}
/* vim: set ts=4 sts=4 sw=4 noexpandtab : */
