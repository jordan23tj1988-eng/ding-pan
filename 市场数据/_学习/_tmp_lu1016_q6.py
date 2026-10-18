# -*- coding: utf-8 -*-
import csv, os, json
M=r"D:\股票数据\市场数据"
def R(p):
    return list(csv.DictReader(open(p,encoding="utf-8-sig")))
y=R(os.path.join(M,"20261015","zt_pool.csv")); t=R(os.path.join(M,"20261016","zt_pool.csv"))
zb=R(os.path.join(M,"20261016","zb_pool.csv")); dt=R(os.path.join(M,"20261016","dt_pool.csv"))
yt={r["代码"]:r for r in y}
print("昨日涨停",len(y),"今日涨停",len(t))
import collections
c=collections.Counter(r["连板数"] for r in y); print("昨日梯队",dict(sorted(c.items(),key=lambda x:-int(x[0]))))
c2=collections.Counter(r["连板数"] for r in t); print("今日梯队",dict(sorted(c2.items(),key=lambda x:-int(x[0]))))
tody={r["代码"]:r for r in t}; zd={r["代码"]:r for r in zb}; dd={r["代码"]:r for r in dt}
again=[k for k in yt if k in tody]; boom=[k for k in yt if k in zd]; die=[k for k in yt if k in dd]
print("昨涨停→今再涨停 %d (%.1f%%)"%(len(again),len(again)/len(y)*100))
print("昨涨停→今炸板 %d (%.1f%%)"%(len(boom),len(boom)/len(y)*100))
print("昨涨停→今跌停 %d (%.1f%%)"%(len(die),len(die)/len(y)*100))
# 一进二
y1=[r["代码"] for r in y if r["连板数"]=="1"]
y2=[r["代码"] for r in y if int(r["连板数"])>=2]
t2=[r["代码"] for r in t if int(r["连板数"])>=2]
print("\n昨日首板 %d → 今日连板≥2: %d = %.1f%%"%(len(y1),sum(1 for k in y1 if k in t2),sum(1 for k in y1 if k in t2)/len(y1)*100))
print("昨日连板≥2 %d → 今日连板≥3: %d = %.1f%%"%(len(y2),sum(1 for k in y2 if k in [r["代码"] for r in t if int(r["连板数"])>=3]),sum(1 for k in y2 if k in [r["代码"] for r in t if int(r["连板数"])>=3])/len(y2)*100))
print("昨日连板≥2 明细:",[(r["代码"],r["名称"],r["连板数"],"今日:"+(tody.get(r["代码"],{}).get("连板数","-") if r["代码"] in tody else ("炸板" if r["代码"] in zd else ("跌停" if r["代码"] in dd else "其余")))) for r in y if int(r["连板数"])>=2])
# 核按钮: 昨日涨停今日跌停 or 低开大跌
print("\n昨涨停今跌停:",[(k,yt[k]["名称"],yt[k]["连板数"]) for k in die])
# 今日炸板的 昨日身位
print("今日炸板49只中昨日涨停的 %d 只"%len(boom))
print([(zd[k]["名称"],zd[k]["涨跌幅"][:5],yt[k]["连板数"]) for k in boom])
