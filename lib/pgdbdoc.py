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
__version__ = '$Revision: 1.1.1.1 $'[11:-2]

import dbdoc.dbdoc
import dbdoc.pgschema
import getopt, sys, os

def usage_exit(progname, msg=None):
    if msg:
        print msg
        print
    print "usage: %s connstring outdir [propsfile]" % progname
    sys.exit(2)

def main(argv):
    progname = os.path.basename(argv[0])
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
        for opt, value in opts:
            if opt in ('-h', '--help'): usage_exit(progname)
    except getopt.error, e:
        usage_exit(progname, e)
    if len(args) == 3:
        conn_string, outdir, props_file = args
    elif len(args) == 2:
        conn_string, outdir = args
        props_file = None
    else:
        usage_exit(progname)

    for lib in ('psycopg', 'PoPy', 'pgdb'):
        try:
            connector = __import__(lib)
            break
        except ImportError:
            continue
    if not connector:
        print "couldn't find a pg access module"
        sys.exit(1)
    conn = connector.connect(conn_string)
    schema = dbdoc.pgschema.PostgresSchema(conn, 'postgres')
    dbdoc.dbdoc.main(schema, outdir, props_file)

if __name__ == '__main__':
    main(sys.argv)

    #import pgdb
    #conn = pgdb.connect(':postgres:postgres')

    #import psycopg
    #dsn = 'dbname=postgres user=postgres'
    #conn = psycopg.connect(dsn)

    #import PoPy
    #dsn = 'dbname=postgres user=postgres'
    #conn = PoPy.connect(dsn)
