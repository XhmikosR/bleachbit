# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""Shrink the gettext .mo files that the Windows build ships"""

import ast
import os
import re
import struct

MO_MAGIC = 0x950412de
# The only header fields Python's gettext and libintl read
_HEADER_FIELDS = (b'content-type', b'plural-forms')


def read_mo(path):
    """Return the (msgid, msgstr) byte pairs of a .mo file

    Return None for a revision this module cannot write back, such as
    one with system-dependent strings.
    """
    with open(path, 'rb') as f:
        data = f.read()
    for order in '<>':
        magic, revision, count, ids_offset, strs_offset = struct.unpack_from(
            order + '5I', data)
        if magic == MO_MAGIC:
            break
    else:
        raise ValueError(f'Not a .mo file: {path}')
    if revision != 0:
        return None
    entries = []
    for i in range(count):
        id_len, id_pos = struct.unpack_from(
            order + '2I', data, ids_offset + 8 * i)
        str_len, str_pos = struct.unpack_from(
            order + '2I', data, strs_offset + 8 * i)
        entries.append((data[id_pos:id_pos + id_len],
                        data[str_pos:str_pos + str_len]))
    return entries


def write_mo(path, entries):
    """Write a .mo file without the optional hash table"""
    entries = sorted(entries)
    count = len(entries)
    ids_start = 28 + 16 * count
    ids = b''.join(msgid + b'\0' for msgid, _msgstr in entries)
    id_table = []
    str_table = []
    id_pos = ids_start
    str_pos = ids_start + len(ids)
    for msgid, msgstr in entries:
        id_table += (len(msgid), id_pos)
        str_table += (len(msgstr), str_pos)
        id_pos += len(msgid) + 1
        str_pos += len(msgstr) + 1
    with open(path, 'wb') as f:
        f.write(struct.pack('<7I', MO_MAGIC, 0, count,
                            28, 28 + 8 * count, 0, ids_start))
        f.write(struct.pack(f'<{4 * count}I', *id_table, *str_table))
        f.write(ids)
        f.write(b''.join(msgstr + b'\0' for _msgid, msgstr in entries))


def _trim_header(msgstr):
    lines = [line for line in msgstr.split(b'\n')
             if line.split(b':', 1)[0].strip().lower() in _HEADER_FIELDS]
    return b'\n'.join(lines) + b'\n'


def shrink_mo(path, drop_msgids=frozenset(), keep_identical=False):
    """Rewrite a .mo file without the entries the program never needs

    Drops the msgids in drop_msgids, the header fields nobody reads, the
    hash table, and unless keep_identical, the singular entries translated
    to themselves, where the lookup falls back to the same msgid.

    Return False and leave the file alone if read_mo() cannot handle it.
    """
    entries = read_mo(path)
    if entries is None:
        return False
    kept = []
    for msgid, msgstr in entries:
        if msgid == b'':
            msgstr = _trim_header(msgstr)
        elif msgid.split(b'\0', 1)[0] in drop_msgids:
            continue
        elif not keep_identical and msgid == msgstr and b'\0' not in msgid:
            continue
        kept.append((msgid, msgstr))
    write_mo(path, kept)
    return True


def unused_msgids(pot_path, unused_sources):
    """Return the msgids that only the files named in unused_sources use

    The msgids are encoded as in a .mo file, with any msgctxt in front.
    """
    unused = set()
    refs = []
    ctx = msgid = None
    field = None

    def end_entry():
        if msgid and refs and all(
                os.path.basename(re.sub(r':\d+$', '', ref)) in unused_sources
                for ref in refs):
            key = f'{ctx}\x04{msgid}' if ctx is not None else msgid
            unused.add(key.encode('utf-8'))

    with open(pot_path, encoding='utf-8') as f:
        # The extra blank line ends the last entry
        for line in [*f, '\n']:
            line = line.strip()
            if not line:
                end_entry()
                refs = []
                ctx = msgid = field = None
            elif line.startswith('#:'):
                refs += line[2:].split()
            elif line.startswith('#'):
                continue
            elif line.startswith('"'):
                if field == 'msgctxt':
                    ctx += ast.literal_eval(line)
                elif field == 'msgid':
                    msgid += ast.literal_eval(line)
            else:
                field, _, value = line.partition(' ')
                if field == 'msgctxt':
                    ctx = ast.literal_eval(value)
                elif field == 'msgid':
                    msgid = ast.literal_eval(value)
    return unused
