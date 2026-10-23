# -*- coding: utf-8 -*-
import json, io, os
from collections import Counter
base = r'D:\股票数据\市场数据\_学习'
g = json.load(io.open(os.path.join(base, '题材归位_20260818.json'), encoding='utf-8'))
# 找到映射结构
print('顶层keys:', list(g.keys()))
# 统计来源档
cnt = Counter()
for k, v in g.items():
    if isinstance(v, dict):
        s = v.get('来源档') or v.get('档') or v.get('source')
        if s: cnt[s] += 1
print('来源档分布:', dict(cnt))
# 找C档票
for k, v in g.items():
    if isinstance(v, dict):
        s = v.get('来源档') or v.get('档')
        if s == 'C':
            print('C档票:', k, v)
