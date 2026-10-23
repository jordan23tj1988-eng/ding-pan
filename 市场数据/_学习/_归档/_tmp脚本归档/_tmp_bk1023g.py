# -*- coding: utf-8 -*-
import os, json, csv
L = r"D:/股票数据/市场数据/_学习"
B = r"D:/股票数据/市场数据"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
cold=[r for r in recs if r["temp"]<25]
tr=[r for r in cold if r["tradeable"]]
base=sum(r["e1"] for r in tr)/len(tr)
print("冰点严格可成交基线 %.3f%% n=%d" % (base, len(tr)))
def rep(tag, rs):
    x=[r for r in rs if r["tradeable"]]
    if not x: print("  %-30s n=%d 全不可成交"% (tag,len(rs))); return
    m=sum(r["e1"] for r in x)/len(x); w=100*sum(1 for r in x if r["e1"]>0)/len(x)
    print("  %-30s 全池n=%3d 剔%2d 可成交n=%3d 均%+.3f%% 超额%+.3fpp 胜率%5.1f%%" % (tag,len(rs),len(rs)-len(x),len(x),m,m-base,w))
for tag,f in [("①整格 封单<0.5×换手3-10",lambda r:r["seal"]<0.5 and 3<=r["to"]<=10),
              ("  └换手3-5%",lambda r:r["seal"]<0.5 and 3<=r["to"]<5),
              ("  └换手5-7%",lambda r:r["seal"]<0.5 and 5<=r["to"]<7),
              ("  └换手7-10%",lambda r:r["seal"]<0.5 and 7<=r["to"]<=10),
              ("  └首板",lambda r:r["seal"]<0.5 and 3<=r["to"]<=10 and r["lb"]==1),
              ("  └炸0",lambda r:r["seal"]<0.5 and 3<=r["to"]<=10 and r["zb"]==0),
              ("  └炸>=2",lambda r:r["seal"]<0.5 and 3<=r["to"]<=10 and r["zb"]>=2)]:
    rep(tag,[r for r in cold if f(r)])

# 今日落格计数
rows=list(csv.DictReader(open(os.path.join(B,"20261023","zt_pool.csv"), encoding="utf-8-sig")))
c1=c2=c3=0
for r in rows:
    seal=float(r["封板资金"])/float(r["流通市值"])*100; to=float(r["换手率"]); ft=str(r["首次封板时间"]).zfill(6)
    lb=int(float(r["连板数"])); zb=int(float(r["炸板次数"]))
    if seal<0.5 and 3<=to<=10: c1+=1
    if seal>=4 and zb==0: c2+=1
    if ft>"143000" and lb==1: c3+=1
print("\n今日落格: ①%d只 ②%d只 ③%d只 (池82)" % (c1,c2,c3))
# 一进二 权威复算
import collections
y=list(csv.DictReader(open(os.path.join(B,"20261022","zt_pool.csv"), encoding="utf-8-sig")))
y1=[r for r in y if r["涨停统计"].split("/")[0]=="1"] if "涨停统计" in y[0] else []
first=[r for r in y if int(float(r["连板数"]))==1]
codes={r["代码"] for r in rows}
hit=[r["代码"] for r in first if r["代码"] in codes]
print("昨首板 %d 只, 今日仍涨停 %d 只 → 一进二 %.1f%%" % (len(first), len(hit), 100*len(hit)/len(first)))
print("昨池 %d, 今日涨停交集 %d" % (len(y), len({r['代码'] for r in y} & codes)))
