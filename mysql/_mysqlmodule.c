#include "Python.h"
#include "structmember.h"
#include "mysql.h"

static PyObject *_mysql_Warning;
static PyObject *_mysql_Error;
static PyObject *_mysql_InterfaceError; 
static PyObject *_mysql_DataError;
static PyObject *_mysql_OperationalError; 
static PyObject *_mysql_IntegrityError; 
static PyObject *_mysql_InternalError; 
static PyObject *_mysql_ProgrammingError;
 
typedef struct {
	PyObject_HEAD
	MYSQL connection;
	int open;
} _mysql_ConnectionObject;

extern PyTypeObject _mysql_ConnectionObject_Type;

typedef struct {
	PyObject_HEAD
	PyObject *conn;
	MYSQL *connection;
	MYSQL_RES *result;
} _mysql_ResultObject;

extern PyTypeObject _mysql_ResultObject_Type;

typedef struct {
	PyObject_HEAD
	_mysql_ResultObject *result;
	MYSQL_FIELD *field;
} _mysql_FieldObject;

extern PyTypeObject _mysql_FieldObject_Type;

PyObject *
_mysql_Exception(c)
	_mysql_ConnectionObject *c;
{
	PyObject *t;
	if (!(t = PyTuple_New(2))) return NULL;
	PyTuple_SET_ITEM(t, 0, PyInt_FromLong((long)mysql_errno(&(c->connection))));
	PyTuple_SET_ITEM(t, 1, PyString_FromString(mysql_error(&(c->connection))));
	PyErr_SetObject(_mysql_Error, t);
	Py_DECREF(t);
	return NULL;
}

static PyObject *
_mysql_connect(self, args, kwargs)
	PyObject *self;
	PyObject *args;
	PyObject *kwargs;
{
	MYSQL *conn;
	char *host = NULL, *user = NULL, *passwd = NULL,
		*db = NULL, *unix_socket = NULL;
	uint port = 3306;
	uint client_flag = 0;
	static char *kwlist[] = { "host", "user", "passwd", "db", "port",
				  "unix_socket", "client_flag",
				  NULL } ;
	_mysql_ConnectionObject *c = PyObject_NEW(_mysql_ConnectionObject,
					      &_mysql_ConnectionObject_Type);
	if (c == NULL) return NULL;
	c->open = 0;
	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ssssisi:connect",
					 kwlist,
					 &host, &user, &passwd, &db,
					 &port, &unix_socket, &client_flag))
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
_mysql_escape(self, args)
	PyObject *self;
	PyObject *args;
{
	PyObject *str;
	char *in, *out;
	int len, size;
	PyObject *o;
	if (!PyArg_ParseTuple(args, "s#:escape", &in, &size)) return NULL;
	str = PyString_FromStringAndSize((char *) NULL, size*2+1);
	if (!str) return PyErr_NoMemory();
	out = PyString_AS_STRING(str);
	len = mysql_escape_string(out, in, size);
	if (_PyString_Resize(&str, len) < 0) return NULL;
	return (str);
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
_mysql_get_client_info(self, args)
	PyObject *self;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_get_client_info());
}

static PyObject *
_mysql_ResultObject_fetch_row(self, args)
	_mysql_ResultObject *self;
	PyObject *args;
{
	unsigned int n, i;
	unsigned long *length;
	PyObject *r;
	MYSQL_ROW row;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	row = mysql_fetch_row(self->result);
        Py_END_ALLOW_THREADS;
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
			v = PyString_FromStringAndSize(row[i], length[i]);
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
	_mysql_ResultObject *r;
	char *wild = NULL;

	if (!PyArg_ParseTuple(args, "|s:list_dbs", &wild)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_list_dbs(&(self->connection), wild);
	Py_END_ALLOW_THREADS
        if (!(r->result)) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &(self->connection);
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
}

static PyObject *
_mysql_ConnectionObject_list_fields(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	_mysql_ResultObject *r;
	char *wild = NULL, *table;

	if (!PyArg_ParseTuple(args, "s|s:list_fields", &table, &wild)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_list_fields(&(self->connection), table, wild);
	Py_END_ALLOW_THREADS
        if (!(r->result)) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &(self->connection);
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
}

static PyObject *
_mysql_ConnectionObject_list_processes(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	_mysql_ResultObject *r;

	if (!PyArg_NoArgs(args)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_list_processes(&(self->connection));
	Py_END_ALLOW_THREADS
        if (!(r->result)) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &self->connection;
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
}

static PyObject *
_mysql_ConnectionObject_list_tables(self, args)
	_mysql_ConnectionObject *self;
	PyObject *args;
{
	_mysql_ResultObject *r;
	char *wild = NULL;

	if (!PyArg_ParseTuple(args, "|s:list_tables", &wild)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_list_tables(&(self->connection), wild);
	Py_END_ALLOW_THREADS
        if (!(r->result)) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &self->connection;
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
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
	_mysql_ResultObject *r;
	unsigned int n;

	if (!PyArg_NoArgs(args)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_store_result(&(self->connection));
	Py_END_ALLOW_THREADS
	n = mysql_num_fields(&(self->connection));
        if (!(r->result) && n) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &self->connection;
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
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
	_mysql_ResultObject *r;

	if (!PyArg_NoArgs(args)) return NULL;
	if (!(r = PyObject_NEW(_mysql_ResultObject, &_mysql_ResultObject_Type)))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
        r->result = mysql_use_result(&(self->connection));
	Py_END_ALLOW_THREADS
        if (!(r->result)) {
		Py_DECREF(r);
		return _mysql_Exception(self);
	}
	r->connection = &(self->connection);
	r->conn = (PyObject *) self;
	Py_INCREF(self);
	return (PyObject *) r;
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
_mysql_ResultObject_seek(self, args)
     _mysql_ResultObject *self;
     PyObject *args;
{
	unsigned int offset;
	if (!PyArg_ParseTuple(args, "i:seek", &offset)) return NULL;
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
	mysql_free_result(self->result);
	Py_DECREF(self->conn);
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

static void
_mysql_FieldObject_dealloc(self)
	_mysql_FieldObject *self;
{
	Py_DECREF(self->result);
	PyMem_Free((char *)self);
}

static PyObject *
_mysql_FieldObject_repr(self)
	_mysql_ResultObject *self;
{
	char buf[300];
	sprintf(buf, "<field object at %lx>",
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
	{"list_dbs",        (PyCFunction)_mysql_ConnectionObject_list_dbs, 1},
	{"list_fields",     (PyCFunction)_mysql_ConnectionObject_list_fields, 1},
	{"list_processes",  (PyCFunction)_mysql_ConnectionObject_list_processes, 1},
	{"list_tables",     (PyCFunction)_mysql_ConnectionObject_list_tables, 1},
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
	{NULL} /* Sentinel */
};

static PyMethodDef _mysql_ResultObject_methods[] = {
	{"describe",        (PyCFunction)_mysql_ResultObject_describe, 0},
	{"num_rows",        (PyCFunction)_mysql_ResultObject_num_rows, 0},
	{"fetch_row",       (PyCFunction)_mysql_ResultObject_fetch_row, 0},
	{NULL,              NULL} /* sentinel */
};

static struct memberlist _mysql_ResultObject_memberlist[] = {
	{NULL} /* Sentinel */
};

static PyMethodDef _mysql_FieldObject_methodsp[] = {
	{NULL,              NULL} /* sentinel */
};

static struct memberlist _mysql_FieldObject_memberlist[] = {
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
				"can't delete file attributes");
		return -1;
	}
	return PyMember_Set((char *)c, _mysql_ConnectionObject_memberlist, name, v);
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
	0, /* tp_setattr */
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
	0, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_ResultObject_repr, /* tp_repr */
};

PyTypeObject _mysql_FieldObject_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"result",
	sizeof(_mysql_FieldObject),
	0,
	(destructor)_mysql_FieldObject_dealloc, /* tp_dealloc */
	0, /*tp_print*/
	0, /*(getattrfunc)_mysql_FieldObject_getattr, /* tp_getattr */
	0, /* tp_setattr */
	0, /*tp_compare*/
	(reprfunc)_mysql_FieldObject_repr, /* tp_repr */
};

static PyMethodDef
_mysql_methods[] = {
	{ "connect", _mysql_connect, METH_VARARGS | METH_KEYWORDS },
	{ "escape", _mysql_escape, METH_VARARGS },
	{ "get_client_info", _mysql_get_client_info, METH_VARARGS },
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

void
init_mysql()
{
	PyObject *dict, *module;
	module = Py_InitModule("_mysql", _mysql_methods);

	dict = PyModule_GetDict(module);
	if ((_mysql_Warning = _mysql_NewException(dict, "Warning", NULL)) == NULL) goto error;
	if ((_mysql_Error = _mysql_NewException(dict, "Error", NULL)) == NULL) goto error;
	if ((_mysql_DataError = _mysql_NewException(dict, "DataError", _mysql_Error)) == NULL) goto error;
	if ((_mysql_OperationalError = _mysql_NewException(dict, "OperationalError", _mysql_Error)) == NULL) goto error;
	if ((_mysql_IntegrityError = _mysql_NewException(dict, "IntegrityError", _mysql_Error)) == NULL) goto error;
	if ((_mysql_InternalError = _mysql_NewException(dict, "InternalError", _mysql_Error)) == NULL) goto error;
	if ((_mysql_ProgrammingError = _mysql_NewException(dict, "ProgrammingError", _mysql_Error)) == NULL) goto error;
  error:
	if (PyErr_Occurred())
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
	return;
}


