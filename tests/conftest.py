# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Under plain `pytest`, tests.TestAll's temp-dir wrapper never runs, so
subprocess-spawning tests (e.g. TestCLI.py) would otherwise inherit the
real BleachBit config dir. Set a per-worker one before any test module
(and therefore bleachbit, which reads this at import time) is imported.
"""

import os
import shutil
import tempfile

if not os.environ.get('BLEACHBIT_TEST_OPTIONS_DIR'):
    _worker = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    os.environ['BLEACHBIT_TEST_OPTIONS_DIR'] = tempfile.mkdtemp(
        prefix=f'bleachbit-test-{_worker}-')


def pytest_sessionfinish(session, exitstatus):
    options_dir = os.environ.get('BLEACHBIT_TEST_OPTIONS_DIR')
    if options_dir and os.path.isdir(options_dir):
        shutil.rmtree(options_dir, ignore_errors=True)
