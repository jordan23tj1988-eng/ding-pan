# -*- coding: utf-8 -*-
"""把 judgment_20260929.json 的缩进还原为原风格 indent=1(与 .bak_fix2 一致), 让 diff 只剩意图内改动。"""
import json, difflib
from pathlib import Path

BASE = Path(r'D:\股票数据\市场数据')
J = BASE / '_学习' / 'judgment_20260929.json'
BAK = J.with_suffix('.json.bak_fix2_20260930')
norm = J.with_suffix('.json.bak_fix2_20260930')  # 参考基线

doc = json.loads(J.read_text(encoding='utf-8'))
J.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')

cur = J.read_text(encoding='utf-8').splitlines()
old = BAK.read_text(encoding='utf-8').splitlines()
diff = [l for l in difflib.unified_diff(old, cur, lineterm='', n=2)]
print('diff 行数:', len(diff))
for l in diff[:40]:
    print(l[:200])
print('...' if len(diff) > 40 else '')
# 语义等价断言(除两处意图改动外)
a, b = json.loads(BAK.read_text(encoding='utf-8')), json.loads(J.read_text(encoding='utf-8'))
same_keys = set(a) == set(b)
print('顶层键一致:', same_keys)
diff_keys = [k for k in a if json.dumps(a[k], ensure_ascii=False) != json.dumps(b[k], ensure_ascii=False)]
print('内容有差异的顶层键:', diff_keys)
