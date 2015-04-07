#!/usr/bin/env python
#
# Use of this software is subject to the terms specified in the LICENCE
# file included in the distribution package, and also available via
# https://github.com/purcell/dbdoc
#

# Oracle 8i implementation of the database schema API
#
# designed for DB API 2.0 compliant DB interfaces, such as
# - cx_Oracle
# - DcOracle

__author__ = 'Andy Todd <andy47@halfcooked.com>'
__version__ = '$Version: $'[11:-2]

import string

class OracleSchema:
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
        return _OracleTable(name, cols, pkey, fkeys, defaults, indexes)

class _OracleTable:
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
        return _OracleColumn(name, self.name, colinfo,
                               self._fkeys.get(name, None),
                               self._defaults.get(name))

    def get_indexes(self):
        return map(self.get_index, self._indexes.keys())

    def get_index(self, name):
        index_info = self._indexes.get(name, None)
        if not index_info: return None
        colnames, unique = index_info
        return _OracleIndex(name, self.name, colnames, unique)

class _OracleColumn:
    def __init__(self, name, table_name, colinfo, references, default):
        self.name = name
        self.table_name = table_name
        self.type, self.nullable, has_default, self.length = colinfo
        self.references = references
        self.default_value = default

class _OracleIndex:
    def __init__(self, name, table_name, col_names, unique):
        self.name = name
        self.table_name = table_name
        self._col_names = col_names
        self.unique = unique

    def get_column_names(self):
        return self._col_names

def _get_column_info(conn):
    "Get a dictionary of (table, [list of column details]) tuples for all tables"
    # AJT 13.11.2001 - Note date is hard coded to '11'. Probably should special
    # case this in the documentation class to ignore the length of dates.
    stmt = """SELECT table_name, column_name, data_type, nullable,
                     decode(default_length, NULL, 0, 1) hasdef,
                     decode(data_type, 'DATE', '11',
                                       'NUMBER', nvl(data_precision,38)||'.'||data_scale,
                                       data_length) data_length
              FROM   user_tab_columns"""
    tables = {}
    for table, attr, typ, nullable, hasdef, length in _query(conn, stmt):
        t = tables.get(table, None)
        if not t:
            t = []
            tables[table] = t
        # If nullable is not one of 'Y' or 'N' raise AssertionError
        assert nullable in ('Y', 'N'), nullable
        nullable = (nullable == 'Y')
        t.append((attr, typ, nullable, hasdef, length))
    return tables

def _get_foreign_keys(conn):
    """Get a dictionary of {table: {column name:
                                   (referenced table, referenced key)}}
    """
    # AJT 14.11.2001 - Changed order of tables in from clause to speed up query
    fkeys = {}
    stmt = """SELECT uc.table_name
                    ,ucc.column_name
                    ,fc.table_name
                    ,fc.constraint_name
              FROM   user_cons_columns ucc
                    ,user_constraints fc
                    ,user_constraints uc
              WHERE  uc.constraint_type = 'R'
              AND    uc.constraint_name = ucc.constraint_name
              AND    fc.constraint_name = uc.r_constraint_name"""

    for owner_table, column, referenced_table, referenced_table_pkey in _query(conn, stmt):
        t = fkeys.get(owner_table, None)
        if not t:
            t = {}
            fkeys[owner_table] = t
        t[column] = (referenced_table, referenced_table_pkey)
    return fkeys

def _get_column_defaults(conn):
    "Get a dictionary of {table: {column name: default value}}"
    # AJT 08.11.2001
    # It might be necessary to remove the where clause here.
    stmt = """SELECT table_name, column_name, data_default
              FROM   user_tab_columns
              WHERE  default_length IS NOT NULL"""
    defaults = {}
    for table, attr, default in _query(conn, stmt):
        t = defaults.get(table, None)
        if not t: defaults[table] = t = {}
        t[attr] = default
    return defaults

def _get_indexes(conn):
    # AJT 08.11.2001
    stmt = """SELECT ui.table_name, ui.index_name, ui.uniqueness
              FROM   user_indexes ui
              ORDER BY ui.table_name"""
    indices = {}
    for table, index_name, unique in _query(conn, stmt):
        t = indices.get(table, None)
        if not t:
            indices[table] = t = {}
        stmt = """SELECT column_name
                  FROM   user_ind_columns
                  WHERE  index_name = '%s'""" % index_name
        columns = []
        # AJT - Could replace this with a list comprehension
        for columnName in _query(conn, stmt):
            columns.append(columnName[0])
        t[index_name] = (columns, unique == 'UNIQUE')
    return indices

def _get_primary_keys(conn):
    # AJT 08.11.2001
    pkeys = {}
    stmt = """SELECT uc.table_name, ucc.column_name
              FROM   user_constraints uc
                    ,user_cons_columns ucc
              WHERE  uc.constraint_name = ucc.constraint_name
              AND    uc.constraint_type = 'P'
              ORDER BY uc.table_name, ucc.position"""
    for table, column in _query(conn, stmt):
        pkey = pkeys.get(table, None)
        if not pkey:
            pkeys[table] = column
        else:
            pkeys[table] = pkey + ', ' + column
    return pkeys

def _query(conn, querystr):
    cur = conn.cursor()
    cur.execute(querystr)
    results = cur.fetchall()
    cur.close()
    return results


if __name__ == '__main__':
    import cx_Oracle
    connection = cx_Oracle.connect('andy/andy@angua')

    #import DCOracle2
    #connection = < Something >

    s = OracleSchema(connection, 'Oracle')
