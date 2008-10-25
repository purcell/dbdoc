#!/usr/bin/env python
# -*- encoding: iso-8859-15 -*-
# Use of this software is subject to the terms specified in the LICENCE
# file included in the distribution package, and also available via
# http://dbdoc.sourceforge.net/
#

#
# Provides support for reading and writing Java-style properties files
#

__author__ = 'Steve Purcell <stephen_purcell at yahoo dot com>'
__version__ = "$Revision: 1.2 $"[11:-2] 

import UserDict, re, string, os

class Properties(UserDict.UserDict):
    """All-purpose wrapper for properties files. Handles most sanely-
    formatted property entries. Does not support special characters in
    property names, but does support them in values.
    """

    PROPERTY_RE = re.compile(r'^\s*([\w\.\-]+)\s*=\s*(\"?)(.*)\2$')
    ATTR_KEYS = () # keys that will look like instance attributes
    # translations for \-escaped characters
    _LOAD_TRANSLATIONS = {'=':'=', ':':':', ' ':' ', 't':'\t',
                          'r':'\r', 'n':'\n', 'f':'\f', '#':'#',
                          '!':'!', '\\':'\\'}
    _SAVE_TRANSLATIONS = {}
    for k, v in _LOAD_TRANSLATIONS.items():
        _SAVE_TRANSLATIONS[v] = k
    known_keys = {} # forward def to stop setattr and getattr complaining

    def __init__(self):
        self.data = {}
        self.known_keys = {}
        for key in self.ATTR_KEYS: self.known_keys[key] = 1

    def save(self, stream):
        items = self.items()
        items.sort()
        for key, value in items:
            stream.write("%s=%s%s" % (key, self.escape_value(value), os.linesep))

    def __getattr__(self, attr):
        if self.known_keys.has_key(attr):
            try:
                return self[attr]
            except KeyError:
                pass
        raise AttributeError, attr
        
    def __setattr__(self, attr, value):
        if self.known_keys.has_key(attr):
            self[attr] = value
        else:
            self.__dict__[attr] = value

    def unescape_value(self, value):
        chars = []
        i = 0
        while i < len(value):
            c = value[i]
            if c == '\\':
                i = i + 1
                c = value[i]
                replacement = self._LOAD_TRANSLATIONS.get(c, None)
                if replacement:
                    chars.append(replacement)
                    i = i + 1
                elif c == 'u':
                    code = value[i+1:i+5]
                    if len(code) != 4:
                        raise ValueError, "illegal unicode escape sequence"
                    chars.append(chr(string.atoi(code, 16)))
                    i = i + 5
                else:
                    raise ValueError, "unknown escape \\%s" % c
            else:
                chars.append(c)
                i = i + 1
        return string.join(chars, '')

    def escape_value(self, value):
        chars = []
        for c in value:
            replacement = self._SAVE_TRANSLATIONS.get(c, None)
            if replacement:
                chars.append("\\%s" % replacement)
            elif ord(c) < 0x20 or ord(c) > 0x7e:
                chars.append("\\u%04X" % ord(c))
            else:
                chars.append(c)
        return string.join(chars, '')

    def load(self, stream):
        while 1:
            line = stream.readline()
            if not line: break
            m = self.PROPERTY_RE.match(line)
            if m:
                name, quote, value = m.groups()
                self[name] = self.unescape_value(value)



##############################################################################
# A sprinkling of test code that runs when the module is imported or executed
##############################################################################

def test():
    def checkmatch(regex, s, groups):
        match = regex.match(s)
        assert match, "failed on %s" % s
        assert (match.groups() == groups), str(match.groups())

    regex = Properties.PROPERTY_RE
    checkmatch(regex, 'blah=foo\n', ('blah','','foo'))
    checkmatch(regex, '  blah = "foo"\n', ('blah','"','foo'))
    checkmatch(regex, ' blah = "foo "\n', ('blah','"','foo '))
    checkmatch(regex, ' blah = "foo "\n', ('blah','"','foo '))
    ## Trailing comments are not legal
    #checkmatch(regex, ' blah = "foo" # blah\n', ('blah','"','foo'))
    #checkmatch(regex, ' blah = "fo\\"o" # blah\n', ('blah','"','fo\\"o'))
    #checkmatch(regex, ' blah = fo\\"o # blah\n', ('blah','','fo\\"o'))

    p = Properties()
    from StringIO import StringIO
    unquoted = '!"§$%&/()=?ßµ'
    quoted = '\!"\u00A7$%&/()\=?\u00DF\u00B5'
    i = StringIO('key=%s\n' % quoted)
    p.load(i)
    assert p['key'] == unquoted
    o = StringIO()
    p.save(o)
    assert o.getvalue() == 'key=%s\n' % quoted



if __name__ == '__main__':
    test()
