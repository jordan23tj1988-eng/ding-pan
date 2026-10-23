# -*- coding: utf-8 -*-
import csv, json, statistics
D="D:/股票数据/市场数据/"
def rd(p):
    with open(p, encoding='utf-8-sig') as f: return list(csv.DictReader(f))
days=["20261012","20261013","20261014","20261015","20261016","20261019","20261020","20261021","20261022","20261023"]
panel={}
for d in days:
    rows=rd(D+d+"/zt_pool.csv")
    for r in rows:
        try:
            fz=float(r["封板资金"]); fl=float(r["流通市值"]); hs=float(r["换手率"])
        except: continue
        panel.setdefault(d,{})[r["代码"]]=dict(name=r["名称"], seal=fz, float=fl, sealr=fz/fl*100 if fl else 0,
            turn=hs, zha=int(float(r["炸板次数"] or 0)), lb=int(float(r["连板数"] or 0)),
            first=str(r["首次封板时间"]).zfill(6), px=float(r["最新价"]), amt=float(r["成交额"]))
# 机器人 line per day from 归位
print("date      width  2板  3板+  开板占比  封单中位  早封<=0936  炸合计  最高板  晋级率")
for d in days:
    gp=D+"_学习/题材归位_"+d+".json"
    try: g=json.load(open(gp,encoding='utf-8'))["映射"]
    except: print(d,"no 归位"); continue
    mp=g
    rob=[v for c,v in panel.get(d,{}).items() if mp.get(c,{}).get("大方向")=="机器人"]
    if not rob: print(d,"0"); continue
    n=len(rob); b2=sum(1 for x in rob if x["lb"]==2); b3=sum(1 for x in rob if x["lb"]>=3)
    op=sum(1 for x in rob if x["zha"]>0)/n
    med=statistics.median([x["sealr"] for x in rob])
    er=sum(1 for x in rob if x["first"]<="093600")
    print(f"{d}  {n:4d} {b2:4d} {b3:5d}  {op:8.2f} {med:9.2f}% {er:9d}/{n:<3d} {sum(x['zha'] for x in rob):5d}  {max(x['lb'] for x in rob):5d}")
# T vs T-1 detail for 20261023 机器人
g23=json.load(open(D+"_学习/题材归位_20261023.json",encoding='utf-8'))["映射"]
g22=json.load(open(D+"_学习/题材归位_20261022.json",encoding='utf-8'))["映射"]
print("\n=== 20261023 机器人 逐只 + T-1 质量 ===")
print("code name       lb  first   zha  sealr    turn    T-1sealr T-1turn 双日确认  T-1线")
for c,x in sorted(panel["20261023"].items(), key=lambda kv:(-kv[1]["lb"], -kv[1]["sealr"])):
    if g23.get(c,{}).get("大方向")!="机器人": continue
    p=panel["20261022"].get(c)
    s1=f"{p['sealr']:.2f}%" if p else "—"
    t1=f"{p['turn']:.1f}" if p else "—"
    ok="—"
    if p:
        ok="PASS" if (x["sealr"]>=1.5 and p["sealr"]>=1.0 and x["turn"]<=p["turn"]*1.5) else "fail"
    print(f"{c} {x['name']:8s} {x['lb']}  {x['first']} {x['zha']:4d} {x['sealr']:7.2f}% {x['turn']:7.1f}% {s1:>8s} {t1:>7s} {ok:6s} {g22.get(c,{}).get('大方向','—')}")
