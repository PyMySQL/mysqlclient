#include "Python.h"
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
	{ "SET", SET_FLAG },
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
	if (conv) {
		c->converter = conv;
		Py_INCREF(conv);
	} else {
		if (!(c->converter = PyDict_New())) {
			Py_DECREF(c);
			return NULL;
		}
	}
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
	PyObject *o;
	if (!PyArg_ParseTuple(args, "s#:escape_string", &in, &size)) return NULL;
	str = PyString_FromStringAndSize((char *) NULL, size*2+1);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
	len = mysql_escape_string(out, in, size);
	if (_PyString_Resize(&str, len) < 0) return NULL;
	return (str);
}

static PyObject *_mysql_NULL;

static PyObject *
_mysql_escape_row(self, args)
	PyObject *self;
	PyObject *args;
{
	PyObject *o=NULL, *r=NULL, *item, *quoted, *str, *itemstr;
	char *in, *out;
	int i, n, len, size;
	if (!PyArg_ParseTuple(args, "O:escape_row", &o)) goto error2;
	if (!PySequence_Check(o)) {
		PyErr_SetString(PyExc_TypeError, "sequence required");
		goto error2;
	}
	if (!(n = PyObject_Length(o))) goto error2;
	if (!(r = PyTuple_New(n))) goto error;
	for (i=0; i<n; i++) {
		if (!(item = PySequence_GetItem(o, i))) goto error;
		if (item == Py_None) {
			quoted = _mysql_NULL;
			Py_INCREF(_mysql_NULL);
		}
		else {
			if (!(itemstr = PyObject_Str(item)))
				goto error;
			if (!(in = PyString_AsString(itemstr))) {
				Py_DECREF(itemstr);
				goto error;
			}
			size = PyString_GET_SIZE(itemstr);
			str = PyString_FromStringAndSize((char *)NULL, size*2+3);
			if (!str) goto error;
			out = PyString_AS_STRING(str);
			len = mysql_escape_string(out+1, in, size);
			*out = '\'' ;
			*(out+len+1) = '\'' ;
			*(out+len+2) = 0;
			if (_PyString_Resize(&str, len+2) < 0)
				goto error;
			Py_DECREF(itemstr);
			quoted = str;
		}
		Py_DECREF(item);
		PyTuple_SET_ITEM(r, i, quoted);
	}
	return r;
  error:
	Py_XDECREF(r);
  error2:
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
_mysql_ResultObject_fetch_row(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r, *c;
	MYSQL_ROW row;
	if (!args) {
		if (!PyArg_NoArgs(args)) return NULL;
	}
	if (!self->use)
		row = mysql_fetch_row(self->result);
	else {
		Py_BEGIN_ALLOW_THREADS;
		row = mysql_fetch_row(self->result);
		Py_END_ALLOW_THREADS;
	}
	n = mysql_num_fields(self->result);
	if (!row && mysql_errno(self->connection))
		return _mysql_Exception(self->connection);
	if (!row) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	if (!(r = PyTuple_New(n))) return NULL;
	length = mysql_fetch_lengths(self->result);
	for (i=0; i<n; i++) {
		PyObject *v;
		if (row[i]) {
			c = PyTuple_GET_ITEM(self->converter, i);
			if (c != Py_None)
				v = PyObject_CallFunction(c,
							  "s#",
							  row[i],
							  (int)length[i]);
			else
				v = PyString_FromStringAndSize(row[i],
							       (int)length[i]);
			if (!v) goto error;
		}
		else {
			Py_INCREF(Py_None);
			v = Py_None;
		}
		PyTuple_SET_ITEM(r, i, v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static PyObject *
_mysql_ResultObject_fetch_all_rows(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r;
	if (!PyArg_NoArgs(args)) return NULL;
	if (!(r = PyList_New(0))) return NULL;
	while (1) {
		PyObject *v = _mysql_ResultObject_fetch_row(self, NULL);
		if (!v) goto error;
		if (v == Py_None) {
			Py_DECREF(v);
			return r;
		}
		PyList_Append(r, v);
		Py_DECREF(v);
	}
  error:
	Py_XDECREF(r);
	return NULL;
}

static PyObject *
_mysql_ResultObject_fetch_rows(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	unsigned int n, i;
	PyObject *r;

	if (!PyArg_ParseTuple(args, "i", &n)) return NULL;
	if (!(r = PyTuple_New(n))) return NULL;
	for (i = 0; i<n; i++) {
		PyObject *v = _mysql_ResultObject_fetch_row(self, NULL);
		if (!v) goto error;
		if (v == Py_None) {
			Py_DECREF(v);
			if (_PyTuple_Resize(&r, i, 0) == -1)
				goto error;
			return r;
		}
		PyTuple_SET_ITEM(r, i, v);
	}
	return r;
  error:
	Py_XDECREF(r);
	return NULL;
}

static PyObject *
_mysql_get_client_info(self, args)
	PyObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_client_info());
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
	return (PyObject *) _mysql_ResultObject_New(self, result, 0);
}

static PyObject *
_mysql_ConnectionObject_list_fields(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	_mysql_ResultObject *r;
	MYSQL_RES *result;
	char *wild = NULL, *table;

	if (!PyArg_ParseTuple(args, "s|s:list_fields", &table, &wild)) return NULL;
	Py_BEGIN_ALLOW_THREADS
        result = mysql_list_fields(&(self->connection), table, wild);
	Py_END_ALLOW_THREADS
        if (!result) return _mysql_Exception(self);
	return (PyObject *) _mysql_ResultObject_New(self, result, 0);
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
	return (PyObject *) _mysql_ResultObject_New(self, result, 0);
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
	return (PyObject *) _mysql_ResultObject_New(self, result, 0);
}

static PyObject *
_mysql_ConnectionObject_num_fields(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyInt_FromLong((long)mysql_num_fields(&(self->connection)));
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
_mysql_ConnectionObject_row_tell(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	unsigned int r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(self->connection));
	Py_END_ALLOW_THREADS
	return PyInt_FromLong((long)r);
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
	unsigned int n;

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
	Py_DECREF(self->converter);
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
	unsigned int offset;
	if (!PyArg_ParseTuple(args, "i:data_seek", &offset)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	mysql_data_seek(self->result, offset);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static void
_mysql_ResultObject_dealloc(self)
	_mysql_ResultObject *self;
{
	int i;
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
	{"close",           (PyCFunction)_mysql_ConnectionObject_close, 0},
	{"dump_debug_info", (PyCFunction)_mysql_ConnectionObject_dump_debug_info, 0},
	{"error",           (PyCFunction)_mysql_ConnectionObject_error, 0},
	{"errno",           (PyCFunction)_mysql_ConnectionObject_errno, 0},
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
	{"num_fields",      (PyCFunction)_mysql_ConnectionObject_num_fields, 0},
	{"ping",            (PyCFunction)_mysql_ConnectionObject_ping, 0},
	{"query",           (PyCFunction)_mysql_ConnectionObject_query, 1},
	{"row_tell",        (PyCFunction)_mysql_ConnectionObject_row_tell, 0},
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
	{"describe",        (PyCFunction)_mysql_ResultObject_describe, 0},
	{"fetch_row",       (PyCFunction)_mysql_ResultObject_fetch_row, 0},
	{"fetch_rows",      (PyCFunction)_mysql_ResultObject_fetch_rows, 1},
	{"fetch_all_rows",  (PyCFunction)_mysql_ResultObject_fetch_all_rows, 0},
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
	PyObject_HEAD_INIT(&PyType_Type)
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
	PyObject_HEAD_INIT(&PyType_Type)
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
	{ "connect", _mysql_connect, METH_VARARGS | METH_KEYWORDS },
	{ "escape_row", _mysql_escape_row, METH_VARARGS },
	{ "escape_string", _mysql_escape_string, METH_VARARGS },
	{ "get_client_info", _mysql_get_client_info },
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
which convert a string to some value. This is used by the various\n\
fetch methods. Types not mapped are returned as strings. Numbers are\n\
all converted reasonably, except DECIMAL.\n\
\n\
result.describe() produces a DB API description of the rows.\n\
\n\
escape_row() accepts a sequence of items, converts them to strings, does\n\
mysql_escape_string() on them, and returns them as a tuple.\n\
\n\
result.field_flags() returns the field flags for the result.\n\
\n\
result.fetch_row() fetches the next row as a tuple of objects. MySQL\n\
returns strings, but fetch_row() does data conversion according to\n\
type_conv.\n\
\n\
result.fetch_rows(n) is like fetch_row() but fetches up to n rows and\n\
returns a tuple of rows.\n\
\n\
result.fetch_all_rows() is like fetch_rows() but fetchs all rows.\n\
\n\
For everything else, check the MySQL docs." ;

void
init_mysql()
{
	PyObject *dict, *module;
	module = Py_InitModule3("_mysql", _mysql_methods, _mysql___doc__);

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
	if (!(_mysql_NULL = PyString_FromString("NULL")))
		goto error;
	if (PyDict_SetItemString(dict, "NULL", _mysql_NULL)) goto error;
  error:
	if (PyErr_Occurred())
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
	return;
}


