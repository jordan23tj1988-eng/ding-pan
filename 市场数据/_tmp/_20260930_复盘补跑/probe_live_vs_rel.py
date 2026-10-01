# -*- coding: utf-8 -*-
"""对比 现站(复盘/盯盘台) 与 20260929 release site 的 7 页: 字节一致性 / PAPERTRADE / 累计%。只读。"""
import hashlib, re
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
REL = BASE / 'releases/20260929-1-282d0a64da0148f9b0f5ae89cfd390da/site'
LIVE = BASE / '复盘/盯盘台'
pages = ['auction.html', 'lhb.html', 'theme.html', 'logic.html', 'limitup.html', 'index.html']

for name in pages:
    a = REL / name
    b = LIVE / name
    ta = a.read_text(encoding='utf-8') if a.is_file() else ''
    tb = b.read_text(encoding='utf-8') if b.is_file() else ''
    same = ta == tb
    def pt(t):
        i = t.find('PAPER TRADING')
        return (t.count('<!--PAPERTRADE-->'), '-'.join(re.findall(r'累计\s*([+-]?[0-9.]+)%', t[i:i+900])[:2]) if i >= 0 else 'NONE')
    print('%-14s same=%-5s size %6d/%6d  rel_pt=%s live_pt=%s' % (
        name, same, len(ta), len(tb), pt(ta), pt(tb)))
print('archive exists:', (LIVE / 'archive/20260929.html').is_file(),
      (LIVE / 'archive/20260929.html').stat().st_size if (LIVE / 'archive/20260929.html').is_file() else '')
print('CURRENT.json:', (BASE / 'CURRENT.json').read_text(encoding='utf-8')[:400])
