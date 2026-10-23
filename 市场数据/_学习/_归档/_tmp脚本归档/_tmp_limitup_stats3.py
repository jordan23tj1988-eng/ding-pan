# -*- coding: utf-8 -*-
import json, io, os
from collections import Counter, defaultdict
base = r'D:\股票数据\市场数据\_学习'
d = json.load(io.open(os.path.join(base, '涨停质量荐票_20260818.json'), encoding='utf-8'))
det = d['明细']
# 质量分Top5
top5 = sorted(det, key=lambda x: -x.get('质量分', 0))[:5]
print('=== 质量分Top5 ===')
for x in top5:
    print(x['代码'], x['名称'], '质量分', x.get('质量分'), '抓龙率', x['抓龙率'], '命中', x['命中数'],
          '连板', x['连板'], '首封', x.get('首封时间'), '开板', x.get('开板次数'), '封单比', x.get('封单比'),
          '执1', x['预测执1胜率'], x['预测执1均涨'], '执2', x['预测执2胜率'], x['预测执2均涨'], '大方向', x.get('大方向'))
# 命中规则票
print('=== 命中规则数>0 ===', sum(1 for x in det if x['命中数'] > 0))

# 对链条主线结构
lz = json.load(io.open(os.path.join(base, '涨停对链条_20260818.json'), encoding='utf-8'))
print('=== 对链条顶层keys ===', list(lz.keys()))
# 尝试找题材/线聚合
