#!/usr/bin/env python
#
# Use of this software is subject to the terms specified in the LICENCE
# file included in the distribution package, and also available via
# http://dbdoc.sourceforge.net/
#

# Postgres 7.x implementation of the database schema API
# May also work for older postgres versions, but foreign keys are unlikely
# to be detected correctly.
#
# designed for DB API 2.0 compliant DB interfaces, such as
# - pygresql (pgdb module)
# - psycopg
# - popy

__author__ = 'Steve Purcell <stephen_purcell at yahoo dot com>'
__version__ = '$Version: $'[11:-2]

import string

class PostgresSchema:
    schema_api_version = 1

    def __init__(self, conn, name):
        self.name = name
        self._column_info = _get_column_info(conn)
        self._foreign_keys = _get_foreign_keys(conn)
        self._column_defaults = _get_column_defaults(conn)
        self._primary_keys = _get_primary_keys(conn)
        self._indexes = _get_indexes(conn)

    def get_tables(self):
        return map(self.get_table, self._column_info.keys())

    def get_table(self, name):
        cols = self._column_info.get(name)
        if not cols: return None
        indexes = self._indexes.get(name, {})
        fkeys = self._foreign_keys.get(name, {})
        pkey = self._primary_keys.get(name, None)
        defaults = self._column_defaults.get(name, {})
        return _PostgresTable(name, cols, pkey, fkeys, defaults, indexes)

class _PostgresTable:
    def __init__(self, name, cols, pkey, fkeys, defaults, indexes):
        self.name = name
        self._coldict = {}
        for attr, typ, nullable, hasdef, length in cols:
            self._coldict[attr] = (typ, nullable, hasdef, length)
        self._colnames = map(lambda c: c[0], cols)
        self.primary_key_name = pkey
        self._fkeys = fkeys
        self._defaults = defaults
        self._indexes = indexes

    def get_columns(self):
        return map(self.get_column, self._colnames)

    def get_column(self, name):
        colinfo = self._coldict.get(name, None)
        if not colinfo: return None
        return _PostgresColumn(name, self.name, colinfo,
                               self._fkeys.get(name, None),
                               self._defaults.get(name))

    def get_indexes(self):
        return map(self.get_index, self._indexes.keys())

    def get_index(self, name):
        index_info = self._indexes.get(name, None)
        if not index_info: return None
        colnames, unique = index_info
        return _PostgresIndex(name, self.name, colnames, unique)


class _PostgresColumn:
    def __init__(self, name, table_name, colinfo, references, default):
        self.name = name
        self.table_name = table_name
        self.type, self.nullable, has_default, self.length = colinfo
        self.references = references
        self.default_value = default

class _PostgresIndex:
    def __init__(self, name, table_name, col_names, unique):
        self.name = name
        self.table_name = table_name
        self._col_names = col_names
        self.unique = unique

    def get_column_names(self):
        return self._col_names


def _get_column_info(conn):
    Q = """SELECT c.relname, a.attname, t.typname, a.attlen, a.attnotnull,
           a.atthasdef, a.atttypmod
           FROM pg_class c, pg_attribute a, pg_type t
           WHERE
           c.relname !~ '^pg_' and
           c.relname !~ '^Inv' and
           c.relkind = 'r' and
           a.attnum > 0 and
           a.attrelid = c.oid and
           a.atttypid = t.oid"""
    tables = {}
    for table, attr, typ, length, notnull, hasdef, typmod in _query(conn, Q):
        t = tables.get(table, None)
        if not t:
            t = []
            tables[table] = t
        assert notnull in ('t', 'f', 1, 0), notnull
        nullable = (notnull not in ('t', 1))
        hasdef = (hasdef == 't')
        if length == -1:
            length = typmod
        t.append((attr, typ, nullable, hasdef, length))
    return tables

def _get_foreign_keys(conn):
    """Find foreign keys by looking at triggers. (Query adapted from
       query posted to pgsql-general by Michael Fork according to
       http://www.geocrawler.com/mail/msg.php3?msg_id=4895586&list=12)
    """
    fkeys = {}
    for (tgargs,) in _query(conn, '''
  SELECT pt.tgargs FROM pg_class pc,
        pg_proc pg_proc, pg_proc pg_proc_1, pg_trigger pg_trigger,
        pg_trigger pg_trigger_1, pg_proc pp, pg_trigger pt
  WHERE  pt.tgrelid = pc.oid AND pp.oid = pt.tgfoid
        AND pg_trigger.tgconstrrelid = pc.oid
        AND pg_proc.oid = pg_trigger.tgfoid
        AND pg_trigger_1.tgfoid = pg_proc_1.oid
        AND pg_trigger_1.tgconstrrelid = pc.oid
        AND ((pp.proname LIKE '%ins')
        AND (pg_proc.proname LIKE '%upd')
        AND (pg_proc_1.proname LIKE '%del')
        AND (pg_trigger.tgrelid=pt.tgconstrrelid)
        AND (pg_trigger_1.tgrelid = pt.tgconstrrelid))'''):
        # Varies between psycopg and other DB APIs.
        if string.find(tgargs, '\000') != -1:
            tgargs = string.split(tgargs, '\000')
        else:
            tgargs = string.split(tgargs, '\\000')
        if len(tgargs) != 7:
            raise RuntimeError, "error parsing trigger args for foreign key: %s" \
                  % repr(tgargs)
        (name, owner_table, referenced_table,
         unknown, column, referenced_table_pkey, blank) = tgargs
        t = fkeys.get(owner_table, None)
        if not t:
            t = {}
            fkeys[owner_table] = t
        t[column] = (referenced_table, referenced_table_pkey)
    return fkeys


def _get_column_defaults(conn):
    results = _query(conn, """select pg_class.relname, pg_attribute.attname,
                              pg_attrdef.adsrc from pg_attrdef,
                              pg_class, pg_attribute where
                              pg_attribute.attrelid = pg_class.oid and
                              pg_attrdef.adnum = pg_attribute.attnum and
                              pg_attrdef.adrelid = pg_class.oid""")
    defaults = {}
    for table, attr, default in results:
        t = defaults.get(table, None)
        if not t: defaults[table] = t = {}
        t[attr] = default
    return defaults

def _get_indexes(conn):
    results = _query(conn, """select t.relname, i.relname, pg_index.indkey, pg_index.indisunique from
              pg_class i, pg_class t, pg_index where
              i.oid = pg_index.indexrelid and
              t.oid = pg_index.indrelid""")
    indices = {}
    for table, index_name, cols, unique in results:
        # this looped query is another opportunity for optimisation
        def first(row): return row[0]
        cols = string.replace(cols, ' ', ',')
        colnames = map(first, _query(conn,
            """select a.attname from pg_attribute a, pg_class where
               a.attrelid = pg_class.oid and
               pg_class.relname = '%s' and
               a.attnum in (%s)""" % (table, cols)))
        t = indices.get(table, None)
        if not t:
            indices[table] = t = {}
        t[index_name] = (colnames, unique == 't')
    return indices

def _get_primary_keys(conn):
    pkeys = {}
    results = _query(conn, """select
              pg_class.relname, pg_attribute.attname from pg_class,
              pg_attribute, pg_index where
              pg_class.oid = pg_attribute.attrelid and
              pg_class.oid = pg_index.indrelid and
              pg_index.indkey[0] = pg_attribute.attnum and
              pg_index.indisprimary = 't'""")
    for table, attr in results:
        pkeys[table] = attr
    return pkeys

def _query(conn, querystr):
    cur = conn.cursor()
    cur.execute(querystr)
    results = cur.fetchall()
    cur.close()
    return results


if __name__ == '__main__':
    import pgdb
    conn = pgdb.connect(':postgres:postgres')

    #import psycopg
    #dsn = 'dbname=postgres user=postgres'
    #conn = psycopg.connect(dsn)

    #import PoPy
    #dsn = 'dbname=postgres user=postgres'
    #conn = PoPy.connect(dsn)

    # Works with 'em all!
    s = PostgresSchema(conn, 'postgres')
