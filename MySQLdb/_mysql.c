#define version_info "(0,9,1,'final',1)"
#define __version__ "0.9.1"
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

#include "Python.h"

#ifdef MS_WIN32
#include <windows.h>
#ifndef uint
#define uint unsigned int
#endif
#endif /* MS_WIN32 */

#include "structmember.h"
#include "mysql.h"
#include "mysqld_error.h"
#include "errmsg.h"

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

#define check_connection(c) if (!(c->open)) _mysql_Exception(c)
#define result_connection(r) ((_mysql_ConnectionObject *)r->conn)
#define check_result_connection(r) if (!(result_connection(r)->open)) _mysql_Exception(result_connection(r))

extern PyTypeObject _mysql_ConnectionObject_Type;

typedef struct {
	PyObject_HEAD
	PyObject *conn;
	MYSQL_RES *result;
	int nfields;
	int use;
	PyObject *converter;
} _mysql_ResultObject;

extern PyTypeObject _mysql_ResultObject_Type;

PyObject *
_mysql_Exception(_mysql_ConnectionObject *c)
{
	PyObject *t, *e;
	int merr;

	if (!(t = PyTuple_New(2))) return NULL;
	if (!(c->open)) {
		e = _mysql_InternalError;
		PyTuple_SET_ITEM(t, 0, PyInt_FromLong(-1L));
		PyTuple_SET_ITEM(t, 1, PyString_FromString("connection is closed"));
		PyErr_SetObject(e, t);
		Py_DECREF(t);
		return NULL;
	}
	merr = mysql_errno(&(c->connection));
	if (!merr)
		e = _mysql_InterfaceError;
	else if (merr > CR_MAX_ERROR) {
		PyTuple_SET_ITEM(t, 0, PyInt_FromLong(-1L));
		PyTuple_SET_ITEM(t, 1, PyString_FromString("error totally whack"));
		PyErr_SetObject(_mysql_InterfaceError, t);
		Py_DECREF(t);
		return NULL;
	}
	else switch (merr) {
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
	case ER_DUP_ENTRY:
#ifdef ER_DUP_UNIQUE
	case ER_DUP_UNIQUE:
#endif
#ifdef ER_PRIMARY_CANT_HAVE_NULL
	case ER_PRIMARY_CANT_HAVE_NULL:
#endif
		e = _mysql_IntegrityError;
		break;
#ifdef ER_WARNING_NOT_COMPLETE_ROLLBACK
	case ER_WARNING_NOT_COMPLETE_ROLLBACK:
		e = _mysql_NotSupportedError;
		break;
#endif
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


static _mysql_ResultObject*
_mysql_ResultObject_New(
	_mysql_ConnectionObject *conn,
	MYSQL_RES *result,
	int use,
	PyObject *conv)
{
	int n, i;
	MYSQL_FIELD *fields;
	_mysql_ResultObject *r;

	r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type);
	if (!r) return NULL;
	r->conn = (PyObject *) conn;
	r->use = use;
	r->result = result;
	n = mysql_num_fields(result);
	r->nfields = n;
	if (!(r->converter = PyTuple_New(n))) goto error;
	fields = mysql_fetch_fields(result);
	for (i=0; i<n; i++) {
		PyObject *tmp, *fun;
		tmp = PyInt_FromLong((long) fields[i].type);
		if (!tmp) goto error;
		fun = PyObject_GetItem(conv, tmp);
		Py_DECREF(tmp);
		if (!fun) {
			PyErr_Clear();
			fun = Py_None;
			Py_INCREF(Py_None);
		}
		PyTuple_SET_ITEM(r->converter, i, fun);
	}
	Py_INCREF(conn);
	return r;
  error:
	Py_DECREF(r);
	return NULL;
}

static char _mysql_connect__doc__[] =
"connect() -- returns a MYSQL connection object. Exclusive use of\n\
              keyword parameters strongly recommended. Consult the\n\
              MySQL C API documentation for more details.\n\
\n\
host -- string, host to connect to or NULL pointer (localhost)\n\
user -- string, user to connect as or NULL (your username)\n\
passwd -- string, password to use or NULL (no password)\n\
db -- string, database to use or NULL (no DB selected)\n\
port -- integer, TCP/IP port to connect to or default MySQL port\n\
unix_socket -- string, location of unix_socket to use or use TCP\n\
client_flags -- integer, flags to use or 0 (see MySQL docs)\n\
conv -- dictionary, maps MySQL FIELD_TYPE.* to Python functions which\n\
        convert a string to the appropriate Python type\n\
connect_time -- number of seconds to wait before the connection\n\
        attempt fails.\n\
compress -- if set, compression is enabled\n\
init_command -- command which is run once the connection is created\n\
read_default_file -- see the MySQL documentation for mysql_options()\n\
read_default_group -- see the MySQL documentation for mysql_options()\n\
";

static PyObject *
_mysql_connect(
	PyObject *self,
	PyObject *args,
	PyObject *kwargs)
{
	MYSQL *conn;
	PyObject *conv = NULL;
	char *host = NULL, *user = NULL, *passwd = NULL,
		*db = NULL, *unix_socket = NULL;
	uint port = MYSQL_PORT;
	uint client_flag = 0;
	static char *kwlist[] = { "host", "user", "passwd", "db", "port",
				  "unix_socket", "conv",
				  "connect_timeout", "compress",
				  "named_pipe", "init_command",
				  "read_default_file", "read_default_group",
				  NULL } ;
	int connect_timeout = 0;
	int compress = -1, named_pipe = -1;
	char *init_command=NULL,
	     *read_default_file=NULL,
	     *read_default_group=NULL;
	_mysql_ConnectionObject *c=NULL;
	
	c = PyObject_NEW(_mysql_ConnectionObject,
			 &_mysql_ConnectionObject_Type);
	if (c == NULL) return NULL;
	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ssssisOiiisss:connect",
					 kwlist,
					 &host, &user, &passwd, &db,
					 &port, &unix_socket, &conv,
					 &connect_timeout,
					 &compress, &named_pipe,
					 &init_command, &read_default_file,
					 &read_default_group))
		return NULL;

	if (!conv) 
		conv = PyDict_New();
#if PY_VERSION_HEX > 0x02000100
	else
		Py_INCREF(conv);
#endif
	c->converter = conv;
	if (!(c->converter)) {
		Py_DECREF(c);
		return NULL;
	}

	c->open = 1;
	Py_BEGIN_ALLOW_THREADS ;
	conn = mysql_init(&(c->connection));
	if (connect_timeout) {
		unsigned int timeout = connect_timeout;
		mysql_options(&(c->connection), MYSQL_OPT_CONNECT_TIMEOUT, 
				(char *)&timeout);
	}
	if (compress != -1) {
		mysql_options(&(c->connection), MYSQL_OPT_COMPRESS, 0);
		client_flag |= CLIENT_COMPRESS;
	}
	if (named_pipe != -1)
		mysql_options(&(c->connection), MYSQL_OPT_NAMED_PIPE, 0);
	if (init_command != NULL)
		mysql_options(&(c->connection), MYSQL_INIT_COMMAND, init_command);
	if (read_default_file != NULL)
		mysql_options(&(c->connection), MYSQL_READ_DEFAULT_FILE, read_default_file);
	if (read_default_group != NULL)
		mysql_options(&(c->connection), MYSQL_READ_DEFAULT_GROUP, read_default_group);
	conn = mysql_real_connect(&(c->connection), host, user, passwd, db,
				  port, unix_socket, client_flag);
	Py_END_ALLOW_THREADS ;

	if (!conn) {
		_mysql_Exception(c);
		c->open = 0;
		Py_DECREF(c);
		return NULL;
	}
	return (PyObject *) c;
}

static PyObject *
_mysql_ConnectionObject_close(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	if (self->open) {
		Py_BEGIN_ALLOW_THREADS
		mysql_close(&(self->connection));
		Py_END_ALLOW_THREADS
		self->open = 0;
	}
	Py_XDECREF(self->converter);
	self->converter = NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_affected_rows(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyLong_FromUnsignedLongLong(mysql_affected_rows(&(self->connection)));
}

static char _mysql_debug__doc__[] =
"debug(s) -- Does a DBUG_PUSH with the given string.\n\
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

static PyObject *
_mysql_ConnectionObject_dump_debug_info(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int err;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	err = mysql_dump_debug_info(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_errno(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyInt_FromLong((long)mysql_errno(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_error(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyString_FromString(mysql_error(&(self->connection)));
}

static char _mysql_escape_string__doc__[] =
"escape_string(s) -- quote any SQL-interpreted characters in string s.\n\
\n\
This function is somewhat deprecated. mysql_real_escape_string() was\n\
introduced in MySQL-3.23. The new version handles character sets\n\
correctly, but requires a connection object to work. Therefore,\n\
escape_string() has become a method of the connection object. It is\n\
retained as a module function for compatibility reasons. Use the\n\
method version of this function if at all possible.";
static PyObject *
_mysql_escape_string(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	PyObject *str;
	char *in, *out;
	int len, size;
	if (!PyArg_ParseTuple(args, "s#:escape_string", &in, &size)) return NULL;
	str = PyString_FromStringAndSize((char *) NULL, size*2+1);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
#if MYSQL_VERSION_ID < 32321
	len = mysql_escape_string(out, in, size);
#else
	if (self) {
		check_connection(self);
		len = mysql_real_escape_string(&(self->connection), out, in, size);
	}
	else
		len = mysql_escape_string(out, in, size);
#endif
	if (_PyString_Resize(&str, len) < 0) return NULL;
	return (str);
}

static char _mysql_string_literal__doc__[] =
"string_literal(obj) -- converts object obj into a SQL string literal.\n\
This means, any special SQL characters are escaped, and it is enclosed\n\
within single quotes. In other words, it performs:\n\
\n\
\"'%s'\" % escape_string(str(obj))\n\
\n\
This function is somewhat deprecated. mysql_real_escape_string() was\n\
introduced in MySQL-3.23. The new version handles character sets\n\
correctly, but requires a connection object to work. Therefore,\n\
string_literal() has become a method of the connection object. It is\n\
retained as a module function for compatibility reasons. Use the\n\
method version of this function if at all possible.";
static PyObject *
_mysql_string_literal(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	PyObject *str, *s, *o, *d;
	char *in, *out;
	int len, size;
	if (!PyArg_ParseTuple(args, "O|O:string_literal", &o, &d)) return NULL;
	s = PyObject_Str(o);
	if (!s) return NULL;
	in = PyString_AsString(s);
	size = PyString_GET_SIZE(s);
	str = PyString_FromStringAndSize((char *) NULL, size*2+3);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
#if MYSQL_VERSION_ID < 32321
	len = mysql_escape_string(out+1, in, size);
#else
	if (self) {
		check_connection(self);
		len = mysql_real_escape_string(&(self->connection), out+1, in, size);
	}
	else
		len = mysql_escape_string(out+1, in, size);
#endif
	*out = *(out+len+1) = '\'';
	if (_PyString_Resize(&str, len+2) < 0) return NULL;
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
				 (PyObject *) &PyString_Type);
	}
	if (!itemconv) {
		PyErr_SetString(PyExc_TypeError,
				"no default type converter defined");
		goto error;
	}
	quoted = PyObject_CallFunction(itemconv, "OO", item, d);
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
	int ppos = 0;
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
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}
				

static PyObject *
_mysql_ResultObject_describe(
	_mysql_ResultObject *self,
	PyObject *args)
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	if (!PyArg_NoArgs(args)) return NULL;
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
	
static PyObject *
_mysql_ResultObject_field_flags(
	_mysql_ResultObject *self,
	PyObject *args)
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	if (!PyArg_NoArgs(args)) return NULL;
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
	unsigned long length)
{
	PyObject *v;
	if (rowitem) {
		if (converter != Py_None)
			v = PyObject_CallFunction(converter,
						  "s#",
						  rowitem,
						  (int)length);
		else
			v = PyString_FromStringAndSize(rowitem,
						       (int)length);
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

	n = mysql_num_fields(self->result);
	if (!(r = PyTuple_New(n))) return NULL;
	length = mysql_fetch_lengths(self->result);
	for (i=0; i<n; i++) {
		PyObject *v;
		c = PyTuple_GET_ITEM(self->converter, i);
		v = _mysql_field_to_python(c, row[i], length[i]);
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
		v = _mysql_field_to_python(c, row[i], length[i]);
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
		v = _mysql_field_to_python(c, row[i], length[i]);
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
	unsigned int i;
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
#if PY_VERSION_HEX < 0x02020000
			if (_PyTuple_Resize(r, i, 0) == -1) goto error;
#else
			if (_PyTuple_Resize(r, i) == -1) goto error;
#endif
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
	unsigned int maxrows=1, how=0, skiprows=0, rowsadded;
	PyObject *r=NULL;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii:fetch_row", kwlist,
					 &maxrows, &how))
		return NULL;
	check_result_connection(self);
	if (how < 0 || how >= sizeof(row_converters)) {
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

#if MYSQL_VERSION_ID >= 32303
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
#endif

#if MYSQL_VERSION_ID >= 32321
static PyObject *
_mysql_ConnectionObject_character_set_name(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	const char *s;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	s = mysql_character_set_name(&(self->connection));
	return PyString_FromString(s);
}
#endif

static char _mysql_get_client_info__doc__[] =
"get_client_info() -- Returns a string that represents\n\
the client library version.";
static PyObject *
_mysql_get_client_info(
	PyObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_client_info());
}

static PyObject *
_mysql_ConnectionObject_get_host_info(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyString_FromString(mysql_get_host_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_proto_info(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyInt_FromLong((long)mysql_get_proto_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_server_info(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	return PyString_FromString(mysql_get_server_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_info(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	char *s;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	s = mysql_info(&(self->connection));
	if (s) return PyString_FromString(s);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_insert_id(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	my_ulonglong r;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyLong_FromUnsignedLongLong(r);
}

static PyObject *
_mysql_ConnectionObject_kill(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	unsigned long pid;
	int r;
	if (!PyArg_ParseTuple(args, "i:kill", &pid)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_kill(&(self->connection), pid);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_field_count(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
#if MYSQL_VERSION_ID < 32224
	return PyInt_FromLong((long)mysql_num_fields(&(self->connection)));
#else
	return PyInt_FromLong((long)mysql_field_count(&(self->connection)));
#endif
}	

static PyObject *
_mysql_ResultObject_num_fields(
	_mysql_ResultObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_result_connection(self);
	return PyInt_FromLong((long)mysql_num_fields(self->result));
}	

static PyObject *
_mysql_ResultObject_num_rows(
	_mysql_ResultObject *self,
	PyObject *args)
{
	if (!PyArg_NoArgs(args)) return NULL;
	check_result_connection(self);
	return PyLong_FromUnsignedLongLong(mysql_num_rows(self->result));
}	

static PyObject *
_mysql_ConnectionObject_ping(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int r;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_ping(&(self->connection));
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

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

static PyObject *
_mysql_ConnectionObject_shutdown(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	int r;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	r = mysql_shutdown(&(self->connection));
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_stat(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	char *s;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	s = mysql_stat(&(self->connection));
	Py_END_ALLOW_THREADS
	if (!s) return _mysql_Exception(self);
	return PyString_FromString(s);
}

static PyObject *
_mysql_ConnectionObject_store_result(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	MYSQL_RES *result;

	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
        result = mysql_store_result(&(self->connection));
	Py_END_ALLOW_THREADS
        if (!result) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	return (PyObject *) _mysql_ResultObject_New(self, result, 0,
						    self->converter);
}

static PyObject *
_mysql_ConnectionObject_thread_id(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	unsigned long pid;
	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
	pid = mysql_thread_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyInt_FromLong((long)pid);
}

static PyObject *
_mysql_ConnectionObject_use_result(
	_mysql_ConnectionObject *self,
	PyObject *args)
{
	MYSQL_RES *result;

	if (!PyArg_NoArgs(args)) return NULL;
	check_connection(self);
	Py_BEGIN_ALLOW_THREADS
        result = mysql_use_result(&(self->connection));
	Py_END_ALLOW_THREADS
        if (!result) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	return (PyObject *) _mysql_ResultObject_New(self, result, 1,
						    self->converter);
}

static void
_mysql_ConnectionObject_dealloc(
	_mysql_ConnectionObject *self)
{
	PyObject *o;

	if (self->open) {
		o = _mysql_ConnectionObject_close(self, NULL);
		Py_XDECREF(o);
	}
	PyMem_Free((char *) self);
}

static PyObject *
_mysql_ConnectionObject_repr(
	_mysql_ConnectionObject *self)
{
	char buf[300];
	if (self->open)
		sprintf(buf, "<open connection to '%.256s' at %lx>",
			self->connection.host,
			(long)self);
	else
		sprintf(buf, "<closed connection at %lx>",
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
	PyObject *args)
{
	MYSQL_ROW_OFFSET r;
	if (!PyArg_NoArgs(args)) return NULL;
	check_result_connection(self);
	r = mysql_row_tell(self->result);
	return PyInt_FromLong(r-self->result->data->data);
}

static void
_mysql_ResultObject_dealloc(
	_mysql_ResultObject *self)
{
	mysql_free_result(self->result);
	Py_DECREF(self->conn);
	Py_XDECREF(self->converter);
	PyMem_Free((char *) self);
}

static PyObject *
_mysql_ResultObject_repr(
	_mysql_ResultObject *self)
{
	char buf[300];
	sprintf(buf, "<result object at %lx>",
		(long)self);
	return PyString_FromString(buf);
}

static PyMethodDef _mysql_ConnectionObject_methods[] = {
	{"affected_rows",   (PyCFunction)_mysql_ConnectionObject_affected_rows, 0},
#if MYSQL_VERSION_ID >= 32303
	{"change_user",     (PyCFunction)_mysql_ConnectionObject_change_user, METH_VARARGS | METH_KEYWORDS},
#endif
#if MYSQL_VERSION_ID >= 32321
	{"character_set_name", (PyCFunction)_mysql_ConnectionObject_character_set_name, 0},
#endif
	{"close",           (PyCFunction)_mysql_ConnectionObject_close, 0},
	{"dump_debug_info", (PyCFunction)_mysql_ConnectionObject_dump_debug_info, 0},
	{"escape",          (PyCFunction)_mysql_escape, 1},
	{"escape_string",   (PyCFunction)_mysql_escape_string, 1},
	{"error",           (PyCFunction)_mysql_ConnectionObject_error, 0},
	{"errno",           (PyCFunction)_mysql_ConnectionObject_errno, 0},
	{"field_count",     (PyCFunction)_mysql_ConnectionObject_field_count, 0}, 
	{"get_host_info",   (PyCFunction)_mysql_ConnectionObject_get_host_info, 0},
	{"get_proto_info",  (PyCFunction)_mysql_ConnectionObject_get_proto_info, 0},
	{"get_server_info", (PyCFunction)_mysql_ConnectionObject_get_server_info, 0},
	{"info",            (PyCFunction)_mysql_ConnectionObject_info, 0},
	{"insert_id",       (PyCFunction)_mysql_ConnectionObject_insert_id, 0},
	{"kill",            (PyCFunction)_mysql_ConnectionObject_kill, 1},
	{"ping",            (PyCFunction)_mysql_ConnectionObject_ping, 0},
	{"query",           (PyCFunction)_mysql_ConnectionObject_query, 1},
	{"select_db",       (PyCFunction)_mysql_ConnectionObject_select_db, 1},
	{"shutdown",        (PyCFunction)_mysql_ConnectionObject_shutdown, 0},
	{"stat",            (PyCFunction)_mysql_ConnectionObject_stat, 0},
	{"store_result",    (PyCFunction)_mysql_ConnectionObject_store_result, 0},
	{"string_literal",  (PyCFunction)_mysql_string_literal, 1},
	{"thread_id",       (PyCFunction)_mysql_ConnectionObject_thread_id, 0},
	{"use_result",      (PyCFunction)_mysql_ConnectionObject_use_result, 0},
	{NULL,              NULL} /* sentinel */
};

static struct memberlist _mysql_ConnectionObject_memberlist[] = {
	{"open", T_INT, 0, RO},
	{"closed", T_INT, 0, RO},
	{"converter", T_OBJECT, offsetof(_mysql_ConnectionObject,converter)},
	{NULL} /* Sentinel */
};

static PyMethodDef _mysql_ResultObject_methods[] = {
	{"data_seek",       (PyCFunction)_mysql_ResultObject_data_seek,
	                    METH_VARARGS, _mysql_ResultObject_data_seek__doc__},
	{"row_seek",        (PyCFunction)_mysql_ResultObject_row_seek,
	                    METH_VARARGS, _mysql_ResultObject_row_seek__doc__},
	{"row_tell",        (PyCFunction)_mysql_ResultObject_row_tell,
	                    METH_VARARGS, _mysql_ResultObject_row_tell__doc__},
	{"describe",        (PyCFunction)_mysql_ResultObject_describe, 0},
	{"fetch_row",       (PyCFunction)_mysql_ResultObject_fetch_row, METH_VARARGS | METH_KEYWORDS},
	{"field_flags",     (PyCFunction)_mysql_ResultObject_field_flags, 0},
	{"num_fields",      (PyCFunction)_mysql_ResultObject_num_fields, 0},
	{"num_rows",        (PyCFunction)_mysql_ResultObject_num_rows, 0},
	{NULL,              NULL} /* sentinel */
};

static struct memberlist _mysql_ResultObject_memberlist[] = {
	{"converter", T_OBJECT, offsetof(_mysql_ResultObject,converter), RO},
	{NULL} /* Sentinel */
};

static PyObject *
_mysql_ConnectionObject_getattr(
	_mysql_ConnectionObject *self,
	char *name)
{
	PyObject *res;

	res = Py_FindMethod(_mysql_ConnectionObject_methods, (PyObject *)self, name);
	if (res != NULL)
		return res;
	PyErr_Clear();
	if (strcmp(name, "open") == 0)
		return PyInt_FromLong((long)(self->open));
	if (strcmp(name, "closed") == 0)
		return PyInt_FromLong((long)!(self->open));
	if (strcmp(name, "server_capabilities") == 0) {
		check_connection(self);
		return PyInt_FromLong((long)(self->connection.server_capabilities));
	}
	return PyMember_Get((char *)self, _mysql_ConnectionObject_memberlist, name);
}

static PyObject *
_mysql_ResultObject_getattr(
	_mysql_ResultObject *self,
	char *name)
{
	PyObject *res;

	res = Py_FindMethod(_mysql_ResultObject_methods, (PyObject *)self, name);
	if (res != NULL)
		return res;
	PyErr_Clear();
	return PyMember_Get((char *)self, _mysql_ResultObject_memberlist, name);
}

static int
_mysql_ConnectionObject_setattr(
	_mysql_ConnectionObject *c,
	char *name,
	PyObject *v)
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError,
				"can't delete connection attributes");
		return -1;
	}
	return PyMember_Set((char *)c, _mysql_ConnectionObject_memberlist, name, v);
}

static int
_mysql_ResultObject_setattr(
	_mysql_ResultObject *c,
	char *name,
	PyObject *v)
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError,
				"can't delete connection attributes");
		return -1;
	}
	return PyMember_Set((char *)c, _mysql_ResultObject_memberlist, name, v);
}

PyTypeObject _mysql_ConnectionObject_Type = {
#ifndef MS_WIN32
	PyObject_HEAD_INIT(&PyType_Type)
#else
	PyObject_HEAD_INIT(NULL)
#endif
	0,
	"connection",
	sizeof(_mysql_ConnectionObject),
	0,
	(destructor)_mysql_ConnectionObject_dealloc, /* tp_dealloc */
	0, /*tp_print*/
	(getattrfunc)_mysql_ConnectionObject_getattr, /* tp_getattr */
	(setattrfunc)_mysql_ConnectionObject_setattr, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_ConnectionObject_repr, /* tp_repr */
};

PyTypeObject _mysql_ResultObject_Type = {
#ifndef MS_WIN32
	PyObject_HEAD_INIT(&PyType_Type)
#else
	PyObject_HEAD_INIT(NULL)
#endif
	0,
	"result",
	sizeof(_mysql_ResultObject),
	0,
	(destructor)_mysql_ResultObject_dealloc, /* tp_dealloc */
	0, /*tp_print*/
	(getattrfunc)_mysql_ResultObject_getattr, /* tp_getattr */
	(setattrfunc)_mysql_ResultObject_setattr, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_ResultObject_repr, /* tp_repr */
};

static PyMethodDef
_mysql_methods[] = {
	{ "connect",
	  (PyCFunction)_mysql_connect,
	  METH_VARARGS | METH_KEYWORDS,
	  _mysql_connect__doc__
	},
        { "debug",
	  (PyCFunction)_mysql_debug, 
	  METH_VARARGS,
	  _mysql_debug__doc__
	},
	{ "escape", 
	  (PyCFunction)_mysql_escape, 
	  METH_VARARGS,
	  _mysql_escape__doc__
	},
	{ "escape_sequence",
	  (PyCFunction)_mysql_escape_sequence,
	  METH_VARARGS,
	  _mysql_escape_sequence__doc__
	},
	{ "escape_dict",
	  (PyCFunction)_mysql_escape_dict,
	  METH_VARARGS,
	  _mysql_escape_dict__doc__
	},
	{ "escape_string",
	  (PyCFunction)_mysql_escape_string,
	  METH_VARARGS,
	  _mysql_escape_string__doc__
	},
	{ "string_literal",
	  (PyCFunction)_mysql_string_literal,
	  METH_VARARGS,
	  _mysql_string_literal__doc__
	},
	{ "get_client_info",
	  (PyCFunction)_mysql_get_client_info,
	  0,
	  _mysql_get_client_info__doc__
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
	if (PyDict_SetItemString(dict, name, e)) return NULL;
	return e;
}

static char _mysql___doc__[] =
"_mysql: an adaptation of the MySQL C API (mostly)\n\
\n\
You probably are better off using MySQLdb instead of using this\n\
module directly.\n\
\n\
In general, renaming goes from mysql_* to _mysql.*. _mysql.connect()\n\
returns a connection object (MYSQL). Functions which expect MYSQL * as\n\
an argument are now methods of the connection object. A number of things\n\
return result objects (MYSQL_RES). Functions which expect MYSQL_RES * as\n\
an argument are now methods of the result object. The mysql_real_*\n\
functions are the ones used in place of not-real ones. The various\n\
FLAG_*, CLIENT_*, FIELD_TYPE_*, etc. constants are renamed to FLAG.*,\n\
CLIENT.*, FIELD_TYPE.*, etc. Deprecated functions (as of 3.22) are NOT\n\
implemented.\n\
";

DL_EXPORT(void)
init_mysql(void)
{
	PyObject *dict, *module, *emod, *edict;
	module = Py_InitModule3("_mysql", _mysql_methods, _mysql___doc__);
#ifdef MS_WIN32
	_mysql_ConnectionObject_Type.ob_type = &PyType_Type;
	_mysql_ResultObject_Type.ob_type = &PyType_Type;
#endif
	if (!(dict = PyModule_GetDict(module))) goto error;
	if (PyDict_SetItemString(dict, "version_info",
			       PyRun_String(version_info, Py_eval_input,
				       dict, dict)))
		goto error;
	if (PyDict_SetItemString(dict, "__version__",
			       PyString_FromString(__version__)))
		goto error;
	if (!(emod = PyImport_ImportModule("_mysql_exceptions")))
		goto error;
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
	if (PyErr_Occurred())
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
	return;
}


