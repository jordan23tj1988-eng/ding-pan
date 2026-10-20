# -*- coding: utf-8 -*-
import json, csv, os

B = "D:/股票数据/市场数据"
def rows(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

# 1 温度表
t = json.load(open(f"{B}/_学习/_市场温度表.json", encoding='utf-8'))
print("温度表 keys:", list(t.keys())[:10] if isinstance(t, dict) else len(t))
lst = t if isinstance(t, list) else t.get('行') or t.get('rows') or t.get('表')
for r in lst[-4:]:
    print("TEMP", json.dumps(r, ensure_ascii=False))

# 2 晋级
y = rows(f"{B}/20261019/zt_pool.csv")
print("昨日涨停数", len(y))
yfirst = [r for r in y if int(float(r['连板数'])) == 1]
y2 = [r for r in y if int(float(r['连板数'])) == 2]
y3 = [r for r in y if int(float(r['连板数'])) == 3]
ylian = [r for r in y if int(float(r['连板数'])) >= 2]
print("昨梯队: 首板%d 2板%d 3板%d 连板%d" % (len(yfirst), len(y2), len(y3), len(ylian)))
today_codes = {r['代码'] for r in rows(f"{B}/20261020/zt_pool.csv")}
y_codes = {r['代码'] for r in y}
print("昨涨停∩今涨停 %d" % len(y_codes & today_codes))
print("昨日连板今晋级:", [r['名称'] for r in ylian if r['代码'] in today_codes], "/", len(ylian))
print("昨3板今在池:", [r['名称'] for r in y3 if r['代码'] in today_codes])
print("昨2板今在池:", [r['名称'] for r in y2 if r['代码'] in today_codes], "/", len(y2))
first_up = [r for r in yfirst if r['代码'] in today_codes]
print("昨首板今在池 %d/%d" % (len(first_up), len(yfirst)))
# 今日2板中来自昨日首板
today2 = [r for r in rows(f"{B}/20261020/zt_pool.csv") if int(float(r['连板数'])) == 2]
print("今日2板:", [r['名称'] for r in today2], "其中昨首板:", sum(1 for r in today2 if r['代码'] in {x['代码'] for x in yfirst}))
today3 = [r for r in rows(f"{B}/20261020/zt_pool.csv") if int(float(r['连板数'])) == 3]
print("今日3板:", [r['名称'] for r in today3], "其中昨2板:", sum(1 for r in today3 if r['代码'] in {x['代码'] for x in y2}))
today4 = [r for r in rows(f"{B}/20261020/zt_pool.csv") if int(float(r['连板数'])) >= 4]
print("今日4板+:", [r['名称'] + str(r['连板数']) for r in today4], "其中昨3板:", sum(1 for r in today4 if r['代码'] in {x['代码'] for x in y3}))

# 3 bars cache 三票
for code in ("000530", "300045", "301586"):
    p = f"{B}/_学习/_bars_cache/{code}.csv"
    if not os.path.exists(p):
        print(code, "NO CACHE"); continue
    rr = rows(p)
    hdr = list(rr[0].keys())
    for r in rr[-4:]:
        print(code, json.dumps(r, ensure_ascii=False))

# 4 链条
c = json.load(open(f"{B}/_学习/涨停对链条_20261020.json", encoding='utf-8'))
print("链条 keys:", list(c.keys())[:20])
for k, v in c.items():
    if isinstance(v, dict) and k in ('统计', '汇总', 'metrics', '画像'):
        print("CHAIN", k, json.dumps(v, ensure_ascii=False)[:800])
    elif isinstance(v, list):
        print("CHAIN list", k, len(v))
    elif not isinstance(v, (dict, list)):
        print("CHAIN scalar", k, v)

# 5 能力预加载
cap = json.load(open(f"{B}/_学习/能力预加载_20261020.json", encoding='utf-8'))
print("CAP limitup:", json.dumps(cap.get('routes', {}).get('limitup'), ensure_ascii=False)[:800])

# 6 归位
g = json.load(open(f"{B}/_学习/题材归位_20261020.json", encoding='utf-8'))
print("归位 keys:", list(g.keys())[:10])
for k, v in g.items():
    if not isinstance(v, (dict, list)):
        print("GW", k, v)
print(json.dumps(g, ensure_ascii=False)[:600])
