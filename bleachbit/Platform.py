# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Platform detection constants.

Leaf module: imports nothing from bleachbit so it stays free of cycles.
"""

import os
import re
import sys

# platform
IS_WINDOWS = os.name == 'nt'
IS_POSIX = os.name == 'posix'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'
IS_BSD = sys.platform.startswith(('freebsd', 'openbsd', 'netbsd'))
IS_FREEBSD = sys.platform.startswith('freebsd')
IS_NETBSD = sys.platform[:6] == 'netbsd'
ARCH_BITS = 64 if sys.maxsize > 2**32 else 32

# file system attributes
FS_CASE_SENSITIVE = not (IS_WINDOWS or IS_MAC)
FS_SCAN_RE_FLAGS = 0 if FS_CASE_SENSITIVE else re.IGNORECASE
