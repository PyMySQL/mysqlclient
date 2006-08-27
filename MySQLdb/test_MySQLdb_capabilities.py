#!/usr/bin/env python
import test_capabilities
import unittest
import MySQLdb
import warnings

warnings.filterwarnings('error')

class test_MySQLdb(test_capabilities.DatabaseTest):

    db_module = MySQLdb
    connect_args = ()
    connect_kwargs = dict(db='test', read_default_file='~/.my.cnf',
                          charset='utf8', sql_mode="ANSI,STRICT_TRANS_TABLES,TRADITIONAL")
    create_table_extra = "ENGINE=INNODB CHARACTER SET UTF8"
    leak_test = False
    
    def quote_identifier(self, ident):
        return "`%s`" % ident

    def test_TIME(self):
        from datetime import timedelta
        def generator(row,col):
            return timedelta(0, row*8000)
        self.check_data_integrity(
                 ('col1 TIME',),
                 generator)

    def test_TINYINT(self):
        # Number data
        def generator(row,col):
            v = (row*row) % 256
            if v > 127:
                v = v-256
            return v
        self.check_data_integrity(
            ('col1 TINYINT',),
            generator)

    def test_SET(self):
        things = 'ash birch cedar larch pine'.split()
        def generator(row, col):
            from sets import Set
            s = Set()
            for i in range(len(things)):
                if (row >> i) & 1:
                    s.add(things[i])
            return s
        self.check_data_integrity(
            ('col1 SET(%s)' % ','.join(["'%s'" % t for t in things]),),
            generator)
        
    def test_stored_procedures(self):
        db = self.connection
        c = self.cursor
        self.create_table(('pos INT', 'tree CHAR(20)'))
        c.executemany("INSERT INTO %s (pos,tree) VALUES (%%s,%%s)" % self.table,
                      list(enumerate('ash birch cedar larch pine'.split())))
        db.commit()
        
        c.execute("""
        CREATE PROCEDURE test_sp(IN t VARCHAR(255))
        BEGIN
            SELECT pos FROM %s WHERE tree = t;
        END
        """ % self.table)
        db.commit()

        c.callproc('test_sp', ('larch',))
        rows = c.fetchall()
        self.assertEquals(len(rows), 1)
        self.assertEquals(rows[0][0], 3)
        c.nextset()
        
        c.execute("DROP PROCEDURE test_sp")
        c.execute('drop table %s' % (self.table))

        
if __name__ == '__main__':
    if test_MySQLdb.leak_test:
        import gc
        gc.enable()
        gc.set_debug(gc.DEBUG_LEAK)
    unittest.main()
    print '''"Huh-huh, he said 'unit'." -- Butthead'''
