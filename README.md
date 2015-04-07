# DBDoc: Generate Database Schema Documentation

This code generates javadoc-style documentation for a database schema,
and allows optional annotation of tables and columns using an outboard
properties text file.

Support is currently provided for Oracle and PostgreSQL databases.

Example output is [available to browse](http://dbdoc.sourceforge.net/examples/disc_rack/index.html).

## Contents of this package:

    LICENCE   - The licence under the terms of which this package is provided
    lib/      - Python library files and scripts
    examples/ - Example schemas and scripts
    doc/      - Documentation, including the TODO list

## Usage

### Oracle example (assuming cx_Oracle installed):

    % cd lib
    % ./oradbdoc.py 'user/password@db' /tmp

This generates HTML documentation in /tmp detailing the schema of the
Oracle instance 'db' running on the local machine.

### PostgreSQL example (assuming pygresql installed):

    % cd lib
    % ./pgdbdoc.py -d pgdb ':mydb:myuser:' /tmp

This generates HTML documentation in /tmp detailing the schema of the
postgresql instance 'mydb' running on the local machine.

This code was moved from
[dbdoc.sourceforge.net](http://dbdoc.sourceforge.net/), where
additional helpful information may still be available.

## Known issues

Using the DCOracle2 module can result in garbage default column values.
cx_Oracle is recommended in its place.


## Similar tools

[SchemaSpy](http://schemaspy.sourceforge.net/) is pretty nice.

## About

This code was written by Steve Purcell a very long time ago (~2001),
and revived in 2015.

Author links:

[![](http://api.coderwall.com/purcell/endorsecount.png)](http://coderwall.com/purcell)

[![](http://www.linkedin.com/img/webpromo/btn_liprofile_blue_80x15.png)](http://uk.linkedin.com/in/stevepurcell)

[sanityinc.com](http://www.sanityinc.com/)

[@sanityinc](https://twitter.com/)
