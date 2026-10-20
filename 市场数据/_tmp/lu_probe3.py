# -*- coding: utf-8 -*-
import json, csv, os

B = "D:/股票数据/市场数据"
def rows(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

t = json.load(open(f"{B}/_学习/_市场温度表.json", encoding='utf-8'))
ks = sorted(t.keys())
for k in ks[-4:]:
    print("TEMP", k, json.dumps(t[k], ensure_ascii=False))

y = rows(f"{B}/20261019/zt_pool.csv")
print("昨日涨停数", len(y))
yfirst = [r for r in y if int(float(r['连板数'])) == 1]
y2 = [r for r in y if int(float(r['连板数'])) == 2]
y3 = [r for r in y if int(float(r['连板数'])) == 3]
ylian = [r for r in y if int(float(r['连板数'])) >= 2]
print("昨梯队: 首板%d 2板%d 3板%d 连板%d" % (len(yfirst), len(y2), len(y3), len(ylian)))
z = rows(f"{B}/20261020/zt_pool.csv")
today_codes = {r['代码'] for r in z}
y_codes = {r['代码'] for r in y}
print("昨涨停∩今涨停 %d" % len(y_codes & today_codes))
print("昨日连板今晋级:", [r['名称'] for r in ylian if r['代码'] in today_codes], "/", len(ylian))
print("昨3板今在池:", [r['名称'] for r in y3 if r['代码'] in today_codes])
print("昨2板今在池:", [r['名称'] for r in y2 if r['代码'] in today_codes], "/", len(y2))
print("昨首板今在池 %d/%d" % (len([r for r in yfirst if r['代码'] in today_codes]), len(yfirst)))
yf = {r['代码'] for r in yfirst}; y2c = {r['代码'] for r in y2}; y3c = {r['代码'] for r in y3}
today2 = [r for r in z if int(float(r['连板数'])) == 2]
today3 = [r for r in z if int(float(r['连板数'])) == 3]
today4 = [r for r in z if int(float(r['连板数'])) >= 4]
print("今日2板:", [r['名称'] for r in today2], "源自昨首板", sum(1 for r in today2 if r['代码'] in yf))
print("今日3板:", [r['名称'] for r in today3], "源自昨2板", sum(1 for r in today3 if r['代码'] in y2c))
print("今日4板+:", [r['名称'] + str(r['连板数']) for r in today4], "源自昨3板", sum(1 for r in today4 if r['代码'] in y3c))

for code in ("000530", "300045", "301586"):
    p = f"{B}/_学习/_bars_cache/{code}.csv"
    if not os.path.exists(p):
        print(code, "NO CACHE"); continue
    rr = rows(p)
    for r in rr[-3:]:
        print(code, json.dumps(r, ensure_ascii=False))

c = json.load(open(f"{B}/_学习/涨停对链条_20261020.json", encoding='utf-8'))
print("链条 keys:", list(c.keys())[:20])
for k, v in c.items():
    if isinstance(v, (str, int, float)) or v is None:
        print("CHAIN scalar", k, str(v)[:200])
    elif isinstance(v, dict):
        print("CHAIN dict", k, list(v.keys())[:15])
    elif isinstance(v, list):
        print("CHAIN list", k, len(v), json.dumps(v[0], ensure_ascii=False)[:400] if v else "")

cap = json.load(open(f"{B}/_学习/能力预加载_20261020.json", encoding='utf-8'))
print("CAP limitup:", json.dumps(cap.get('routes', {}).get('limitup'), ensure_ascii=False)[:800])

g = json.load(open(f"{B}/_学习/题材归位_20261020.json", encoding='utf-8'))
print("归位 top keys:", list(g.keys())[:12])
print(json.dumps(g, ensure_ascii=False)[:700])
