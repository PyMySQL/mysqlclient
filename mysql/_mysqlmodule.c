#include "Python.h"
#include "structmember.h"
#include "mysql.h"

static PyObject *_mysql_Error;

typedef struct {
	PyObject_HEAD
	MYSQL connection;
	int open;
} _mysql_ConnectionObject;

extern PyTypeObject _mysql_ConnectionObject_Type;

#define MySQL_Exception(e,c) PyErr_SetString(e, mysql_error(&(c->connection)));

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
	conn = mysql_real_connect(&(c->connection), host, user, passwd, db,
				  port, unix_socket, client_flag);
	Py_END_ALLOW_THREADS ;
	if (!conn) {
		MySQL_Exception(_mysql_Error, c);
		Py_DECREF(c);
		return NULL;
	}
	c->open = 1;
	return (PyObject *) c;
}

static PyObject *
_mysql_ConnectionObject_close(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	mysql_close(&(c->connection));
        Py_END_ALLOW_THREADS
	c->open = 0;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_affected_rows(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyLong_FromUnsignedLongLong(mysql_affected_rows(&(c->connection)));
}

/*  static PyObject * */
/*  _mysql_ConnectionObject_seek(c, args) */
/*  	_mysql_ConnectionObject *c; */
/*  	PyObject *args; */
/*  { */
/*  	int offset; */
/*  	if (!PyArg_ParseTuple(args, "u", &offset)) return NULL; */
/*  	mysql_data_seek(&(c->connection), (unsigned int)offset); */
/*  	Py_INCREF(Py_None); */
/*  	return Py_None; */
/*  } */

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
_mysql_ConnectionObject_dump_debug_info(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	int err;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	err = mysql_dump_debug_info(&(c->connection));
	Py_END_ALLOW_THREADS
	if (err) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_errno(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyInt_FromLong((long)mysql_errno(&(c->connection)));
}

static PyObject *
_mysql_ConnectionObject_error(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	if (!PyArg_NoArgs(args)) return NULL;
	return PyString_FromString(mysql_error(&(c->connection)));
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
_mysql_get_client_info(self, args)
	PyObject *self;
	PyObject *args;
{
	if (!PyArg_ParseTuple(args, ":get_client_info")) return NULL;
	return PyString_FromString(mysql_get_client_info());
}

static PyObject *
_mysql_ConnectionObject_get_host_info(c)
	_mysql_ConnectionObject *c;
{
	return PyString_FromString(mysql_get_host_info(&(c->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_proto_info(c)
	_mysql_ConnectionObject *c;
{
	return PyInt_FromLong((long)mysql_get_proto_info(&(c->connection)));
}

static PyObject *
_mysql_ConnectionObject_get_server_info(c)
	_mysql_ConnectionObject *c;
{
	return PyString_FromString(mysql_get_server_info(&(c->connection)));
}

static PyObject *
_mysql_ConnectionObject_info(c)
	_mysql_ConnectionObject *c;
{
	char *s;
	s = mysql_info(&(c->connection));
	if (s) return PyString_FromString(s);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_insert_id(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	my_ulonglong r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(c->connection));
	Py_END_ALLOW_THREADS
	return PyLong_FromUnsignedLongLong(r);
}

static PyObject *
_mysql_ConnectionObject_kill(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	unsigned long pid;
	int r;
	if (!PyArg_ParseTuple(args, "i:kill", &pid)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_kill(&(c->connection), pid);
	Py_END_ALLOW_THREADS
	if (r) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_ping(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	int r;
	if (!PyArg_ParseTuple(args, ":ping")) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_ping(&(c->connection));
	Py_END_ALLOW_THREADS
	if (r) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_query(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	char *query;
	int len, r;
	if (!PyArg_ParseTuple(args, "s#:query", &query, &len)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_real_query(&(c->connection), query, len);
	Py_END_ALLOW_THREADS
	if (r) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_row_tell(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	unsigned int r;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_insert_id(&(c->connection));
	Py_END_ALLOW_THREADS
	return PyInt_FromLong((long)r);
}

static PyObject *
_mysql_ConnectionObject_select_db(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	char *db;
	int r;
	if (!PyArg_ParseTuple(args, "s:select_db", &db)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_select_db(&(c->connection), db);
	Py_END_ALLOW_THREADS
	if (r) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_shutdown(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	int r;
	if (!PyArg_ParseTuple(args, ":shutdown")) return NULL;
	Py_BEGIN_ALLOW_THREADS
	r = mysql_shutdown(&(c->connection));
	Py_END_ALLOW_THREADS
	if (r) {
		MySQL_Exception(_mysql_Error, c);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
_mysql_ConnectionObject_thread_id(c, args)
	_mysql_ConnectionObject *c;
	PyObject *args;
{
	unsigned long pid;
	if (!PyArg_NoArgs(args)) return NULL;
	Py_BEGIN_ALLOW_THREADS
	pid = mysql_thread_id(&(c->connection));
	Py_END_ALLOW_THREADS
	return PyLong_FromUnsignedLong(pid);
}

static void
_mysql_ConnectionObject_dealloc(c)
	_mysql_ConnectionObject *c;
{
	if (c->open) {
		Py_BEGIN_ALLOW_THREADS
		mysql_close(&(c->connection));
		Py_END_ALLOW_THREADS
	}
	PyMem_Free((char *) c);
}

static PyObject *
_mysql_ConnectionObject_repr(c)
	_mysql_ConnectionObject *c;
{
	char buf[300];
	sprintf(buf, "<%s connection to '%.256s' at %lx>",
		c->open ? "open" : "closed",
		c->connection.host,
		(long)c);
	return PyString_FromString(buf);
}

static PyMethodDef _mysql_ConnectionObject_methods[] = {
	{"affected_rows",   (PyCFunction)_mysql_ConnectionObject_affected_rows, 0},
	{"dump_debug_info", (PyCFunction)_mysql_ConnectionObject_dump_debug_info, 0},
	{"error",           (PyCFunction)_mysql_ConnectionObject_error, 0},
	{"errno",           (PyCFunction)_mysql_ConnectionObject_errno, 0},
	{"get_host_info",   (PyCFunction)_mysql_ConnectionObject_get_host_info, 0},
	{"get_proto_info",  (PyCFunction)_mysql_ConnectionObject_get_proto_info, 0},
	{"get_server_info", (PyCFunction)_mysql_ConnectionObject_get_server_info, 0},
	{"info",            (PyCFunction)_mysql_ConnectionObject_info, 0},
	{NULL,              NULL} /* sentinel */
};

static struct memberlist _mysql_ConnectionObject_memberlist[] = {
	{"open", T_INT, 0, RO},
	{"closed", T_INT, 0, RO},
	{NULL} /* Sentinel */
};

static PyObject *
_mysql_ConnectionObject_getattr(c, name)
	_mysql_ConnectionObject *c;
	char *name;
{
	PyObject *res;

	res = Py_FindMethod(_mysql_ConnectionObject_methods, (PyObject *)c, name);
	if (res != NULL)
		return res;
	PyErr_Clear();
	if (strcmp(name, "open") == 0)
		return PyInt_FromLong((long)(c->open));
	if (strcmp(name, "closed") == 0)
		return PyInt_FromLong((long)!(c->open));
	return PyMember_Get((char *)c, _mysql_ConnectionObject_memberlist, name);
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
	if ((_mysql_Error = _mysql_NewException(dict, "error", NULL)) == NULL) goto error;
  error:
	if (PyErr_Occurred())
		PyErr_SetString(PyExc_ImportError,
				"_mysql: init failed");
	return;
}


