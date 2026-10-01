# -*- coding: utf-8 -*-
"""20260930 数据层修复(只改 judgment_20260929.json 的正文标题/表述, 不动生产脚本):
 1) lhb 板块机器直通段 h2 序号分隔符 '、' -> ' ' (对齐黄金页/渲染器契约 <h2>一 / <h2>三 )
 2) limitup 段六 残留 C1 禁词 '沿用20260928' -> '依据20260928'(语义不变, 避开 沿用+前交易日 词表)
写入前断言唯一性; 备份 .bak_fix2_20260930; 回读校验。
"""
import json, shutil
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
J = BASE / '_学习' / 'judgment_20260929.json'
BAK = J.with_suffix('.json.bak_fix2_20260930')

raw = J.read_text(encoding='utf-8')
doc = json.loads(raw)
bodies = doc['bodies']

lhb = bodies['lhb']
edits = [
    ('<h2>一、当日榜与证据</h2>', '<h2>一 当日榜与证据</h2>'),
    ('<h2>三、席位荐票候选过滤</h2>', '<h2>三 席位荐票候选过滤</h2>'),
]
for old, new in edits:
    n = lhb.count(old)
    assert n == 1, ('lhb 目标串不唯一: %r x%d' % (old, n))
    lhb = lhb.replace(old, new)
bodies['lhb'] = lhb

lim = bodies['limitup']
old = '沿用20260928'
n = lim.count(old)
assert n == 1, ('limitup 目标串不唯一: %r x%d' % (old, n))
i = lim.find(old)
print('limitup 上下文:', lim[max(0, i - 60):i + 60].replace('\n', ' '))
lim = lim.replace(old, '依据20260928')
bodies['limitup'] = lim

if not BAK.exists():
    shutil.copy2(J, BAK)
    print('已备份', BAK.name)
else:
    print('备份已存在, 保留', BAK.name)

J.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')

# 回读校验
back = json.loads(J.read_text(encoding='utf-8'))
import re
print('回读 lhb h2:', re.findall(r'<h2[^>]*>([^<]{0,40})', back['bodies']['lhb'])[:9])
print('回读 limitup 含沿用20260928:', '沿用20260928' in back['bodies']['limitup'],
      '| 含依据20260928:', '依据20260928' in back['bodies']['limitup'])
print('其余路 body 是否变长/变短(应不变):', {k: (len(v), len(bodies[k])) for k, v in doc['bodies'].items()})
