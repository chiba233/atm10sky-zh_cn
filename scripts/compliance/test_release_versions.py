#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# atm10sky-zh_cn — All the Mods 10 to the Sky 简体中文汉化补丁
# Copyright (C) 2026 星野夢華 (Hoshino Yumeka)
# SPDX-License-Identifier: GPL-3.0-or-later
"""验打包白名单（scripts/release_versions.py）取不到就会红。

白名单决定发布挂哪些包。它要是在出错时回落成「versions/ 下全部」或「一个都不打」，
发版就会悄悄多出或少掉一批包。这里在临时目录里造出各种坏白名单，确认脚本退出非 0。

用法:
    python3 scripts/compliance/test_release_versions.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

SELF = Path(__file__).resolve().parent.parent / 'release_versions.py'


def run(root):
    return subprocess.run([sys.executable, str(SELF), str(root)], capture_output=True, text=True)


def repo(versions, whitelist):
    d = Path(tempfile.mkdtemp())
    (d / 'versions').mkdir()
    for v in versions:
        (d / 'versions' / v).mkdir()
    (d / 'versions' / 'db').mkdir()
    if whitelist is not None:
        (d / 'versions' / 'whitelist.txt').write_text(whitelist, encoding='utf-8')
    return d


fails = 0


def expect(name, root, ok, out=None):
    global fails
    r = run(root)
    good = (r.returncode == 0) == ok and (out is None or r.stdout.strip() == out)
    print(('✅ ' if good else '❌ ') + name + ('' if good else '（退出码 %d，输出 %r %r）' % (r.returncode, r.stdout, r.stderr)))
    if not good:
        fails += 1


expect('正常白名单 → 按版本号升序输出', repo(['2.0.7', '2.1.0', '2.10.0', '2.2.0'], '# 注释\n2.10.0\n2.1.0\n\n2.2.0\n'), True, '2.1.0 2.2.0 2.10.0')
expect('白名单不存在 → 必须红', repo(['2.1.0'], None), False)
expect('白名单里一个版本都没有 → 必须红', repo(['2.1.0'], '# 只有注释\n'), False)
expect('列了 versions/ 下没有的版本 → 必须红', repo(['2.1.0'], '2.1.0\n9.9.9\n'), False)
expect('同一版本列了两次 → 必须红', repo(['2.1.0', '2.2.0'], '2.1.0\n2.1.0\n'), False)
expect('db 目录不算版本 → 必须红', repo(['2.1.0'], 'db\n'), False)
sys.exit(1 if fails else 0)
