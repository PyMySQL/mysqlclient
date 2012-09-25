This is the legacy (1.x) version of MySQLdb. While it is still being
maintained, there will not be a lot of new feature development. 

TODO
====

* A bugfix 1.2.4 release
* A 1.3.0 release that will support Python 2.7-3.3

The 2.0 version is being renamed moist and lives at
https://github.com/farcepest/moist

Repository list
===============

MySQLdb-svn
	This is the old Subversion repository located on SourceForge at
	https://svn.code.sf.net/p/mysql-python/svn
	(https://sourceforge.net/p/mysql-python/svn/)
	It has all the early historical development of MySQLdb through 1.2.3,
	and also is the working repository for ZMySQLDA. The trunk on this
	repository was forked to create the MySQLdb2 repository.
MySQLdb1
	This is the new (active) git repository, located on:

	* SourceForge: git://git.code.sf.net/p/mysql-python/code 
	  (https://sourceforge.net/p/mysql-python/code)
	* GitHub: git://github.com/farcepest/MySQLdb1.git
	  (https://github.com/farcepest/MySQLdb1)

	I intend to keep these two in sync.
	Only updates to the 1.x series will happen here.
MySQLdb2
	This is the now obsolete Mercurial repository for MySQLdb-2.0
	located on SourceForge at
	http://hg.code.sf.net/p/mysql-python/mysqldb-2
	(https://sourceforge.net/p/mysql-python/mysqldb-2/)
	SourceForge currently shows this as an "Empty Repository", but
	it is looking for a default branch that doesn't exist. The only
	working branch is MySQLdb. This repository is migrating to the
        moist repository.
moist
	This is a git repository located on github at
	https://github.com/farcepest/moist  It's actually empty as of
	this writing, but it will soon contain the contents of the
	MySQLdb2 repository.

