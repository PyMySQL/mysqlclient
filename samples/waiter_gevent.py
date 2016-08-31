from __future__ import print_function
"""Demo using Gevent with mysqlclient."""

import gevent.hub
import MySQLdb


def gevent_waiter(fd, hub=gevent.hub.get_hub()):
    hub.wait(hub.loop.io(fd, 1))


def f(n):
    conn = MySQLdb.connect(user='root', waiter=gevent_waiter)
    cur = conn.cursor()
    cur.execute("SELECT SLEEP(%s)", (n,))
    cur.execute("SELECT 1+%s", (n,))
    print(cur.fetchall()[0])


gevent.spawn(f, 1)
gevent.spawn(f, 2)
gevent.spawn(f, 3)
gevent.spawn(f, 4)
gevent.sleep(5)
