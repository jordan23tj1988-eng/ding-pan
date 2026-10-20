# -*- coding: utf-8 -*-
import json, csv
B = "D:/股票数据/市场数据"
lib = json.load(open(f"{B}/_学习/_涨停质量库.json", encoding='utf-8'))
f = lib['因子']
for name in ("换手率", "首封时间", "开板次数", "封单比"):
    v = f[name]
    print("==", name, json.dumps({k: v[k] for k in v if k not in ('桶', '表')}, ensure_ascii=False))
    for key in ('桶', '表', '分桶'):
        if key in v:
            for b in v[key]:
                print("   ", json.dumps(b, ensure_ascii=False))
print("基准", json.dumps(lib.get('基准'), ensure_ascii=False)[:600])

q = json.load(open(f"{B}/_学习/涨停质量荐票_20261020.json", encoding='utf-8'))
det = q['明细']
# 首封分布
import collections
def slot(t):
    if t <= '092500': return '一字<=09:25'
    if t <= '093100': return '秒板<=09:31'
    if t <= '100000': return '早盘09:31-10:00'
    if t <= '140000': return '盘中10:00-14:00'
    return '尾盘>14:00'
c = collections.Counter(slot(x['首封']) for x in det)
print("首封分布", dict(c))
print("开板分布", dict(collections.Counter(x['开板次数'] for x in det)))
def tb(h):
    if h < 3: return '<3%'
    if h < 10: return '3-10%'
    if h < 20: return '10-20%'
    return '>=20%'
print("换手桶", dict(collections.Counter(tb(x['换手']) for x in det)))
print("封单比>=2%%家数", sum(1 for x in det if x['封单比'] >= 2))
print("开板>=5", [(x['代码'], x['名称'], x['开板次数']) for x in det if x['开板次数'] >= 5])
print("一字<=0925 家数", sum(1 for x in det if x['首封'] <= '0925'))
# 换手桶 x 预测
agg = {}
for x in det:
    agg.setdefault(tb(x['换手']), []).append(x['预测执1均涨'])
print({k: (len(v), round(sum(v)/len(v), 3)) for k, v in agg.items()})
