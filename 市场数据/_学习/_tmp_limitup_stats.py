# -*- coding: utf-8 -*-
import json, io, os
base = r'D:\股票数据\市场数据\_学习'

d = json.load(io.open(os.path.join(base, '涨停质量荐票_20260818.json'), encoding='utf-8'))
det = d['明细']
n = len(det)
e1 = [x['预测执1胜率'] for x in det]
e2 = [x['预测执2胜率'] for x in det]
print('打标数', d.get('打标数'), '明细len', n)
print('执1胜率 max/中位/均值', round(max(e1), 1), round(sorted(e1)[n // 2], 1), round(sum(e1) / n, 2))
print('执1均涨 均值', round(sum(x['预测执1均涨'] for x in det) / n, 3))
print('执2胜率 max', round(max(e2), 1), '执2均涨均值', round(sum(x['预测执2均涨'] for x in det) / n, 3))
hit = sum(1 for x in det if x['命中数'] > 0)
print('命中规则票数', hit, '/', n)
print('库窗口', d.get('库窗口'), '库样本', d.get('库样本'))
from collections import Counter
lb = Counter(x['连板'] for x in det)
print('连板分布', dict(lb))
top = sorted(det, key=lambda x: -x['抓龙率'])[:6]
for x in top:
    print('抓龙Top', x['代码'], x['名称'], '抓龙率', x['抓龙率'], '命中', x['命中数'], '连板', x['连板'], '大方向', x.get('大方向'))
# 命中规则票列表
print('--- 命中规则票 ---')
for x in det:
    if x['命中数'] > 0:
        print(x['代码'], x['名称'], '命中', x['命中数'], '连板', x['连板'], '执1', x['预测执1胜率'], x['预测执1均涨'], '抓龙率', x['抓龙率'], '大方向', x.get('大方向'))
