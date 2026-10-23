# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
env = json.load(open(os.path.join(L,"_tmp_env.json"), encoding="utf-8"))
prev, fix = env["prev"], set(env["fix"])
inpool = {(r["d"], r["code"]) for r in recs}
dl = sorted(set(r["d"] for r in recs))
nxt = {d: dl[i+1] for i,d in enumerate(dl[:-1])}
for r in recs:
    nd = nxt.get(r["d"])
    r["seal_next"] = 1 if nd and (nd, r["code"]) in inpool else 0

def sub(pred): return [r for r in recs if pred(r)]

def report(tag, rs):
    if not rs:
        print("  %-28s EMPTY" % tag); return
    tr = [r for r in rs if r["tradeable"]]
    allm = sum(r["e1"] for r in rs)/len(rs)
    trm = sum(r["e1"] for r in tr)/len(tr) if tr else 0
    w = 100*sum(1 for r in tr if r["e1"]>0)/len(tr) if tr else 0
    sr = 100*sum(r["seal_next"] for r in rs)/len(rs)
    print("  %-28s 全池n=%4d 剔%3d 可成交n=%4d 均%+.2f%% 超额%+.2fpp 胜率%5.1f%% 次日封板%5.1f%%" %
          (tag, len(rs), len(rs)-len(tr), len(tr), trm, trm-allm, w, sr))

print("=== 环境基线（可成交执1均）===")
for tag, pred in [("冰点<25", lambda r: r["temp"]<25), ("偏冷25-45", lambda r: 25<=r["temp"]<45),
                  ("中性45-65", lambda r: 45<=r["temp"]<65), ("偏热>=65", lambda r: r["temp"]>=65),
                  ("修复日(T-1<25,T>=45)", lambda r: r["d"] in fix)]:
    report(tag, sub(pred))

neu = sub(lambda r: 45<=r["temp"]<65)
fixs = sub(lambda r: r["d"] in fix)
print("\n=== 中性(45-65)环境桶表 n=%d ===" % len(neu))
for tag,f in [("首封<=09:25",lambda r:r["ft"]<="092500"),("09:26-09:31",lambda r:"092500"<r["ft"]<="093100"),
              ("09:32-10:00",lambda r:"093100"<r["ft"]<="100000"),("10:01-13:00",lambda r:"100000"<r["ft"]<="130000"),
              ("13:01-14:00",lambda r:"130000"<r["ft"]<="140000"),("14:01-14:30",lambda r:"140000"<r["ft"]<="143000"),
              (">14:30",lambda r:r["ft"]>"143000"),
              ("封单<0.5%",lambda r:r["seal"]<0.5),("0.5-1%",lambda r:0.5<=r["seal"]<1),("1-2%",lambda r:1<=r["seal"]<2),
              ("2-4%",lambda r:2<=r["seal"]<4),(">=4%",lambda r:r["seal"]>=4),
              ("炸0",lambda r:r["zb"]==0),("炸1",lambda r:r["zb"]==1),("炸2-4",lambda r:2<=r["zb"]<=4),("炸>=5",lambda r:r["zb"]>=5),
              ("换手<3%",lambda r:r["to"]<3),("换手3-10%",lambda r:3<=r["to"]<=10),("换手10-20%",lambda r:10<r["to"]<=20),("换手>=20%",lambda r:r["to"]>20),
              ("首板",lambda r:r["lb"]==1),("2板",lambda r:r["lb"]==2),("3板",lambda r:r["lb"]==3),("4板+",lambda r:r["lb"]>=4)]:
    report(tag, [r for r in neu if f(r)])

print("\n=== 修复日(prev<25,T>=45)桶表 n=%d ===" % len(fixs))
for tag,f in [("首封<=10:00",lambda r:r["ft"]<="100000"),("10:01-14:00",lambda r:"100000"<r["ft"]<="140000"),(">14:00",lambda r:r["ft"]>"140000"),
              ("封单<0.5%",lambda r:r["seal"]<0.5),("0.5-2%",lambda r:0.5<=r["seal"]<2),(">=2%",lambda r:r["seal"]>=2),
              ("炸0",lambda r:r["zb"]==0),("炸>=1",lambda r:r["zb"]>=1),("炸>=3",lambda r:r["zb"]>=3),
              ("换手<3%",lambda r:r["to"]<3),("换手3-10%",lambda r:3<=r["to"]<=10),("换手>=10%",lambda r:r["to"]>10),
              ("首板",lambda r:r["lb"]==1),("2板+",lambda r:r["lb"]>=2)]:
    report(tag, [r for r in fixs if f(r)])

print("\n=== 全窗候选复合桶（可成交口径）===")
for tag,f in [("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),
              ("连板>=5×炸0",lambda r:r["lb"]>=5 and r["zb"]==0),
              ("连板>=4×炸>=2",lambda r:r["lb"]>=4 and r["zb"]>=2),
              ("连板>=4×炸0",lambda r:r["lb"]>=4 and r["zb"]==0),
              ("封单<0.1%×换手>=20%",lambda r:r["seal"]<0.1 and r["to"]>=20),
              ("封单<0.5%×换手>=20%",lambda r:r["seal"]<0.5 and r["to"]>=20),
              ("封单1-2%×炸0×换手5-15%",lambda r:1<=r["seal"]<2 and r["zb"]==0 and 5<=r["to"]<=15),
              ("尾盘>14×炸>=1",lambda r:r["ft"]>"140000" and r["zb"]>=1),
              ("尾盘>14×炸0",lambda r:r["ft"]>"140000" and r["zb"]==0),
              ("3板×炸0",lambda r:r["lb"]==3 and r["zb"]==0),
              ("3板×封单>=2%",lambda r:r["lb"]==3 and r["seal"]>=2),
              ("炸>=5×换手>=20%",lambda r:r["zb"]>=5 and r["to"]>=20)]:
    report(tag, sub(f))
