#!/usr/bin/python

__version__ = """$Revision$"""[11:-2]

# No, HyperText is not publicly available, yet.
# Let me know if it looks useful.

from HyperText.HTML40 import STYLE, CSSRule
from HyperText.Documents import Document

class MyDoc(Document):

    style = STYLE(
	CSSRule("BODY", background_color="white", color="black"),
	CSSRule("CAPTION", font="italic"),
	CSSRule(".C", font_family="typewriter"),
	CSSRule(".Py", font_family="typewriter", color="#004000"),
	type="text/css")

def CTD(*args):
    from HyperText.HTML40 import P, TD
    return TD(apply(P, args, {'klass': 'C'}))

def PyTD(*args):
    from HyperText.HTML40 import P, TD
    return TD(apply(P, args, {'klass': 'Py'}))

def MapTR(c, py):
    from HyperText.HTML40 import TR
    return TR(CTD(c), PyTD(py))

def BDT(*args):
    from HyperText.HTML40 import B, DT
    return DT(apply(B, args))

def main():
    from HyperText.HTML40 import TITLE, META, H1, H2, H3, A, P, UL, LI, TT, \
	 TABLE, TR, TD, TH, CAPTION, BR, DIV, CENTER, DL, DT, DD, EM, PRE
    import license
    d = MyDoc()
    d.head.append(
	TITLE("MySQLdb: a Python interface for MySQL"),
	META(name="keywords", content="MySQL,Python"))
    d.body.append(
	H1("MySQLdb: a Python interface for MySQL"),
	P("Brought to you by ",
	  A("Andy Dustman",
	    href="mailto:adustman@comstar.net"), " and ",
	  A("Comstar Commnuications Corporation",
	    href="http://www.comstar.net/"), "."),
	P("Please read the ",
	  A("licensing agreement",
	    href="license.py"), " with it's lack of warranty\n" \
	  "statement."),
	H2("Overview"),
	P("MySQLdb is an interface to the popular ",
	  A("MySQL", href="http://www.mysql.net/mirrors.html"),
	  " database server for ",
	  A("Python", href="http://www.python.org/"), ". The " \
	  "design goals are:"),
	UL(LI("Compliance with Python ",
	      A("database API version 2.0",
		href="http://www.python.org/topics/database/DatabaseAPI-2.0.html"),
	      ),
	   LI("Thread-safety"),
	   LI("Thread-friendliness (threads will not block each other)"),
	   LI("Compatibility with MySQL 3.22")),
	P("This module should be mostly compatible with an older interface\n" \
	  "written by Joe Skinner and others. However, the older version\n" \
	  "is a) not thread-friendly, b) written for MySQL 3.21, c)\n" \
	  "apparently not actively maintained. No code from that version\n" \
	  "is used in MySQLdb. MySQLdb is distributed free of charge\n" \
	  "under a license derived from the Python license."),
	P("Notes: MySQL 3.22.11 is known NOT to work. Only versions\n" \
	  "3.22.19 and up are known to work. If you have an older version\n" \
	  "you should seriously consider upgrading for it's own sake.\n"),
	P("If you work out\n" \
	  "an installation routine for Windows, please contact the author."),
	P("This module works better if you have the ",
	  A("DateTime",
	    href="http://starship.skyport.net/~lemburg/mxDateTime.html"),
	  "\nmodule, but will function without it."),
	P("The web page documentation may be slightly ahead of the\n" \
	  "latest release and may reflect features of the next release."),
	H2("_mysql -- low-level interface"),
	P("If you want to write applications which are portable across\n" \
	  "databases, avoid using this module directly. ", TT("_mysql"),
	  " provides an\n" \
	  "interface which mostly implements the MySQL C API. For more\n" \
	  "information, see the MySQL documentation, section 18.\n" \
	  "The documentation for this module is intentionally weak\n" \
	  "because you probably should use the higher-level ",
	  TT("MySQLdb"), " module. If you really need it, use the\n",
	  "standard MySQL docs and transliterate as necessary."),
	P("The C API has been wrapped in an object-oriented way. The\n" \
	  "only MySQL data structures which are implemented are the\n",
	  TT("MYSQL"), " (database connection handle) and ",
	  TT("MYSQL_RES"), " (result handle) types. In general, any\n" \
	  "function which takes ", TT("MYSQL *mysql"), " as an\n" \
	  "argument is now a method of the connection object, and\n" \
	  "any function which takes ", TT("MYSQL_RES *result"),
	  "\nas an argument is a method of the result object.\n" \
	  "Functions requiring none of the MySQL data structures\n" \
	  "are implemented as functions in the module. Functions\n" \
	  "requiring one of the other MySQL data structures are\n" \
	  "generally not implemented. Deprecated functions are not\n" \
	  "implemented. In all cases, the ", TT("mysql_"), " prefix\n" \
	  "is dropped from the name."),
	CENTER(TABLE(
	    CAPTION("MySQL C API function mapping"),
	    TR(TH("C API"), TH("_mysql")),
	    MapTR("mysql_affected_rows()",
		  "_mysql.affected_rows()"),
	    MapTR("mysql_close()",
		  "conn.close()"),
	    MapTR("mysql_connect()",
		  "_mysql.connect()"),
	    MapTR("mysql_data_seek()",
		  "result.data_seek()"),
	    MapTR("mysql_debug()",
		  "_mysql.debug()"),
	    MapTR("mysql_dump_debug_info",
		  "conn.dump_debug_info()"),
	    MapTR("mysql_escape_string()",
		  "_mysql.escape_string()"),
	    MapTR("mysql_fetch_row()",
		  DIV("result.fetch_row()", BR(),
		      "result.fetch_rows()", BR(),
		      "result.fetch_all_rows()",
		      klass="Py")),
	    MapTR("mysql_get_client_info()",
		  "_mysql.get_client_info()"),
	    MapTR("mysql_get_host_info()",
		  "conn.get_host_info()"),
	    MapTR("mysql_get_proto_info()",
		  "conn.get_proto_info()"),
	    MapTR("mysql_get_server_info()",
		  "conn.get_server_info()"),
	    MapTR("mysql_info()",
		  "conn.info()"),
	    MapTR("mysql_insert_id()",
		  "conn.insert_id()"),
	    MapTR("mysql_list_dbs()",
		  "conn.list_dbs()"),
	    MapTR("mysql_list_fields()",
		  "conn.list_fields()"),
	    MapTR("mysql_list_processes()",
		  "conn.list_processes()"),
	    MapTR("mysql_list_tables()",
		  "conn.list_tables()"),
	    MapTR("mysql_num_fields()",
		  "result.num_fields()"),
	    MapTR("mysql_num_rows()",
		  "result.num_rows()"),
	    MapTR("mysql_ping()",
		  "conn.ping()"),
	    MapTR("mysql_query()",
		  "conn.query()"),
	    MapTR("mysql_real_connect()",
		  "_mysql.connect()"),
	    MapTR("mysql_real_query()",
		  "conn.query()"),
	    MapTR("mysql_row_seek()",
		  "result.row_seek()"),
	    MapTR("mysql_row_tell()",
		  "result.row_tell()"),
	    MapTR("mysql_select_db()",
		  "conn.select_db()"),
	    MapTR("mysql_stat()",
		  "conn.stat()"),
	    MapTR("mysql_store_result()",
		  "conn.store_result()"),
	    MapTR("mysql_thread_id()",
		  "conn.thread_id()"),
	    MapTR("mysql_use_result()",
		  "conn.use_result()"),
	    MapTR("CLIENT_*",
		  "_mysql.CLIENT.*"),
	    MapTR("CR_*",
		  "_mysql.CR.*"),
	    MapTR("ER_*",
		  "_mysql.ER.*"),
	    MapTR("FIELD_TYPE_*",
		  "_mysql.FIELD_TYPE.*"),
	    MapTR("FLAG_*",
		  "_mysql.FLAG.*"),
	    border=1)),
	H2("MySQLdb -- DB API interface"),
	P(TT("MySQLdb"), " is a thin Python wrapper around ",
	  TT("_mysql"), " which makes it compatible with the Python\n" \
	  "DB API interface (version 2). In reality, a fair amount\n" \
	  "of the code which implements the API is in ",
	  TT("_mysql"), " for the sake of efficiency."),
	P(A("The DB API specification",
	    href="http://www.python.org/topics/database/DatabaseAPI-2.0.html"),
	  " should be your primary guide for\n" \
	  "using this module. Only deviations from the spec and other\n" \
	  "database-dependent things will be documented here.\n" \
	  "Note that all symbols from ", TT("_mysql"), " are imported\n" \
	  "into this module. Mostly these are the required exceptions\n" \
	  "the constant classes, and a very few functions."),
	DL(BDT("connect(parameters...)"),
	   DD(P("Constructor for creating a connection to the database.\n" \
		"Returns a Connection Object. Parameters are the same as\n" \
		"for the MySQL C API. Note that all parameters must be\n" \
		"specified as keyword arguments! The default value for\n" \
		"each parameter is NULL or zero, as appropriate. Consult\n" \
		"the MySQL documentation for more details. The important\n" \
		"parameters are:"),
	      P(DL(BDT("host"),
		   DD("name of host to connect to"),
		   BDT("user"),
		   DD("user to authenticate as"),
		   BDT("passwd"),
		   DD("password to authenticate with"),
		   BDT("db"),
		   DD("database to use")))),
	   BDT("apilevel"),
	   DD(P("String constant stating the supported DB API level. '2.0'")),
	   BDT("threadsafety"),
	   DD(P("Integer constant stating the level of thread safety\n" \
		"the interface supports. Set to 1, which means:\n" \
		"Threads may share the module, but not connections.\n" \
		"This is the practice recommended by the MySQL\n" \
		"documentation. However, it should be safe to share\n" \
		"a connection between two threads provided only one\n" \
		"thread at a time uses it (i.e. a mutex is employed).\n" \
		"Note that this is only safe if the threads are using.\n",
		TT("mysql_store_result()"), " as opposed to ",
		TT("mysql_use_result()"), ". The latter is not recommended\n" \
		"for threaded applications. See the MySQL documentation\n" \
		"for more details.")),
	   BDT("paramstyle"),
	   DD(P("String constant stating the type of parameter marker\n" \
		"formatting expected by the interface. Set to \n" \
		"'format' = ANSI C printf format codes, \n" \
		"e.g. '...WHERE name=%s'. If a mapping object is used\n" \
		"for ", TT("conn.execute()"), ", then the interface\n" \
		"actually uses 'pyformat' = Python extended format codes,\n" \
		"e.g. '...WHERE name=%(name)s'. However, the API does not\n" \
		"presently allow the specification of more than one style\n" \
		"in ", TT("paramstyle"), ".")),
	   BDT("type_conv"),
	   DD(P("A dictionary mapping MySQL types (from ",
		TT("FIELD_TYPE.*"), ") to callable Python objects\n" \
		"(usually functions) which convert from a string to\n" \
		"the desired type. This is imported from the\n",
		TT("_mysql"), " module, where it is initialized with\n" \
		"reasonable defaults for most types. ", TT("MySQLdb"),
		"\nalso adds a few additional functions, using some of\n" \
		"the factory functions from the\n",
		A("DateTime",
		  href="http://starship.skyport.net/~lemburg/mxDateTime.html"),
		" module. Several non-standard types (SET, ENUM) are\n" \
		"returned as strings, which is how MySQL returns all\n"
		"columns."))),
	H3("Connection Objects"),
	DL(BDT("commit()"),
	   DD(P("MySQL does not support transactions, so this method\n" \
		"successfully does nothing.")),
	   BDT("rollback()"),
	   DD(P("MySQL does not support transactions, so this method\n" \
		"is not defined. ", EM("Note that the older MySQLmodule\n"\
		"does define this method, which sucessfully does\n" \
		"nothing. This is dangerous behavior, as a succesful\n" \
                "rollback indicates that the current transaction was\n" \
                "backed out, which is not true, and fails to notify\n" \
		"the programmer that the database now needs to be\n" \
		"cleaned up by other means."))),
	   BDT("cursor(parameters...)"),
	   DD(P("MySQL does not support cursors; however, cursors are\n" \
		"fairly easily emulated. Any positional or keyword\n" \
		"arguments are passed to the cursor constructor.")),
	   BDT("db"),
	   DD(P("The ", TT("_mysql"), " connection object. This may be\n" \
		"used in case it is necessary to employ some\n" \
		"MySQL-specific functions.")),
	   BDT("CursorClass"),
	   DD(P("The class used to create a new cursor with\n",
		TT("conn.cursor()"), ". If you subclass the Connection\n" \
		"object, you will probably want to change this."))),
	H3("Cursor Objects"),
	P("Cursor objects support some parameters when created, usually\n" \
	  "passed by ", TT("conn.cursor()"), ". They are also attributes\n" \
	  "of the cursor, but it is probably best to not mess with them."),
	DL(BDT("name=''"),
	   DD("Names the cursor, which is pretty useless."),
	   BDT("use=0"),
	   DD("Cursor objects normally employ ",
	      TT("mysql_store_result()"), ". Setting this value to a\n" \
	      "true value will cause it to use\n",
	      TT("mysql_use_result()"), " instead. See the MySQL\n" \
	      "documentation for more information."),
	   BDT("warnings=1"),
	   DD("If true, detects warnings and raises the ",
	      TT("Warning"), " exception.")),
	P("While it is possible to create Cursor objects with the\n" \
	  "class constructor, this is not recommended, so they are\n" \
	  "hidden as _Cursor objects."),
	DL(BDT("callproc()"),
	   DD(P("Not implemented.")),
	   BDT("nextset()"),
	   DD(P("Not implemented.")),
	   BDT("setinputsizes()"),
	   DD(P("Does nothing, successfully.")),
	   BDT("setoutputsizes()"),
	   DD(P("Does nothing, successfully.")),
	   BDT("execute(query[,parameters])"),
	   BDT("executemany(query,[,parameters])"),
	   DD(P("These methods work as described in the API. However,\n" \
		"it should be noted that the interface relies on the\n",
		TT("__str__"), " method of each parameter. That is,\n" \
		"each parameter is converted to a string when passed\n" \
		"to MySQL. This presents a problem for the various\n" \
		"date and time columns: ", TT("__str__"), " for\n" \
		"DateTime objects includes fractional seconds, which\n" \
		"MySQL (up to 3.22.20a, at least), considers illegal\n" \
		"input, and so zeros the field.")),
	   BDT("format_DATE(d)"),
	   BDT("format_TIME(d)"),
	   BDT("format_TIMESTAMP(d)"),
	   DD(P("These functions all take a DateTime object as input and\n" \
		"return an appropriately formatted string. They are\n" \
		"intended for use with the ", TT("executeXXX()"),
		" methods."))
	   ),
	H2("General Design Notes"),
	P("In general, it is probably wise to not directly interact\n" \
	  "with the DB API except for small applicatons.\n" \
	  "Databases, even SQL databases, vary widely\n" \
	  "in capabilities and may have non-standard features. The DB API\n" \
	  "does a good job of providing a reasonably portable interface\n" \
	  "but some methods are non-portable. Specifically, the parameters\n" \
	  "accepted by ", TT("connect()"), " are completely\n" \
	  "implementation-dependent."),
	P("If you\n" \
	  "believe your application may need to run on several\n" \
	  "different databases, the author recommends the following\n" \
	  "approach, based on personal experience: Write a simplified\n" \
	  "API for your application which implements the specific\n" \
	  "queries and operations your application needs to perform.\n" \
	  "Implement this API\n" \
	  "as a base class which should be have few database\n" \
	  "dependencies, and then derive a subclass from this\n" \
	  "which implements the necessary dependencies. In this way,\n" \
	  "porting your application to a new database should be a\n" \
	  "relatively simple matter of creating a new subclass,\n" \
	  "assuming the new database is reasonably standard."),
	H2("License"),
	P(PRE(license.__doc__)),
	P("$Id$"))
    print d

if __name__ == "__main__": main()
