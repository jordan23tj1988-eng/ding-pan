# -*- coding: utf-8 -*-
import csv,json,statistics
D="D:/股票数据/市场数据/"
zt=list(csv.DictReader(open(D+"20261023/zt_pool.csv",encoding='utf-8-sig')))
g=json.load(open(D+"_学习/题材归位_20261023.json",encoding='utf-8'))["映射"]
by={}
for r in zt:
    c=r["代码"];a=g.get(c,{});line=a.get("大方向","未归位")
    fl=float(r["流通市值"]);fz=float(r["封板资金"])
    by.setdefault(line,[]).append((r["名称"],fz/fl*100,int(float(r["连板数"] or 0)),int(float(r["炸板次数"] or 0)),a.get("环节","")))
for k,v in sorted(by.items(),key=lambda kv:-len(kv[1])):
    print(f"{k:6s} n={len(v):2d} 封单率中位={statistics.median([x[1] for x in v]):.2f}% 二板={sum(1 for x in v if x[2]==2)} 炸合计={sum(x[3] for x in v)}")
print("\n消费环节:", [x[4] for x in by["消费"]])
print("消费封单:", [(x[0],round(x[1],2),x[2]) for x in sorted(by["消费"],key=lambda y:-y[1])])
