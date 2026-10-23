# -*- coding: utf-8 -*-
import os, json, csv
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
env = json.load(open(os.path.join(L,"_tmp_env.json"), encoding="utf-8"))
fix = set(env["fix"])
BC = os.path.join(L,"_bars_cache"); cache={}
def bars(code):
    if code in cache: return cache[code]
    p=os.path.join(BC, code+".csv")
    cache[code] = {b["date"].replace("-",""): b for b in csv.DictReader(open(p, encoding="utf-8-sig"))} if os.path.exists(p) else {}
    return cache[code]
for r in recs:
    b = bars(r["code"]); ds = sorted(b.keys())
    if r["d"] in b and ds.index(r["d"])+1 < len(ds):
        b1 = b[ds[ds.index(r["d"])+1]]
        o,h = float(b1["open"]), float(b1["high"])
        r["loose"] = not (r["yizi"] or (r["gap"]>=9.5 and abs(o-h)<1e-9))
inpool = {(r["d"], r["code"]) for r in recs}
dl = sorted(set(r["d"] for r in recs)); nxt={d:dl[i+1] for i,d in enumerate(dl[:-1])}
for r in recs:
    nd = nxt.get(r["d"]); r["sn"] = 1 if nd and (nd, r["code"]) in inpool else 0

def base(rs): 
    x=[r for r in rs if r["tradeable"]]
    return (sum(r["e1"] for r in x)/len(x) if x else 0)
out=[]
def P(s): out.append(s)
def rep(tag, rs, b):
    x=[r for r in rs if r["tradeable"]]
    if not x: P("  %-30s n=%d 全不可成交"%(tag,len(rs))); return
    m=sum(r["e1"] for r in x)/len(x); w=100*sum(1 for r in x if r["e1"]>0)/len(x)
    sr=100*sum(r["sn"] for r in rs)/len(rs)
    P("  %-30s 全池n=%4d 剔%3d 可成交n=%4d 均%+.3f%% 超额%+.3fpp 胜率%5.1f%% 次封%5.1f%%"%(tag,len(rs),len(rs)-len(x),len(x),m,m-b,w,sr))

neu=[r for r in recs if 45<=r["temp"]<65]; nb=base(neu)
cold=[r for r in recs if r["temp"]<25]; cb=base(cold); cbt=sum(r["e1"] for r in cold)/len(cold)
fixr=[r for r in recs if r["d"] in fix]; fb=base(fixr); fbt=sum(r["e1"] for r in fixr)/len(fixr)
P("中性(45-65) 全池n=%d 全池均%.3f%% 可成交基线%.3f%% (n=%d)"%(len(neu),sum(r["e1"] for r in neu)/len(neu),nb,len([r for r in neu if r["tradeable"]])))
P("冰点(<25) 全池n=%d 全池均%.3f%% 可成交基线%.3f%% (n=%d) 剔%.1f%%"%(len(cold),cbt,cb,len([r for r in cold if r["tradeable"]]),100*(1-len([r for r in cold if r["tradeable"]])/len(cold))))
P("修复日n=%d 全池均%.3f%% 可成交基线%.3f%%"%(len(fixr),fbt,fb))
P("\n[中性桶]")
for tag,f in [("首封<=09:25",lambda r:r["ft"]<="092500"),("09:26-09:31",lambda r:"092500"<r["ft"]<="093100"),
  ("09:32-10:00",lambda r:"093100"<r["ft"]<="100000"),("10:01-13:00",lambda r:"100000"<r["ft"]<="130000"),
  ("13:01-14:00",lambda r:"130000"<r["ft"]<="140000"),("14:01-14:30",lambda r:"140000"<r["ft"]<="143000"),
  (">14:30",lambda r:r["ft"]>"143000"),
  ("封单<0.5%",lambda r:r["seal"]<0.5),("0.5-1%",lambda r:0.5<=r["seal"]<1),("1-2%",lambda r:1<=r["seal"]<2),
  ("2-4%",lambda r:2<=r["seal"]<4),(">=4%",lambda r:r["seal"]>=4),
  ("炸0",lambda r:r["zb"]==0),("炸1",lambda r:r["zb"]==1),("炸2-4",lambda r:2<=r["zb"]<=4),("炸>=5",lambda r:r["zb"]>=5),
  ("换手<3%",lambda r:r["to"]<3),("换手3-10%",lambda r:3<=r["to"]<=10),("换手10-20%",lambda r:10<r["to"]<=20),("换手>=20%",lambda r:r["to"]>20),
  ("首板",lambda r:r["lb"]==1),("2板",lambda r:r["lb"]==2),("3板",lambda r:r["lb"]==3),("4板+",lambda r:r["lb"]>=4),
  ("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),("连板>=5×炸0",lambda r:r["lb"]>=5 and r["zb"]==0),
  ("换手>=20×首封<=10:00",lambda r:r["to"]>20 and r["ft"]<="100000"),
  ("炸>=5×换手>=20%",lambda r:r["zb"]>=5 and r["to"]>20)]:
    rep(tag,[r for r in neu if f(r)],nb)
P("\n[冰点 MA 三格 两种可成交口径]")
def ma(tag,f):
    a=[r for r in cold if f(r)]
    if not a: P(tag+" empty"); return
    m=sum(r["e1"] for r in a)/len(a)
    for nm,key in (("原M-04","loose"),("严格分板","tradeable")):
        x=[r for r in a if r[key]]
        if not x: P("  %s %s 全不可成交"%(tag,nm)); continue
        mm=sum(r["e1"] for r in x)/len(x); w=100*sum(1 for r in x if r["e1"]>0)/len(x)
        P("  %-26s[%s] 全池n=%3d 均%+.3f%% 超%+.3fpp | 剔%2d n=%3d 均%+.3f%% 超%+.3fpp 胜%5.1f%%"%(
          tag,nm,len(a),m,m-cbt,len(a)-len(x),len(x),mm,mm-cb,w))
ma("①封单<0.5×换手3-10",lambda r:r["seal"]<0.5 and 3<=r["to"]<=10)
ma("②封单>=4×炸0",lambda r:r["seal"]>=4 and r["zb"]==0)
ma("③首封>14:30×首板",lambda r:r["ft"]>"143000" and r["lb"]==1)
P("\n[①子段 严格口径]")
for tag,f in [("换手3-5%",lambda r:r["seal"]<0.5 and 3<=r["to"]<5),("换手5-7%",lambda r:r["seal"]<0.5 and 5<=r["to"]<7),
              ("换手7-10%",lambda r:r["seal"]<0.5 and 7<=r["to"]<=10)]:
    a=[r for r in cold if f(r)]; x=[r for r in a if r["tradeable"]]
    m=sum(r["e1"] for r in x)/len(x)
    P("  %-10s 全池n=%2d 可成交n=%2d 均%+.3f%% 超额%+.3fpp 胜率%5.1f%%"%(tag,len(a),len(x),m,m-cb,100*sum(1 for r in x if r["e1"]>0)/len(x)))
P("\n[修复日桶]")
for tag,f in [("首板",lambda r:r["lb"]==1),("2板+",lambda r:r["lb"]>=2),("换手>=10%",lambda r:r["to"]>=10),
              ("封单0.5-2%",lambda r:0.5<=r["seal"]<2),("炸>=3",lambda r:r["zb"]>=3)]:
    rep(tag,[r for r in fixr if f(r)],fb)
P("\n[全窗 高位]")
allb=base(recs)
for tag,f in [("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),("连板>=5×炸0",lambda r:r["lb"]>=5 and r["zb"]==0),
              ("连板>=4×炸>=2",lambda r:r["lb"]>=4 and r["zb"]>=2),("连板>=4×炸0",lambda r:r["lb"]>=4 and r["zb"]==0)]:
    rep(tag,[r for r in recs if f(r)],allb)
# 今日候选
P("\n[今日候选票落桶]")
rows=list(csv.DictReader(open(r"D:/股票数据/市场数据/20261023/zt_pool.csv", encoding="utf-8-sig")))
for r in rows:
    if r["代码"] in ("003021","300561","002724","603278","301502","000678"):
        seal=float(r["封板资金"])/float(r["流通市值"])*100
        P("  %s %s 板%s 首封%s 炸%s 封单%.3f%% 换手%.2f 流通%.1f亿 成交%.2f亿 封单额%.2f亿 行业%s"%(
          r["代码"],r["名称"],r["连板数"],r["首次封板时间"],r["炸板次数"],seal,float(r["换手率"]),
          float(r["流通市值"])/1e8,float(r["成交额"])/1e8,float(r["封板资金"])/1e8,r["所属行业"]))
open(os.path.join(L,"_tmp_out_1023.txt"),"w",encoding="utf-8").write("\n".join(out))
print("written", len(out), "lines")
