"""MySQL Connection Errors

Nearly all of these raise OperationalError. COMMANDS_OUT_OF_SYNC
raises ProgrammingError.

"""

if __name__ == "__main__":
    """
    Usage: python CR.py [/path/to/mysql/errmsg.h ...] >> CR.py
    """
    import fileinput, re
    data = {}
    error_last = None
    for line in fileinput.input():
        line = re.sub(r'/\*.*?\*/', '', line)
        m = re.match(r'^\s*#define\s+CR_([A-Z0-9_]+)\s+(\d+)(\s.*|$)', line)
        if m:
            name = m.group(1)
            value = int(m.group(2))
            if name == 'ERROR_LAST':
                if error_last is None or error_last < value:
                    error_last = value
                continue
            if value not in data:
                data[value] = set()
            data[value].add(name)
    for value, names in sorted(data.items()):
        for name in sorted(names):
            print('%s = %s' % (name, value))
    if error_last is not None:
        print('ERROR_LAST = %s' % error_last)


MIN_ERROR = 2000
MAX_ERROR = 2999
UNKNOWN_ERROR = 2000
SOCKET_CREATE_ERROR = 2001
CONNECTION_ERROR = 2002
CONN_HOST_ERROR = 2003
IPSOCK_ERROR = 2004
UNKNOWN_HOST = 2005
SERVER_GONE_ERROR = 2006
VERSION_ERROR = 2007
OUT_OF_MEMORY = 2008
WRONG_HOST_INFO = 2009
LOCALHOST_CONNECTION = 2010
TCP_CONNECTION = 2011
SERVER_HANDSHAKE_ERR = 2012
SERVER_LOST = 2013
COMMANDS_OUT_OF_SYNC = 2014
NAMEDPIPE_CONNECTION = 2015
NAMEDPIPEWAIT_ERROR = 2016
NAMEDPIPEOPEN_ERROR = 2017
NAMEDPIPESETSTATE_ERROR = 2018
CANT_READ_CHARSET = 2019
NET_PACKET_TOO_LARGE = 2020
