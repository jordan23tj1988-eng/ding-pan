# -*- coding: utf-8 -*-
"""测量 20260929 lhb body 的 h2二(今日S/A动向)大段构成 + 候选页是否含台账日块。只读。"""
import json, re
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
b = json.loads((BASE / '_学习/judgment_20260929.json').read_text(encoding='utf-8'))['bodies']['lhb']
sec = b[2014:328533]
print('secLen', len(sec))
print('details', sec.count('<details'), 'tables', sec.count('<table'),
      'SEATCARD', sec.count('<!--SEATCARD-->'), 'chain_open', sec.count('chain" open'),
      'tli', sec.count('class="tli'))
txt = re.sub(r'<[^>]+>', '', sec)
print('plainLen', len(txt))
print('text_head', txt[:400].replace('\n', ' '))
print('summary_days', re.findall(r'<summary><b>([0-9\-]+)</b>', sec)[:15])
print('h3', len(re.findall(r'<h3', sec)), 'h2_in_sec', sec.count('<h2'))

pages = sorted((BASE).glob('.review_staging/20260929-*/site/lhb.html'), key=lambda x: x.stat().st_mtime)
p = pages[-1]
s = p.read_text(encoding='utf-8')
print('--- page', p.parent.parent.name, 'size', len(s))
print('page details', s.count('<details'), 'summaries', re.findall(r'<summary><b>([0-9\-]+)</b>', s)[:10])
for kw in ('今日S/A', '席位荐票候选过滤', '当日榜与证据', '席位荐票与空仓', '席位台账与模拟盘持仓'):
    print('page has', kw, kw in s)
