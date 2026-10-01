# -*- coding: utf-8 -*-
"""把现站 6 页还原为 20260929 已验收 release site 的逐字节副本(撤销外部多余 inject 造成的 1 字节漂移),
使现站 theme.html 与 .theme_page_freeze.json 冻结哈希一致(哨兵C13)。备份 .bak_inject_20260930。
"""
import hashlib, shutil, json
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
REL = BASE / 'releases/20260929-1-282d0a64da0148f9b0f5ae89cfd390da/site'
LIVE = BASE / '复盘/盯盘台'
pages = ['auction.html', 'lhb.html', 'theme.html', 'logic.html', 'limitup.html', 'index.html']

for name in pages:
    a, b = REL / name, LIVE / name
    assert a.is_file() and b.is_file(), name
    bak = b.with_suffix(b.suffix + '.bak_inject_20260930')
    if not bak.exists():
        shutil.copy2(b, bak)
    shutil.copy2(a, b)
    ha = hashlib.sha256(a.read_bytes()).hexdigest()
    hb = hashlib.sha256(b.read_bytes()).hexdigest()
    print('%-14s restored=%-5s sha_match=%s' % (name, True, ha == hb))

freeze = json.loads((LIVE / '.theme_page_freeze.json').read_text(encoding='utf-8'))
cur = hashlib.sha256((LIVE / 'theme.html').read_bytes()).hexdigest()
print('freeze d=%s match=%s' % (freeze['d'], cur == freeze['theme_sha256']))
