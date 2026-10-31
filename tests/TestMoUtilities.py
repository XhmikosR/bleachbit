# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test case for module MoUtilities
"""

import gettext
import os
import struct

from windows.MoUtilities import (MO_MAGIC, read_mo, shrink_mo, unused_msgids,
                                 write_mo)
from tests import common

HEADER = (b'Project-Id-Version: bleachbit\n'
          b'Last-Translator: Someone <someone@example.com>\n'
          b'Language: pt_BR\n'
          b'Content-Type: text/plain; charset=UTF-8\n'
          b'Plural-Forms: nplurals=2; plural=n > 1;\n'
          b'X-Generator: Weblate\n')

ENTRIES = [
    (b'', HEADER),
    (b'Cookies', b'Cookies'),
    (b'Delete the cache', 'Excluir o cache'.encode()),
    (b'nsis:INSTALLER_CAPTION\x04${prodname} Setup',
     'Instalação'.encode()),
    (b'menu\x04Preferences', 'Preferências'.encode()),
    (b'%d file\0%d files', b'%d arquivo\0%d arquivos'),
    (b'File\0Files', b'File\0Files'),
]


class MoUtilitiesTestCase(common.BleachbitTestCase):
    """Test case for module MoUtilities"""

    def _write_mo(self):
        path = os.path.join(self.mkdtemp(), 'bleachbit.mo')
        write_mo(path, ENTRIES)
        return path

    def _load(self, path):
        with open(path, 'rb') as f:
            return gettext.GNUTranslations(f)

    def test_write_mo_round_trip(self):
        """read_mo returns what write_mo wrote, sorted"""
        path = self._write_mo()
        self.assertEqual(read_mo(path), sorted(ENTRIES))
        t = self._load(path)
        self.assertEqual(t.gettext('Delete the cache'), 'Excluir o cache')
        self.assertEqual(t.pgettext('menu', 'Preferences'),
                         'Preferências')

    def test_shrink_mo(self):
        """shrink_mo drops unused entries and keeps the lookups"""
        path = self._write_mo()
        drop = {b'nsis:INSTALLER_CAPTION\x04${prodname} Setup'}
        self.assertTrue(shrink_mo(path, drop))
        msgids = [msgid for msgid, _msgstr in read_mo(path)]
        self.assertNotIn(b'Cookies', msgids)
        self.assertIn(b'File\0Files', msgids)
        self.assertEqual(len(msgids), len(ENTRIES) - 2)
        t = self._load(path)
        self.assertEqual(t.info(), {'content-type': 'text/plain; charset=UTF-8',
                                    'plural-forms': 'nplurals=2; plural=n > 1;'})
        self.assertEqual(t.charset(), 'UTF-8')
        self.assertEqual(t.gettext('Cookies'), 'Cookies')
        self.assertEqual(t.gettext('Delete the cache'), 'Excluir o cache')
        self.assertEqual(t.pgettext('menu', 'Preferences'),
                         'Preferências')
        self.assertEqual(t.pgettext('nsis:INSTALLER_CAPTION', '${prodname} Setup'),
                         '${prodname} Setup')
        # The pt_BR plural rule survives: 0 is singular
        self.assertEqual(t.ngettext('%d file', '%d files', 0), '%d arquivo')
        self.assertEqual(t.ngettext('%d file', '%d files', 2), '%d arquivos')

    def test_shrink_mo_keep_identical(self):
        """keep_identical keeps the entries translated to themselves"""
        path = self._write_mo()
        self.assertTrue(shrink_mo(path, keep_identical=True))
        self.assertIn((b'Cookies', b'Cookies'), read_mo(path))

    def test_shrink_mo_big_endian(self):
        """shrink_mo reads a big-endian .mo"""
        path = os.path.join(self.mkdtemp(), 'be.mo')
        msgid, msgstr = b'Cache', b'Cache!'
        with open(path, 'wb') as f:
            f.write(struct.pack('>7I', MO_MAGIC, 0, 1, 28, 36, 0, 44))
            f.write(struct.pack('>4I', len(msgid), 44,
                                len(msgstr), 45 + len(msgid)))
            f.write(msgid + b'\0' + msgstr + b'\0')
        self.assertTrue(shrink_mo(path))
        self.assertEqual(self._load(path).gettext('Cache'), 'Cache!')

    def test_shrink_mo_revision(self):
        """shrink_mo leaves alone a revision it cannot write"""
        path = self._write_mo()
        with open(path, 'r+b') as f:
            f.seek(4)
            f.write(struct.pack('<I', 1))
        with open(path, 'rb') as f:
            before = f.read()
        self.assertFalse(shrink_mo(path))
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), before)

    def test_shrink_mo_not_mo(self):
        """read_mo rejects a file that is not a .mo"""
        path = os.path.join(self.mkdtemp(), 'bad.mo')
        with open(path, 'wb') as f:
            f.write(b'\0' * 28)
        with self.assertRaises(ValueError):
            read_mo(path)

    def test_unused_msgids(self):
        """unused_msgids keeps any msgid that a used source shares"""
        pot = os.path.join(self.mkdtemp(), 'test.pot')
        with open(pot, 'w', encoding='utf-8') as f:
            f.write('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=utf-8\\n"\n\n'
                    '#: windows/NsisInclude/NsisMultiUserLang.nsh\n'
                    'msgctxt "nsis:RUNNING"\nmsgid ""\n"${prodname} is "\n"running.\\n"\nmsgstr ""\n\n'
                    '#: ../org.bleachbit.BleachBit.desktop\n'
                    '#: ../org.bleachbit.BleachBit.metainfo.xml\n'
                    'msgid "Free space"\nmsgstr ""\n\n'
                    '#: ../org.bleachbit.BleachBit.desktop ../bleachbit/GuiWindow.py:12\n'
                    'msgid "Shared"\nmsgstr ""\n\n'
                    'msgid "No reference"\nmsgstr ""\n\n'
                    '#: ../org.bleachbit.BleachBit.metainfo.xml\n'
                    'msgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] ""\nmsgstr[1] ""\n')
        sources = ('NsisMultiUserLang.nsh', 'org.bleachbit.BleachBit.desktop',
                   'org.bleachbit.BleachBit.metainfo.xml')
        self.assertEqual(unused_msgids(pot, sources),
                         {b'nsis:RUNNING\x04${prodname} is running.\n',
                          b'Free space', b'%d file'})

    def test_unused_msgids_bleachbit_pot(self):
        """Every NSIS entry in bleachbit.pot is unused, and no code entry is"""
        pot = os.path.join('po', 'bleachbit.pot')
        unused = unused_msgids(pot, ('NsisMultiUserLang.nsh',))
        with open(pot, encoding='utf-8') as f:
            nsis_count = f.read().count('\nmsgctxt "nsis:')
        self.assertGreater(nsis_count, 0)
        self.assertEqual(len(unused), nsis_count)
        self.assertTrue(all(msgid.startswith(b'nsis:') for msgid in unused))
