/*
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

extern PyTypeObject _mysql_ConnectionObject_Type;

typedef struct {
	PyObject_HEAD
	PyObject *conn;
	MYSQL *connection;
	MYSQL_RES *result;
	int nfields;
	int use;
	PyObject *converter;
} _mysql_ResultObject;

extern PyTypeObject _mysql_ResultObject_Type;

PyObject *
_mysql_Exception(c)
	_mysql_ConnectionObject *c;
{
	PyObject *t, *e;
	int merr;

	if (!(t = PyTuple_New(2))) return NULL;
	merr = mysql_errno(&(c->connection));
	if (!merr)
		e = _mysql_InterfaceError;
	else if (merr > CR_MAX_ERROR) {
		PyTuple_SET_ITEM(t, 0, PyInt_FromLong(-1L));
		PyTuple_SET_ITEM(t, 1, PyString_FromString("error totally whack"));
		PyErr_SetObject(_mysql_Error, t);
		return NULL;
	}
	else switch (merr) {
	case CR_COMMANDS_OUT_OF_SYNC:
		e = _mysql_ProgrammingError;
		break;
	case ER_DUP_ENTRY:
		e = _mysql_IntegrityError;
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

typedef struct {
	char *name;
	int value;
} _mysql_Constant;

static _mysql_Constant _mysql_Constant_flag[] = {
	{ "NOT_NULL", NOT_NULL_FLAG },
	{ "PRI_KEY", PRI_KEY_FLAG },
	{ "UNIQUE_KEY", UNIQUE_KEY_FLAG },
	{ "MULTIPLE_KEY", MULTIPLE_KEY_FLAG },
	{ "BLOB", BLOB_FLAG },
	{ "UNSIGNED", UNSIGNED_FLAG },
	{ "ZEROFILL", ZEROFILL_FLAG },
	{ "BINARY", BINARY_FLAG },
	{ "ENUM", ENUM_FLAG },
	{ "AUTO_INCREMENT", AUTO_INCREMENT_FLAG },
	{ "TIMESTAMP", TIMESTAMP_FLAG },
#ifdef SET_FLAG
	{ "SET", SET_FLAG },
#endif
	{ "PART_KEY", PART_KEY_FLAG },
	{ "GROUP", GROUP_FLAG },
	{ NULL } /* sentinel */
} ;

static _mysql_Constant _mysql_Constant_client[] = {
	{ "LONG_PASSWORD", CLIENT_LONG_PASSWORD },
	{ "FOUND_ROWS", CLIENT_FOUND_ROWS },
	{ "LONG_FLAG", CLIENT_LONG_FLAG },
	{ "CONNECT_WITH_DB", CLIENT_CONNECT_WITH_DB },
	{ "NO_SCHEMA", CLIENT_NO_SCHEMA },
	{ "COMPRESS", CLIENT_COMPRESS },
	{ "ODBC", CLIENT_ODBC },
	{ "LOCAL_FILES", CLIENT_LOCAL_FILES },
	{ "IGNORE_SPACE", CLIENT_IGNORE_SPACE },
	{ NULL } /* Sentinel */
} ;

static _mysql_Constant _mysql_Constant_field_type[] = {
	{ "DECIMAL", FIELD_TYPE_DECIMAL },
	{ "TINY", FIELD_TYPE_TINY },
	{ "SHORT", FIELD_TYPE_SHORT },
	{ "LONG", FIELD_TYPE_LONG },
	{ "FLOAT", FIELD_TYPE_FLOAT },
	{ "DOUBLE", FIELD_TYPE_DOUBLE },
	{ "NULL", FIELD_TYPE_NULL },
	{ "TIMESTAMP", FIELD_TYPE_TIMESTAMP },
	{ "LONGLONG", FIELD_TYPE_LONGLONG },
	{ "INT24", FIELD_TYPE_INT24 },
	{ "DATE", FIELD_TYPE_DATE },
	{ "TIME", FIELD_TYPE_TIME },
	{ "DATETIME", FIELD_TYPE_DATETIME },
	{ "YEAR", FIELD_TYPE_YEAR },
	{ "NEWDATE", FIELD_TYPE_NEWDATE },
	{ "ENUM", FIELD_TYPE_ENUM },
	{ "SET", FIELD_TYPE_SET },
	{ "TINY_BLOB", FIELD_TYPE_TINY_BLOB },
	{ "MEDIUM_BLOB", FIELD_TYPE_MEDIUM_BLOB },
	{ "LONG_BLOB", FIELD_TYPE_LONG_BLOB },
	{ "BLOB", FIELD_TYPE_BLOB },
	{ "VAR_STRING", FIELD_TYPE_VAR_STRING },
	{ "STRING", FIELD_TYPE_STRING },
	{ "CHAR", FIELD_TYPE_CHAR },
	{ "INTERVAL", FIELD_TYPE_ENUM },
	{ NULL } /* sentinel */
} ;

static _mysql_Constant _mysql_Constant_cr[] = {
	{ "UNKNOWN_ERROR", CR_UNKNOWN_ERROR },
	{ "SOCKET_CREATE_ERROR", CR_SOCKET_CREATE_ERROR },
	{ "CONNECTION_ERROR", CR_CONNECTION_ERROR },
	{ "CONN_HOST_ERROR", CR_CONN_HOST_ERROR },
	{ "IPSOCK_ERROR", CR_IPSOCK_ERROR },
	{ "UNKNOWN_HOST", CR_UNKNOWN_HOST },
	{ "SERVER_GONE_ERROR", CR_SERVER_GONE_ERROR },
	{ "VERSION_ERROR", CR_VERSION_ERROR },
	{ "OUT_OF_MEMORY", CR_OUT_OF_MEMORY },
	{ "WRONG_HOST_INFO", CR_WRONG_HOST_INFO },
	{ "LOCALHOST_CONNECTION", CR_LOCALHOST_CONNECTION },
	{ "TCP_CONNECTION", CR_TCP_CONNECTION },
	{ "SERVER_HANDSHAKE_ERR", CR_SERVER_HANDSHAKE_ERR },
	{ "SERVER_LOST", CR_SERVER_LOST },
	{ "COMMANDS_OUT_OF_SYNC", CR_COMMANDS_OUT_OF_SYNC },
	{ "NAMEDPIPE_CONNECTION", CR_NAMEDPIPE_CONNECTION },
	{ "NAMEDPIPEWAIT_ERROR", CR_NAMEDPIPEWAIT_ERROR },
	{ "NAMEDPIPEOPEN_ERROR", CR_NAMEDPIPEOPEN_ERROR },
	{ "NAMEDPIPESETSTATE_ERROR", CR_NAMEDPIPEOPEN_ERROR },
	{ NULL } /* sentinel */
} ;

static _mysql_Constant _mysql_Constant_option[] = {
	{ "OPT_CONNECT_TIMEOUT", MYSQL_OPT_CONNECT_TIMEOUT },
	{ "OPT_COMPRESS", MYSQL_OPT_COMPRESS },
        { "OPT_NAMED_PIPE", MYSQL_OPT_NAMED_PIPE },
        { "INIT_COMMAND", MYSQL_INIT_COMMAND },
        { "READE_DEFAULT_FILE", MYSQL_READ_DEFAULT_FILE },
        { "READ_DEFAULT_GROUP", MYSQL_READ_DEFAULT_GROUP },
	{ NULL } /* sentinel */
} ;

static _mysql_Constant _mysql_Constant_er[] = {
	{ "HASHCHK", ER_HASHCHK },
	{ "NISAMCHK", ER_NISAMCHK },
	{ "NO", ER_NO },
	{ "YES", ER_YES },
	{ "CANT_CREATE_FILE", ER_CANT_CREATE_FILE },
	{ "CANT_CREATE_TABLE", ER_CANT_CREATE_TABLE },
	{ "CANT_CREATE_DB", ER_CANT_CREATE_DB },
	{ "DB_CREATE_EXISTS", ER_DB_CREATE_EXISTS },
	{ "DB_DROP_EXISTS", ER_DB_DROP_EXISTS },
	{ "DB_DROP_DELETE", ER_DB_DROP_DELETE },
	{ "DB_DROP_RMDIR", ER_DB_DROP_RMDIR },
	{ "CANT_DELETE_FILE", ER_CANT_DELETE_FILE },
	{ "CANT_FIND_SYSTEM_REC", ER_CANT_FIND_SYSTEM_REC },
	{ "CANT_GET_STAT", ER_CANT_GET_STAT },
	{ "CANT_GET_WD", ER_CANT_GET_WD },
	{ "CANT_LOCK", ER_CANT_LOCK },
	{ "CANT_OPEN_FILE", ER_CANT_OPEN_FILE },
	{ "FILE_NOT_FOUND", ER_FILE_NOT_FOUND },
	{ "CANT_READ_DIR", ER_CANT_READ_DIR },
	{ "CANT_SET_WD", ER_CANT_SET_WD },
	{ "CHECKREAD", ER_CHECKREAD },
	{ "DISK_FULL", ER_DISK_FULL },
	{ "DUP_KEY", ER_DUP_KEY },
	{ "ERROR_ON_CLOSE", ER_ERROR_ON_CLOSE },
	{ "ERROR_ON_READ", ER_ERROR_ON_READ },
	{ "ERROR_ON_RENAME", ER_ERROR_ON_RENAME },
	{ "ERROR_ON_WRITE", ER_ERROR_ON_WRITE },
	{ "FILE_USED", ER_FILE_USED },
	{ "FILSORT_ABORT", ER_FILSORT_ABORT },
	{ "FORM_NOT_FOUND", ER_FORM_NOT_FOUND },
	{ "GET_ERRNO", ER_GET_ERRNO },
	{ "ILLEGAL_HA", ER_ILLEGAL_HA },
	{ "KEY_NOT_FOUND", ER_KEY_NOT_FOUND },
	{ "NOT_FORM_FILE", ER_NOT_FORM_FILE },
	{ "NOT_KEYFILE", ER_NOT_KEYFILE },
	{ "OLD_KEYFILE", ER_OLD_KEYFILE },
	{ "OPEN_AS_READONLY", ER_OPEN_AS_READONLY },
	{ "OUTOFMEMORY", ER_OUTOFMEMORY },
	{ "OUT_OF_SORTMEMORY", ER_OUT_OF_SORTMEMORY },
	{ "UNEXPECTED_EOF", ER_UNEXPECTED_EOF },
	{ "CON_COUNT_ERROR", ER_CON_COUNT_ERROR },
	{ "OUT_OF_RESOURCES", ER_OUT_OF_RESOURCES },
	{ "BAD_HOST_ERROR", ER_BAD_HOST_ERROR },
	{ "HANDSHAKE_ERROR", ER_HANDSHAKE_ERROR },
	{ "DBACCESS_DENIED_ERROR", ER_DBACCESS_DENIED_ERROR },
	{ "ACCESS_DENIED_ERROR", ER_ACCESS_DENIED_ERROR },
	{ "NO_DB_ERROR", ER_NO_DB_ERROR },
	{ "UNKNOWN_COM_ERROR", ER_UNKNOWN_COM_ERROR },
	{ "BAD_NULL_ERROR", ER_BAD_NULL_ERROR },
	{ "BAD_DB_ERROR", ER_BAD_DB_ERROR },
	{ "TABLE_EXISTS_ERROR", ER_TABLE_EXISTS_ERROR },
	{ "BAD_TABLE_ERROR", ER_BAD_TABLE_ERROR },
	{ "NON_UNIQ_ERROR", ER_NON_UNIQ_ERROR },
	{ "SERVER_SHUTDOWN", ER_SERVER_SHUTDOWN },
	{ "BAD_FIELD_ERROR", ER_BAD_FIELD_ERROR },
	{ "WRONG_FIELD_WITH_GROUP", ER_WRONG_FIELD_WITH_GROUP },
	{ "WRONG_GROUP_FIELD", ER_WRONG_GROUP_FIELD },
	{ "WRONG_SUM_SELECT", ER_WRONG_SUM_SELECT },
	{ "WRONG_VALUE_COUNT", ER_WRONG_VALUE_COUNT },
	{ "TOO_LONG_IDENT", ER_TOO_LONG_IDENT },
	{ "DUP_FIELDNAME", ER_DUP_FIELDNAME },
	{ "DUP_KEYNAME", ER_DUP_KEYNAME },
	{ "DUP_ENTRY", ER_DUP_ENTRY },
	{ "WRONG_FIELD_SPEC", ER_WRONG_FIELD_SPEC },
	{ "PARSE_ERROR", ER_PARSE_ERROR },
	{ "EMPTY_QUERY", ER_EMPTY_QUERY },
	{ "NONUNIQ_TABLE", ER_NONUNIQ_TABLE },
	{ "INVALID_DEFAULT", ER_INVALID_DEFAULT },
	{ "MULTIPLE_PRI_KEY", ER_MULTIPLE_PRI_KEY },
	{ "TOO_MANY_KEYS", ER_TOO_MANY_KEYS },
	{ "TOO_MANY_KEY_PARTS", ER_TOO_MANY_KEY_PARTS },
	{ "TOO_LONG_KEY", ER_TOO_LONG_KEY },
	{ "KEY_COLUMN_DOES_NOT_EXITS", ER_KEY_COLUMN_DOES_NOT_EXITS },
	{ "BLOB_USED_AS_KEY", ER_BLOB_USED_AS_KEY },
	{ "TOO_BIG_FIELDLENGTH", ER_TOO_BIG_FIELDLENGTH },
	{ "WRONG_AUTO_KEY", ER_WRONG_AUTO_KEY },
	{ "READY", ER_READY },
	{ "NORMAL_SHUTDOWN", ER_NORMAL_SHUTDOWN },
	{ "GOT_SIGNAL", ER_GOT_SIGNAL },
	{ "SHUTDOWN_COMPLETE", ER_SHUTDOWN_COMPLETE },
	{ "FORCING_CLOSE", ER_FORCING_CLOSE },
	{ "IPSOCK_ERROR", ER_IPSOCK_ERROR },
	{ "NO_SUCH_INDEX", ER_NO_SUCH_INDEX },
	{ "WRONG_FIELD_TERMINATORS", ER_WRONG_FIELD_TERMINATORS },
	{ "BLOBS_AND_NO_TERMINATED", ER_BLOBS_AND_NO_TERMINATED },
	{ "TEXTFILE_NOT_READABLE", ER_TEXTFILE_NOT_READABLE },
	{ "FILE_EXISTS_ERROR", ER_FILE_EXISTS_ERROR },
	{ "LOAD_INFO", ER_LOAD_INFO },
	{ "ALTER_INFO", ER_ALTER_INFO },
	{ "WRONG_SUB_KEY", ER_WRONG_SUB_KEY },
	{ "CANT_REMOVE_ALL_FIELDS", ER_CANT_REMOVE_ALL_FIELDS },
	{ "CANT_DROP_FIELD_OR_KEY", ER_CANT_DROP_FIELD_OR_KEY },
	{ "INSERT_INFO", ER_INSERT_INFO },
	{ "INSERT_TABLE_USED", ER_INSERT_TABLE_USED },
	{ "NO_SUCH_THREAD", ER_NO_SUCH_THREAD },
	{ "KILL_DENIED_ERROR", ER_KILL_DENIED_ERROR },
	{ "NO_TABLES_USED", ER_NO_TABLES_USED },
	{ "TOO_BIG_SET", ER_TOO_BIG_SET },
	{ "NO_UNIQUE_LOGFILE", ER_NO_UNIQUE_LOGFILE },
	{ "TABLE_NOT_LOCKED_FOR_WRITE", ER_TABLE_NOT_LOCKED_FOR_WRITE },
	{ "TABLE_NOT_LOCKED", ER_TABLE_NOT_LOCKED },
	{ "BLOB_CANT_HAVE_DEFAULT", ER_BLOB_CANT_HAVE_DEFAULT },
	{ "WRONG_DB_NAME", ER_WRONG_DB_NAME },
	{ "WRONG_TABLE_NAME", ER_WRONG_TABLE_NAME },
	{ "TOO_BIG_SELECT", ER_TOO_BIG_SELECT },
	{ "UNKNOWN_ERROR", ER_UNKNOWN_ERROR },
	{ "UNKNOWN_PROCEDURE", ER_UNKNOWN_PROCEDURE },
	{ "WRONG_PARAMCOUNT_TO_PROCEDURE", ER_WRONG_PARAMCOUNT_TO_PROCEDURE },
	{ "WRONG_PARAMETERS_TO_PROCEDURE", ER_WRONG_PARAMETERS_TO_PROCEDURE },
	{ "UNKNOWN_TABLE", ER_UNKNOWN_TABLE },
	{ "FIELD_SPECIFIED_TWICE", ER_FIELD_SPECIFIED_TWICE },
	{ "INVALID_GROUP_FUNC_USE", ER_INVALID_GROUP_FUNC_USE },
	{ "UNSUPPORTED_EXTENSION", ER_UNSUPPORTED_EXTENSION },
	{ "TABLE_MUST_HAVE_COLUMNS", ER_TABLE_MUST_HAVE_COLUMNS },
	{ "RECORD_FILE_FULL", ER_RECORD_FILE_FULL },
	{ "UNKNOWN_CHARACTER_SET", ER_UNKNOWN_CHARACTER_SET },
	{ "TOO_MANY_TABLES", ER_TOO_MANY_TABLES },
	{ "TOO_MANY_FIELDS", ER_TOO_MANY_FIELDS },
	{ "TOO_BIG_ROWSIZE", ER_TOO_BIG_ROWSIZE },
	{ "STACK_OVERRUN", ER_STACK_OVERRUN },
	{ "WRONG_OUTER_JOIN", ER_WRONG_OUTER_JOIN },
	{ "NULL_COLUMN_IN_INDEX", ER_NULL_COLUMN_IN_INDEX },
	{ "CANT_FIND_UDF", ER_CANT_FIND_UDF },
	{ "CANT_INITIALIZE_UDF", ER_CANT_INITIALIZE_UDF },
	{ "UDF_NO_PATHS", ER_UDF_NO_PATHS },
	{ "UDF_EXISTS", ER_UDF_EXISTS },
	{ "CANT_OPEN_LIBRARY", ER_CANT_OPEN_LIBRARY },
	{ "CANT_FIND_DL_ENTRY", ER_CANT_FIND_DL_ENTRY },
	{ "FUNCTION_NOT_DEFINED", ER_FUNCTION_NOT_DEFINED },
	{ "HOST_IS_BLOCKED", ER_HOST_IS_BLOCKED },
	{ "HOST_NOT_PRIVILEGED", ER_HOST_NOT_PRIVILEGED },
	{ "PASSWORD_ANONYMOUS_USER", ER_PASSWORD_ANONYMOUS_USER },
	{ "PASSWORD_NOT_ALLOWED", ER_PASSWORD_NOT_ALLOWED },
	{ "PASSWORD_NO_MATCH", ER_PASSWORD_NO_MATCH },
	{ "UPDATE_INFO", ER_UPDATE_INFO },
	{ "CANT_CREATE_THREAD", ER_CANT_CREATE_THREAD },
	{ "WRONG_VALUE_COUNT_ON_ROW", ER_WRONG_VALUE_COUNT_ON_ROW },
	{ "CANT_REOPEN_TABLE", ER_CANT_REOPEN_TABLE },
	{ "INVALID_USE_OF_NULL", ER_INVALID_USE_OF_NULL },
	{ "REGEXP_ERROR", ER_REGEXP_ERROR },
	{ "MIX_OF_GROUP_FUNC_AND_FIELDS", ER_MIX_OF_GROUP_FUNC_AND_FIELDS },
	{ "NONEXISTING_GRANT", ER_NONEXISTING_GRANT },
	{ "TABLEACCESS_DENIED_ERROR", ER_TABLEACCESS_DENIED_ERROR },
	{ "COLUMNACCESS_DENIED_ERROR", ER_COLUMNACCESS_DENIED_ERROR },
	{ "ILLEGAL_GRANT_FOR_TABLE", ER_ILLEGAL_GRANT_FOR_TABLE },
	{ "GRANT_WRONG_HOST_OR_USER", ER_GRANT_WRONG_HOST_OR_USER },
	{ "NO_SUCH_TABLE", ER_NO_SUCH_TABLE },
	{ "NONEXISTING_TABLE_GRANT", ER_NONEXISTING_TABLE_GRANT },
	{ "NOT_ALLOWED_COMMAND", ER_NOT_ALLOWED_COMMAND },
	{ "SYNTAX_ERROR", ER_SYNTAX_ERROR },
#ifdef ER_DELAYED_CANT_CHANGE_LOCK
	{ "DELAYED_CANT_CHANGE_LOCK", ER_DELAYED_CANT_CHANGE_LOCK },
	{ "TOO_MANY_DELAYED_THREADS", ER_TOO_MANY_DELAYED_THREADS },
	{ "ABORTING_CONNECTION", ER_ABORTING_CONNECTION },
	{ "NET_PACKET_TOO_LARGE", ER_NET_PACKET_TOO_LARGE },
	{ "NET_READ_ERROR_FROM_PIPE", ER_NET_READ_ERROR_FROM_PIPE },
	{ "NET_FCNTL_ERROR", ER_NET_FCNTL_ERROR },
	{ "NET_PACKETS_OUT_OF_ORDER", ER_NET_PACKETS_OUT_OF_ORDER },
	{ "NET_UNCOMPRESS_ERROR", ER_NET_UNCOMPRESS_ERROR },
	{ "NET_READ_ERROR", ER_NET_READ_ERROR },
	{ "NET_READ_INTERRUPTED", ER_NET_READ_INTERRUPTED },
	{ "NET_ERROR_ON_WRITE", ER_NET_ERROR_ON_WRITE },
	{ "NET_WRITE_INTERRUPTED", ER_NET_WRITE_INTERRUPTED },
#endif
	{ "ERROR_MESSAGES", ER_ERROR_MESSAGES },
	{ NULL } /* sentinel */
} ;

static _mysql_ResultObject*
_mysql_ResultObject_New(conn, result, use, conv)
	_mysql_ConnectionObject *conn;
	MYSQL_RES *result;
	int use;
	PyObject *conv;
{
	int n, i;
	MYSQL_FIELD *fields;
	_mysql_ResultObject *r;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	r->connection = &conn->connection;
	r->conn = (PyObject *) conn;
	r->converter = NULL;
	r->use = use;
	Py_INCREF(conn);
	Py_INCREF(conv);
	r->result = result;
	n = mysql_num_fields(result);
	r->nfields = n;
        if (n) {
		if (!(r->converter = PyTuple_New(n))) {
			Py_DECREF(conv);
			Py_DECREF(conn);
			return NULL;
		}
		fields = mysql_fetch_fields(result);
		for (i=0; i<n; i++) {
			PyObject *tmp, *fun;
			tmp = PyInt_FromLong((long) fields[i].type);
			fun = PyObject_GetItem(conv, tmp);
			Py_XDECREF(tmp);
			if (!fun) {
				PyErr_Clear();
				fun = Py_None;
				Py_INCREF(Py_None);
			}
			PyTuple_SET_ITEM(r->converter, i, fun);
		}
	}
	Py_DECREF(conv);
	return r;
}

static PyObject *
_mysql_connect(self, args, kwargs)
	PyObject *self;
	PyObject *args;
	PyObject *kwargs;
{
	MYSQL *conn;
	PyObject *conv = NULL;
	char *host = NULL, *user = NULL, *passwd = NULL,
		*db = NULL, *unix_socket = NULL;
	uint port = MYSQL_PORT;
	uint client_flag = 0;
	static char *kwlist[] = { "host", "user", "passwd", "db", "port",
				  "unix_socket", "client_flag", "conv",
				  NULL } ;
	_mysql_ConnectionObject *c = PyObject_NEW(_mysql_ConnectionObject,
					      &_mysql_ConnectionObject_Type);
	if (c == NULL) return NULL;
	c->open = 0;
	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ssssisiO:connect",
					 kwlist,
					 &host, &user, &passwd, &db,
					 &port, &unix_socket, &client_flag,
					 &conv))
		return NULL;
	if (conv) {
		c->converter = conv;
	} else {
		if (!(c->converter = PyDict_New())) {
			Py_DECREF(c);
			return NULL;
		}
	}
	Py_BEGIN_ALLOW_THREADS ;
	conn = mysql_init(&(c->connection));
	conn = mysql_real_connect(&(c->connection), host, user, passwd, db,
				  port, unix_socket, client_flag);
	Py_END_ALLOW_THREADS ;
	if (!conn) {
		_mysql_Exception(c);
		Py_DECREF(c);
		return NULL;
	}
	c->open = 1;
	return (PyObject *) c;
}

static PyObject *
_mysql_ConnectionObject_close(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	mysql_close(&(self->connection));
        Py_END_ALLOW_THREADS
	self->open = 0;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_affected_rows(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyLong_FromUnsignedLongLong(mysql_affected_rows(&(self->connection)));
}

static PyObject *
_mysql_debug(self, args)
	PyObject *self;
	PyObject *args;
{
	char *debug;
	if (!PyArg_ParseTuple(args, "s", &debug)) return NULL;
	mysql_debug(debug);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_dump_debug_info(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	int err;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_dump_debug_info(&(self->connection));
	Py_END_ALLOW_THREADS
	if (err) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_errno(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyInt_FromLong((long)mysql_errno(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_error(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_error(&(self->connection)));
}

static PyObject *
_mysql_escape_string(self, args)
	PyObject *self;
	PyObject *args;
{
	PyObject *str;
	char *in, *out;
	int len, size;
	if (!PyArg_ParseTuple(args, "s#:escape_string", &in, &size)) return NULL;
	str = PyString_FromStringAndSize((char *) NULL, size*2+1);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
	len = mysql_escape_string(out, in, size);
	if (_PyString_Resize(&str, len) < 0) return NULL;
	return (str);
}

static PyObject *
_mysql_string_literal(self, args)
	PyObject *self;
	PyObject *args;
{
	PyObject *str;
	char *in, *out;
	int len, size;
	if (!PyArg_ParseTuple(args, "s#:string_literal", &in, &size)) return NULL;
	str = PyString_FromStringAndSize((char *) NULL, size*2+3);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
	len = mysql_escape_string(out+1, in, size);
	*out = *(out+len+1) = '\'';
	if (_PyString_Resize(&str, len+2) < 0) return NULL;
	return (str);
}

static PyObject *_mysql_NULL;

static PyObject *
_mysql_escape_row(self, args)
	PyObject *self;
	PyObject *args;
{
	PyObject *o=NULL, *d=NULL, *r=NULL, *item, *quoted, 
		*itemtype, *itemconv;
	int i, n;
	if (!PyArg_ParseTuple(args, "O!O!:escape_row", &PyTuple_Type, &o,
				                       &PyDict_Type, &d))
		goto error;
	if (!(n = PyObject_Length(o))) goto error;
	if (!(r = PyTuple_New(n))) goto error;
	for (i=0; i<n; i++) {
		item = PyTuple_GET_ITEM(o, i);
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
		quoted = PyObject_CallFunction(itemconv, "O", item);
		Py_DECREF(itemconv);
		if (!quoted) goto error;
		PyTuple_SET_ITEM(r, i, quoted);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}
				

static PyObject *
_mysql_ResultObject_describe(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	if (!PyArg_NoArgs(args)) return NULL;
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
_mysql_ResultObject_field_flags(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	PyObject *d;
	MYSQL_FIELD *fields;
	unsigned int i, n;
	if (!PyArg_NoArgs(args)) return NULL;
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
_mysql_field_to_python(converter, rowitem, length)
	PyObject *converter;
	char *rowitem;
	unsigned long length;
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
_mysql_row_to_tuple(self, row)
	_mysql_ResultObject *self;
	MYSQL_ROW row;
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
_mysql_row_to_dict(self, row)
	_mysql_ResultObject *self;
	MYSQL_ROW row;
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
_mysql_row_to_dict_old(self, row)
	_mysql_ResultObject *self;
	MYSQL_ROW row;
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
_mysql_ResultObject_fetch_row(self, args, kwargs)
	_mysql_ResultObject *self;
	PyObject *args, *kwargs;
{
	typedef PyObject *_PYFUNC();
	static char *kwlist[] = { "maxrows", "how", NULL };
	static _PYFUNC *row_converters[] =
	{
		_mysql_row_to_tuple,
		_mysql_row_to_dict,
		_mysql_row_to_dict_old
	};
	_PYFUNC *convert_row;
	unsigned int maxrows=1, how=0, i;
	PyObject *r;
	MYSQL_ROW row;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii:fetch_row", kwlist,
					 &maxrows, &how))
		return NULL;
	if (how < 0 || how >= sizeof(row_converters)) {
		PyErr_SetString(PyExc_ValueError, "how out of range");
		return NULL;
	}
	convert_row = row_converters[how];

	if (!(r = PyTuple_New(maxrows))) return NULL;
	for (i = 0; i<maxrows; i++) {
		PyObject *v;
		if (!self->use)
			row = mysql_fetch_row(self->result);
		else {
			Py_BEGIN_ALLOW_THREADS;
			row = mysql_fetch_row(self->result);
			Py_END_ALLOW_THREADS;
		}
		if (!row && mysql_errno(self->connection)) {
			Py_XDECREF(r);
			return _mysql_Exception(self->connection);
		}
		if (!row) {
			if (_PyTuple_Resize(&r, i, 0) == -1) goto error;
			break;
		}
		v = convert_row(self, row);
		if (!v) goto error;
		PyTuple_SET_ITEM(r, i, v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

#if MYSQL_VERSION_ID >= 32303
static PyObject *
_mysql_ConnectionObject_change_user(self, args, kwargs)
	_mysql_ConnectionObject *self;
	PyObject *args, *kwargs;
{
	char *user, *pwd=NULL, *db=NULL;
	int r;
        static char *kwlist[] = { "user", "passwd", "db", NULL } ;

	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|ss:change_user",
					 kwlist, &user, &pwd, &db))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_change_user(&(self->connection), user, pwd, db);
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}
#endif

static PyObject *
_mysql_get_client_info(self, args)
	PyObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_client_info());
}

static PyObject *
_mysql_ConnectionObject_commit(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
        Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_get_host_info(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_host_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_proto_info(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyInt_FromLong((long)mysql_get_proto_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_server_info(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_server_info(&(self->connection)));
}

static PyObject *
_mysql_ConnectionObject_info(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	char *s;
	if (!PyArg_NoArgs(args)) return NULL;
	s = mysql_info(&(self->connection));
	if (s) return PyString_FromString(s);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_insert_id(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	my_ulonglong r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyLong_FromUnsignedLongLong(r);
}

static PyObject *
_mysql_ConnectionObject_kill(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	unsigned long pid;
	int r;
	if (!PyArg_ParseTuple(args, "i:kill", &pid)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_kill(&(self->connection), pid);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_list_dbs(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;
	char *wild = NULL;

	if (!PyArg_ParseTuple(args, "|s:list_dbs", &wild)) return NULL;
	Py_BEGIN_ALLOW_THREADS
        result = mysql_list_dbs(&(self->connection), wild);
	Py_END_ALLOW_THREADS
        if (!result) return _mysql_Exception(self);
	return (PyObject *) _mysql_ResultObject_New(self, result, 0,
                                                    self->converter);
}

static PyObject *
_mysql_ConnectionObject_list_fields(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;
	char *wild = NULL, *table;

	if (!PyArg_ParseTuple(args, "s|s:list_fields", &table, &wild)) return NULL;
	Py_BEGIN_ALLOW_THREADS
        result = mysql_list_fields(&(self->connection), table, wild);
	Py_END_ALLOW_THREADS
        if (!result) return _mysql_Exception(self);
	return (PyObject *) _mysql_ResultObject_New(self, result, 0,
                                                    self->converter);
}

static PyObject *
_mysql_ConnectionObject_list_processes(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;

	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
        result = mysql_list_processes(&(self->connection));
	Py_END_ALLOW_THREADS
        if (!result) return _mysql_Exception(self);
	return (PyObject *) _mysql_ResultObject_New(self, result, 0,
                                                    self->converter);
}

static PyObject *
_mysql_ConnectionObject_list_tables(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;
	char *wild = NULL;

	if (!PyArg_ParseTuple(args, "|s:list_tables", &wild)) return NULL;
	Py_BEGIN_ALLOW_THREADS
        result = mysql_list_tables(&(self->connection), wild);
	Py_END_ALLOW_THREADS
        if (!result) return _mysql_Exception(self);
	return (PyObject *) _mysql_ResultObject_New(self, result, 0,
                                                    self->converter);
}

static PyObject *
_mysql_ConnectionObject_field_count(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
#if MYSQL_VERSION_ID < 32224
	return PyInt_FromLong((long)mysql_num_fields(&(self->connection)));
#else
	return PyInt_FromLong((long)mysql_field_count(&(self->connection)));
#endif
}	

static PyObject *
_mysql_ResultObject_num_fields(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyInt_FromLong((long)mysql_num_fields(self->result));
}	

static PyObject *
_mysql_ResultObject_num_rows(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyLong_FromUnsignedLongLong(mysql_num_rows(self->result));
}	

static PyObject *
_mysql_ConnectionObject_ping(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	int r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_ping(&(self->connection));
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_query(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	char *query;
	int len, r;
	if (!PyArg_ParseTuple(args, "s#:query", &query, &len)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_real_query(&(self->connection), query, len);
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_select_db(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	char *db;
	int r;
	if (!PyArg_ParseTuple(args, "s:select_db", &db)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_select_db(&(self->connection), db);
	Py_END_ALLOW_THREADS
	if (r) 	return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_shutdown(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	int r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_shutdown(&(self->connection));
	Py_END_ALLOW_THREADS
	if (r) return _mysql_Exception(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_stat(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	char *s;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	s = mysql_stat(&(self->connection));
	Py_END_ALLOW_THREADS
	if (!s) return _mysql_Exception(self);
	return PyString_FromString(s);
}

static PyObject *
_mysql_ConnectionObject_store_result(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;

	if (!PyArg_NoArgs(args)) return NULL;
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
_mysql_ConnectionObject_thread_id(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	unsigned long pid;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	pid = mysql_thread_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyInt_FromLong((long)pid);
}

static PyObject *
_mysql_ConnectionObject_use_result(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	MYSQL_RES *result;

	if (!PyArg_NoArgs(args)) return NULL;
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
_mysql_ConnectionObject_dealloc(self)
	_mysql_ConnectionObject *self;
{
	if (self->open) {
		Py_BEGIN_ALLOW_THREADS
		mysql_close(&(self->connection));
		Py_END_ALLOW_THREADS
	}
	Py_XDECREF(self->converter);
	PyMem_Free((char *) self);
}

static PyObject *
_mysql_ConnectionObject_repr(self)
	_mysql_ConnectionObject *self;
{
	char buf[300];
	sprintf(buf, "<%s connection to '%.256s' at %lx>",
		self->open ? "open" : "closed",
		self->connection.host,
		(long)self);
	return PyString_FromString(buf);
}

static PyObject *
_mysql_ResultObject_data_seek(self, args)
     _mysql_ResultObject *self;
     PyObject *args;
{
	unsigned int row;
	if (!PyArg_ParseTuple(args, "i:data_seek", &row)) return NULL;
	mysql_data_seek(self->result, row);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ResultObject_row_seek(self, args)
     _mysql_ResultObject *self;
     PyObject *args;
{
	int offset;
        MYSQL_ROW_OFFSET r;
	if (!PyArg_ParseTuple(args, "i:row_seek", &offset)) return NULL;
	r = mysql_row_tell(self->result);
	mysql_row_seek(self->result, r+offset);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ResultObject_row_tell(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	MYSQL_ROW_OFFSET r;
	if (!PyArg_NoArgs(args)) return NULL;
	r = mysql_row_tell(self->result);
	return PyInt_FromLong(r-self->result->data->data);
}

static void
_mysql_ResultObject_dealloc(self)
	_mysql_ResultObject *self;
{
	mysql_free_result(self->result);
	Py_DECREF(self->conn);
	Py_DECREF(self->converter);
	PyMem_Free((char *) self);
}

static PyObject *
_mysql_ResultObject_repr(self)
	_mysql_ResultObject *self;
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
	{"close",           (PyCFunction)_mysql_ConnectionObject_close, 0},
	{"commit",          (PyCFunction)_mysql_ConnectionObject_commit, 0},
	{"dump_debug_info", (PyCFunction)_mysql_ConnectionObject_dump_debug_info, 0},
	{"error",           (PyCFunction)_mysql_ConnectionObject_error, 0},
	{"errno",           (PyCFunction)_mysql_ConnectionObject_errno, 0},
	{"field_count",     (PyCFunction)_mysql_ConnectionObject_field_count, 0}, 
	{"get_host_info",   (PyCFunction)_mysql_ConnectionObject_get_host_info, 0},
	{"get_proto_info",  (PyCFunction)_mysql_ConnectionObject_get_proto_info, 0},
	{"get_server_info", (PyCFunction)_mysql_ConnectionObject_get_server_info, 0},
	{"info",            (PyCFunction)_mysql_ConnectionObject_info, 0},
	{"insert_id",       (PyCFunction)_mysql_ConnectionObject_insert_id, 0},
	{"kill",            (PyCFunction)_mysql_ConnectionObject_kill, 1},
	{"list_dbs",        (PyCFunction)_mysql_ConnectionObject_list_dbs, 1},
	{"list_fields",     (PyCFunction)_mysql_ConnectionObject_list_fields, 1},
	{"list_processes",  (PyCFunction)_mysql_ConnectionObject_list_processes, 0},
	{"list_tables",     (PyCFunction)_mysql_ConnectionObject_list_tables, 1},
	{"ping",            (PyCFunction)_mysql_ConnectionObject_ping, 0},
	{"query",           (PyCFunction)_mysql_ConnectionObject_query, 1},
	{"select_db",       (PyCFunction)_mysql_ConnectionObject_select_db, 1},
	{"shutdown",        (PyCFunction)_mysql_ConnectionObject_shutdown, 0},
	{"stat",            (PyCFunction)_mysql_ConnectionObject_stat, 0},
	{"store_result",    (PyCFunction)_mysql_ConnectionObject_store_result, 0},
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
	{"data_seek",       (PyCFunction)_mysql_ResultObject_data_seek, 1},
	{"row_seek",        (PyCFunction)_mysql_ResultObject_row_seek, 1},
	{"row_tell",        (PyCFunction)_mysql_ResultObject_row_tell, 0},
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
_mysql_ConnectionObject_getattr(self, name)
	_mysql_ConnectionObject *self;
	char *name;
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
	return PyMember_Get((char *)self, _mysql_ConnectionObject_memberlist, name);
}

static PyObject *
_mysql_ResultObject_getattr(self, name)
	_mysql_ResultObject *self;
	char *name;
{
	PyObject *res;

	res = Py_FindMethod(_mysql_ResultObject_methods, (PyObject *)self, name);
	if (res != NULL)
		return res;
	PyErr_Clear();
	return PyMember_Get((char *)self, _mysql_ResultObject_memberlist, name);
}

static int
_mysql_ConnectionObject_setattr(c, name, v)
	_mysql_ConnectionObject *c;
	char *name;
	PyObject *v;
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError,
				"can't delete connection attributes");
		return -1;
	}
	return PyMember_Set((char *)c, _mysql_ConnectionObject_memberlist, name, v);
}

static int
_mysql_ResultObject_setattr(c, name, v)
	_mysql_ResultObject *c;
	char *name;
	PyObject *v;
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
	{ "connect", (PyCFunction)_mysql_connect, METH_VARARGS | METH_KEYWORDS },
        { "debug", (PyCFunction)_mysql_debug, METH_VARARGS },
	{ "escape_row", (PyCFunction)_mysql_escape_row, METH_VARARGS },
	{ "escape_string", (PyCFunction)_mysql_escape_string, METH_VARARGS },
	{ "string_literal", (PyCFunction)_mysql_string_literal, METH_VARARGS },
	{ "get_client_info", (PyCFunction)_mysql_get_client_info },
	{NULL, NULL} /* sentinel */
};

static PyObject *
_mysql_NewException(PyObject *dict,
		    char *name,
		    PyObject *base)
{
	PyObject *v;
	char longname[256];

	sprintf(longname, "_mysql.%s", name);
	if ((v = PyErr_NewException(longname, base, NULL)) == NULL)
		return NULL;
	if (PyDict_SetItemString(dict, name, v)) return NULL;
	return v;
}

int
_mysql_Constant_class(mdict, type, table)
	PyObject *mdict;
	char *type;
	_mysql_Constant *table;
{
	PyObject *d, *c, *v;
	int i;
	/* XXX This leaks memory if it fails, but then the whole module
	   fails to import, so probably no big deal */
	if (!(d = PyDict_New())) goto error;
	for (i = 0; table[i].name; i++) {
		if (!(v = PyInt_FromLong((long)table[i].value))) goto error;
		if (PyDict_SetItemString(d, table[i].name, v)) goto error;
	}
	if (!(c = PyClass_New(NULL,d,PyString_InternFromString(type)))) goto error;
	if (PyDict_SetItemString(mdict, type, c)) goto error;
	return 0;
  error:
	Py_XDECREF(d);
	return -1;
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
CLIENT.*, FIELD_TYPE.*, etc. Deprecated functions are NOT implemented.\n\
\n\
type_conv is a dictionary which maps FIELD_TYPE.* to Python functions\n\
which convert a string to some value. This is used by the fetch_row method.\n\
Types not mapped are returned as strings. Numbers are all converted\n\
reasonably, except DECIMAL.\n\
\n\
result.describe() produces a DB API description of the rows.\n\
\n\
escape_row() accepts a sequence of items and a type conversion dictionary.\n\
Using the type of the item, it gets a converter function from the dictionary\n\
(uses the string type if the item type is not found) and applies this to the\n\
item. the result should be converted to strings with all the necessary\n\
quoting.\n\
\n\
mysql_escape_string() on them, and returns them as a tuple.\n\
\n\
result.field_flags() returns the field flags for the result.\n\
\n\
result.fetch_row([n=0[, how=1]]) fetches up to n rows (default: n=1)\n\
as a tuple of tuples (default: how=0) or dictionaries (how=1).\n\
MySQL returns strings, but fetch_row() does data conversion\n\
according to type_conv.\n\
\n\
For everything else, check the MySQL docs." ;

void
init_mysql()
{
	PyObject *dict, *module;
	module = Py_InitModule3("_mysql", _mysql_methods, _mysql___doc__);
#ifdef MS_WIN32
	_mysql_ConnectionObject_Type.ob_type = &PyType_Type;
	_mysql_ResultObject_Type.ob_type = &PyType_Type;
#endif
	dict = PyModule_GetDict(module);
	if (!(_mysql_Warning =
	      _mysql_NewException(dict, "Warning", PyExc_StandardError)))
		goto error;
	if (!(_mysql_Error =
	      _mysql_NewException(dict, "Error", PyExc_StandardError)))
		goto error;
	if (!(_mysql_InterfaceError =
	      _mysql_NewException(dict, "InterfaceError", _mysql_Error)))
		goto error;
	if (!(_mysql_DatabaseError =
	      _mysql_NewException(dict, "DatabaseError", _mysql_Error)))
		goto error;
	if (!(_mysql_DataError =
	      _mysql_NewException(dict, "DataError", _mysql_DatabaseError)))
		goto error;
	if (!(_mysql_OperationalError =
	      _mysql_NewException(dict, "OperationalError",
				  _mysql_DatabaseError)))
		goto error;
	if (!(_mysql_IntegrityError =
	      _mysql_NewException(dict, "IntegrityError",
				  _mysql_DatabaseError)))
		goto error;
	if (!(_mysql_InternalError =
	      _mysql_NewException(dict, "InternalError",
				  _mysql_DatabaseError)))
		goto error;
	if (!(_mysql_ProgrammingError =
	      _mysql_NewException(dict, "ProgrammingError",
				  _mysql_DatabaseError)))
		goto error;
	if (!(_mysql_NotSupportedError =
	      _mysql_NewException(dict, "NotSupportedError",
				  _mysql_DatabaseError)))
		goto error;
	if (_mysql_Constant_class(dict, "FLAG", _mysql_Constant_flag))
		goto error;
	if (_mysql_Constant_class(dict, "CLIENT", _mysql_Constant_client))
		goto error;
	if (_mysql_Constant_class(dict, "FIELD_TYPE", _mysql_Constant_field_type))
		goto error;
	if (_mysql_Constant_class(dict, "CR", _mysql_Constant_cr))
		goto error;
	if (_mysql_Constant_class(dict, "ER", _mysql_Constant_er))
		goto error;
	if (_mysql_Constant_class(dict, "option", _mysql_Constant_option))
		goto error;
	if (!(_mysql_NULL = PyString_FromString("NULL")))
		goto error;
	if (PyDict_SetItemString(dict, "NULL", _mysql_NULL)) goto error;
  error:
	if (PyErr_Occurred())
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
	return;
}


