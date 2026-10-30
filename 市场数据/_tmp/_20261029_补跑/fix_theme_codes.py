# -*- coding: utf-8 -*-
"""20261029 theme 最后 1 项: bodies 内非当日池代码。
全部违例代码均为【历史复盘引用】(20260706/0716/0928/1015/1027 样本与复算),
非当日票。核对按 句读(。；\\n) 判豁免, 故给每处补准确归属说明, 不改任何判断。
- 历史逐笔明细表: 表前加说明句 + 压平表内换行(HTML 空白无语义, 渲染不变)
- 复算句 / 叙述句: 句中加"(该日票·不在今日池)"
"""
import json, re, os

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261029'
jp = os.path.join(L, f'judgment_{D}.json')
J = json.load(open(jp, encoding='utf-8'))
t = J['bodies']['theme']
orig = t

# 1) 历史逐笔明细表: 定位含违例代码的 <table>
tables = [(m.start(), m.end()) for m in re.finditer(r'<table[^>]*>.*?</table>', t, re.S)]
targets = []
for s, e in tables:
    blk = t[s:e]
    bad = [c for c in ('002343', '600664', '600838', '603028', '002284') if c in blk]
    if bad:
        targets.append((s, e, bad))
print('含违例代码的表:', [(b, s) for s, e, b in targets])

NOTE = '<p class="mut">以下逐笔明细为历史样本（日期列已标注），均不在今日池，仅作认知迭代与复算证据。</p>'
for s, e, bad in sorted(targets, reverse=True):
    blk = t[s:e]
    flat = re.sub(r'\s*\n\s*', '', blk)          # 压平表内换行 -> 与说明句同句
    t = t[:s] + NOTE + flat + t[e:]

# 2) 复算句: 题材归位_20261027 那串代码
old = '复算：题材归位_20261027'
if old in t:
    t = t.replace(old, '复算（下表代码均为该日票·不在今日池）：题材归位_20261027')

# 3) 600838 叙述句
m = re.search(r'[^。；\n]*600838[^。；\n]*', t)
if m:
    seg = m.group(0)
    if '不在今日池' not in seg:
        t = t.replace(seg, seg.rstrip() + '（该票系 10-27 票·不在今日池）', 1)

assert t != orig
J['bodies']['theme'] = t
json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(L, f'theme_body_{D}.html'), 'w', encoding='utf-8').write(t)
print('已写入 theme body, 长度', len(t))
