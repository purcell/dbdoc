#!/usr/bin/env python
#
# Use of this software is subject to the terms specified in the LICENCE
# file included in the distribution package, and also available via
# http://dbdoc.sourceforge.net/
#

#
# Generates HTML information from a Postgres schema and a properties file
#

__author__ = 'Steve Purcell <stephen_purcell at yahoo dot com>'
__version__ = '$Revision: 1.4 $'[11:-2]

import dbdoc.dbdoc
import dbdoc.pgschema
import getopt, sys, os

def usage_exit(progname, msg=None):
    if msg:
        print msg
        print
    print "usage: %s [-d dbmodule] [-p propsfile] connstring outdir [table_name ...]" % progname
    sys.exit(2)

def main(argv):
    progname = os.path.basename(argv[0])
    dblib = "pgdb"
    props_file = None
    table_names = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:p:', ['help', 'dblib=', 'props='])
        for opt, value in opts:
            if opt in ('-h','--help'):
                usage_exit(progname)
            if opt in ('-d','--dblib'):
                dblib = value
            if opt in ('-p','--props'):
                props_file = value
    except getopt.error, e:
        usage_exit(progname, e)
    if len(args) < 2:
        usage_exit(progname)

    conn_string, outdir = args[:2]
    if len(args) > 2:
        table_names = args[2:]

    try:
        connector = __import__(dblib)
    except ImportError, e:
        print "couldn't find pg access module '%s': %s" % (dblib, e)
        sys.exit(1)

    conn = connector.connect(conn_string)
    schema = dbdoc.pgschema.PostgresSchema(conn, 'postgres')
    dbdoc.dbdoc.main(schema, outdir, props_file, table_names)


if __name__ == '__main__':
    main(sys.argv)
