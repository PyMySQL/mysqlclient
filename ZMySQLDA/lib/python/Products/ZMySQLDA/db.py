##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

'''$Id$'''
__version__='$Revision$'[11:-2]

import _mysql
from _mysql_exceptions import OperationalError, NotSupportedError
MySQLdb_version_required = (0,9,0)

_v = getattr(_mysql, 'version_info', (0,0,0))
if _v < MySQLdb_version_required:
    raise NotSupportedError, \
	"ZMySQLDA requires at least MySQLdb %s, %s found" % \
	(MySQLdb_version_required, _v)

from MySQLdb.converters import conversions
from MySQLdb.constants import FIELD_TYPE, CR, CLIENT
from Shared.DC.ZRDB.TM import TM
from DateTime import DateTime

import string, sys
from string import strip, split, find, upper, rfind
from time import time

hosed_connection = (
    CR.SERVER_GONE_ERROR,
    CR.SERVER_LOST
    )

key_types = {
    "PRI": "PRIMARY KEY",
    "MUL": "INDEX",
    "UNI": "UNIQUE",
    }

field_icons = "bin", "date", "datetime", "float", "int", "text", "time"

icon_xlate = {
    "varchar": "text", "char": "text",
    "enum": "what", "set": "what",
    "double": "float", "numeric": "float",
    "blob": "bin", "mediumblob": "bin", "longblob": "bin",
    "tinytext": "text", "mediumtext": "text",
    "longtext": "text", "timestamp": "datetime",
    "decimal": "float", "smallint": "int",
    "mediumint": "int", "bigint": "int",
    }

type_xlate = {
    "double": "float", "numeric": "float",
    "decimal": "float", "smallint": "int",
    "mediumint": "int", "bigint": "int",
    "int": "int", "float": "float",
    "timestamp": "datetime", "datetime": "datetime",
    "time": "datetime",
    }
    
def _mysql_timestamp_converter(s):
	if len(s) < 14:
		s = s + "0"*(14-len(s))
        parts = map(int, (s[:4],s[4:6],s[6:8],
                          s[8:10],s[10:12],s[12:14]))
	return DateTime("%04d-%02d-%02d %02d:%02d:%02d" % tuple(parts))

def DateTime_or_None(s):
    try: return DateTime(s)
    except: return None

def int_or_long(s):
    try: return int(s)
    except: return long(s)

class DB(TM):

    Database_Connection=_mysql.connect
    Database_Error=_mysql.Error

    defs={
        FIELD_TYPE.CHAR: "i", FIELD_TYPE.DATE: "d",
        FIELD_TYPE.DATETIME: "d", FIELD_TYPE.DECIMAL: "n",
        FIELD_TYPE.DOUBLE: "n", FIELD_TYPE.FLOAT: "n", FIELD_TYPE.INT24: "i",
        FIELD_TYPE.LONG: "i", FIELD_TYPE.LONGLONG: "l",
        FIELD_TYPE.SHORT: "i", FIELD_TYPE.TIMESTAMP: "d",
        FIELD_TYPE.TINY: "i", FIELD_TYPE.YEAR: "i",
        }

    conv=conversions.copy()
    conv[FIELD_TYPE.LONG] = int_or_long
    conv[FIELD_TYPE.DATETIME] = DateTime_or_None
    conv[FIELD_TYPE.DATE] = DateTime_or_None
    conv[FIELD_TYPE.DECIMAL] = float
    del conv[FIELD_TYPE.TIME]

    _p_oid=_p_changed=_registered=None

    def __init__(self,connection):
        self.connection=connection
        self.kwargs = kwargs = self._parse_connection_string(connection)
        self.db=apply(self.Database_Connection, (), kwargs)
	self.transactions = self.db.server_capabilities & CLIENT.TRANSACTIONS
        if self._try_transactions == '-':
            self.transactions = 0
        elif not self.transactions and self._try_transactions == '+':
            raise NotSupportedError, "transactions not supported by this server"

    def _parse_connection_string(self, connection):
        kwargs = {'conv': self.conv}
        items = split(connection)
        if not items: return kwargs
        db_host, items = items[0], items[1:]
        if '@' in db_host:
            db, host = split(db_host,'@',1)
            kwargs['db'] = db
            if ':' in host:
                host, port = split(host,':',1)
                kwargs['port'] = int(port)
            kwargs['host'] = host
        else:
            kwargs['db'] = db_host
        if kwargs['db'][0] in ('+', '-'):
            self._try_transactions = kwargs['db'][0]
            kwargs['db'] = kwargs['db'][1:]
        else:
            self._try_transactions = None
        if not items: return kwargs
        kwargs['user'], items = items[0], items[1:]
        if not items: return kwargs
        kwargs['passwd'], items = items[0], items[1:]
        if not items: return kwargs
        kwargs['unix_socket'], items = items[0], items[1:]
        return kwargs
        
    def tables(self, rdb=0,
               _care=('TABLE', 'VIEW')):
        r=[]
        a=r.append
	self.db.query("SHOW TABLES")
	result = self.db.store_result()
	while 1:
	    row = result.fetch_row(1)
	    if not row: break
            a({'TABLE_NAME': row[0][0], 'TABLE_TYPE': 'TABLE'})
        return r

    def columns(self, table_name):
        from string import join
        try:
            # Field, Type, Null, Key, Default, Extra
            self.db.query('SHOW COLUMNS FROM %s' % table_name)
            c=self.db.store_result()
        except:
            return ()
        r=[]
        for Field, Type, Null, Key, Default, Extra in c.fetch_row(0):
            info = {}
            field_default = Default and "DEFAULT %s"%Default or ''
            if Default: info['Default'] = Default
            if '(' in Type:
                end = rfind(Type,')')
                short_type, size = split(Type[:end],'(',1)
                if short_type not in ('set','enum'):
                    if ',' in size:
                        info['Scale'], info['Precision'] = \
                                       map(int, split(size,',',1))
                    else:
                        info['Scale'] = int(size)
            else:
                short_type = Type
            if short_type in field_icons:
                info['Icon'] = short_type
            else:
                info['Icon'] = icon_xlate.get(short_type, "what")
            info['Name'] = Field
            info['Type'] = type_xlate.get(short_type,'string')
            info['Extra'] = Extra,
            info['Description'] = join([Type, field_default, Extra or '',
                                        key_types.get(Key, Key or ''),
                                        Null != 'YES' and 'NOT NULL' or '']),
            info['Nullable'] = (Null == 'YES') and 1 or 0
            if Key:
                info['Index'] = 1
            if Key == 'PRI':
                info['PrimaryKey'] = 1
                info['Unique'] = 1
            elif Key == 'UNI':
                info['Unique'] = 1
            r.append(info)
        return r

    def query(self,query_string, max_rows=1000):
	if self.transactions: self._register()
        desc=None
        result=()
        db=self.db
        try:
            for qs in filter(None, map(strip,split(query_string, '\0'))):
                qtype = upper(split(qs, None, 1)[0])
                if qtype == "SELECT" and max_rows:
                    qs = "%s LIMIT %d" % (qs,max_rows)
                    r=0
                db.query(qs)
                c=db.store_result()
                if desc is not None:
                    if c and (c.describe() != desc):
                        raise 'Query Error', (
                            'Multiple select schema are not allowed'
                            )
                if c:
                    desc=c.describe()
                    result=c.fetch_row(max_rows)
                else:
                    desc=None
                    
        except OperationalError, m:
            if m[0] not in hosed_connection: raise
            # Hm. maybe the db is hosed.  Let's restart it.
	    db=self.db=apply(self.Database_Connection, (), self.kwargs)
            return self.query(query_string, max_rows)

        if desc is None: return (),()

        items=[]
        func=items.append
        defs=self.defs
        for d in desc:
            item={'name': d[0],
                  'type': defs.get(d[1],"t"),
                  'width': d[2],
                  'null': d[6]
                 }
            func(item)
        return items, result

    def string_literal(self, s): return self.db.string_literal(s)

    def _begin(self, *ignored):
        self.db.query("BEGIN")
	self.db.store_result()
        
    def _finish(self, *ignored):
        self.db.query("COMMIT")
	self.db.store_result()

    def _abort(self, *ignored):
	self.db.query("ROLLBACK")
	self.db.store_result()
