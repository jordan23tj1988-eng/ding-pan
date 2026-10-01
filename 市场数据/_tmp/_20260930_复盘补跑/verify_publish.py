# -*- coding: utf-8 -*-
"""发布后总验收: 健康文件 / CURRENT / archive / 7页 h2 骨架 / PAPERTRADE / 冻结。只读。"""
import json, re, hashlib
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
L = BASE / '_学习'
LIVE = BASE / '复盘/盯盘台'

hp = L / '复盘链健康_20260929.json'
print('--- 复盘链健康_20260929.json ---')
print(hp.read_text(encoding='utf-8')[:900] if hp.is_file() else 'MISSING')

print('\n--- CURRENT.json ---')
print((BASE / 'CURRENT.json').read_text(encoding='utf-8').strip()[:300])

print('\n--- archive ---')
for p in sorted((LIVE / 'archive').glob('2026*.html'))[-3:]:
    import time
    print(p.name, p.stat().st_size, time.strftime('%m-%d %H:%M', time.localtime(p.stat().st_mtime)))

print('\n--- 现站 7 页 h2 骨架 + PAPERTRADE ---')
for name in ['index.html', 'auction.html', 'cycle.html', 'theme.html', 'limitup.html', 'logic.html', 'lhb.html']:
    p = LIVE / name
    if not p.is_file():
        print(name, 'MISSING'); continue
    t = p.read_text(encoding='utf-8')
    h2 = re.findall(r'<h2[^>]*>\s*([一二三四五六七八九十][^<]{0,24})', t)
    print('%-14s %s | PT=%d | size=%d' % (name, ' / '.join(h2), t.count('<!--PAPERTRADE-->'), len(t)))

print('\n--- 模拟盘 状态/净值 目标日绑定 ---')
for route in ['auction', 'lhb', 'theme', 'logic', 'limitup', 'master']:
    sp = L / '_模拟盘' / route / '状态.json'
    np_ = L / '_模拟盘' / route / '净值.json'
    st = json.loads(sp.read_text(encoding='utf-8')) if sp.is_file() else {}
    navs = json.loads(np_.read_text(encoding='utf-8')) if np_.is_file() else {}
    cum = round((navs.get('20260929', {}).get('nav', float('nan')) - 1) * 100, 4) if '20260929' in navs else None
    print('%-8s 状态date=%s 累计pct=%s 净值日累计=%s bars=%s' % (
        route, st.get('date'), st.get('累计pct'), cum, st.get('bars', st.get('bar_date'))))
