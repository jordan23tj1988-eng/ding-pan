# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
env = json.load(open(os.path.join(L,"_tmp_env.json"), encoding="utf-8"))
fix = set(env["fix"])
inpool = {(r["d"], r["code"]) for r in recs}
dl = sorted(set(r["d"] for r in recs))
nxt = {d: dl[i+1] for i,d in enumerate(dl[:-1])}
for r in recs:
    nd = nxt.get(r["d"]); r["seal_next"] = 1 if nd and (nd, r["code"]) in inpool else 0

def base(pred):
    tr = [r for r in recs if pred(r) and r["tradeable"]]
    return sum(r["e1"] for r in tr)/len(tr), len(tr)

NEU = (lambda r: 45 <= r["temp"] < 65)
FIX = (lambda r: r["d"] in fix)
neu_b, neu_n = base(NEU); fix_b, fix_n = base(FIX)
print("中性可成交基线 %.3f%% (n=%d) | 修复日可成交基线 %.3f%% (n=%d)" % (neu_b, neu_n, fix_b, fix_n))

def rep(tag, rs, b):
    if not rs: print("  %-26s EMPTY" % tag); return
    tr = [r for r in rs if r["tradeable"]]
    if not tr: print("  %-26s 全池n=%d 全不可成交" % (tag, len(rs))); return
    m = sum(r["e1"] for r in tr)/len(tr)
    w = 100*sum(1 for r in tr if r["e1"]>0)/len(tr)
    sr = 100*sum(r["seal_next"] for r in rs)/len(rs)
    print("  %-26s 全池n=%4d 剔%2d 可成交n=%4d 均%+.2f%% 超额%+.2fpp 胜率%5.1f%% 次日封板%5.1f%%" %
          (tag, len(rs), len(rs)-len(tr), len(tr), m, m-b, w, sr))

neu = [r for r in recs if NEU(r)]; fixr = [r for r in recs if FIX(r)]
print("\n=== 中性(45-65) ===")
for tag,f in [("首封<=09:25",lambda r:r["ft"]<="092500"),("09:26-09:31",lambda r:"092500"<r["ft"]<="093100"),
              ("09:32-10:00",lambda r:"093100"<r["ft"]<="100000"),("10:01-13:00",lambda r:"100000"<r["ft"]<="130000"),
              ("13:01-14:00",lambda r:"130000"<r["ft"]<="140000"),("14:01-14:30",lambda r:"140000"<r["ft"]<="143000"),
              (">14:30",lambda r:r["ft"]>"143000"),
              ("封单<0.5%",lambda r:r["seal"]<0.5),("0.5-1%",lambda r:0.5<=r["seal"]<1),("1-2%",lambda r:1<=r["seal"]<2),
              ("2-4%",lambda r:2<=r["seal"]<4),(">=4%",lambda r:r["seal"]>=4),
              ("炸0",lambda r:r["zb"]==0),("炸1",lambda r:r["zb"]==1),("炸2-4",lambda r:2<=r["zb"]<=4),("炸>=5",lambda r:r["zb"]>=5),
              ("换手<3%",lambda r:r["to"]<3),("换手3-10%",lambda r:3<=r["to"]<=10),("换手10-20%",lambda r:10<r["to"]<=20),("换手>=20%",lambda r:r["to"]>20),
              ("首板",lambda r:r["lb"]==1),("2板",lambda r:r["lb"]==2),("3板",lambda r:r["lb"]==3),("4板+",lambda r:r["lb"]>=4)]:
    rep(tag, [r for r in neu if f(r)], neu_b)

print("\n=== 修复日 ===")
for tag,f in [("首封<=10:00",lambda r:r["ft"]<="100000"),("10:01-14:00",lambda r:"100000"<r["ft"]<="140000"),(">14:00",lambda r:r["ft"]>"140000"),
              ("封单<0.5%",lambda r:r["seal"]<0.5),("0.5-2%",lambda r:0.5<=r["seal"]<2),(">=2%",lambda r:r["seal"]>=2),
              ("炸0",lambda r:r["zb"]==0),("炸>=3",lambda r:r["zb"]>=3),
              ("换手<3%",lambda r:r["to"]<3),("换手3-10%",lambda r:3<=r["to"]<=10),("换手>=10%",lambda r:r["to"]>10),
              ("首板",lambda r:r["lb"]==1),("2板+",lambda r:r["lb"]>=2)]:
    rep(tag, [r for r in fixr if f(r)], fix_b)

print("\n=== 全窗复合桶（超额 vs 全窗可成交基线）===")
alltr = [r for r in recs if r["tradeable"]]
all_b = sum(r["e1"] for r in alltr)/len(alltr)
print("全窗可成交基线 %.3f%% n=%d" % (all_b, len(alltr)))
for tag,f in [("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),
              ("连板>=5×炸0",lambda r:r["lb"]>=5 and r["zb"]==0),
              ("连板>=4×炸>=2",lambda r:r["lb"]>=4 and r["zb"]>=2),
              ("连板>=4×炸0",lambda r:r["lb"]>=4 and r["zb"]==0),
              ("封单<0.5%×换手>=20%",lambda r:r["seal"]<0.5 and r["to"]>=20),
              ("封单<0.1%×换手>=20%",lambda r:r["seal"]<0.1 and r["to"]>=20),
              ("封单1-2%×炸0×换手5-15%",lambda r:1<=r["seal"]<2 and r["zb"]==0 and 5<=r["to"]<=15),
              ("尾盘>14×炸>=1",lambda r:r["ft"]>"140000" and r["zb"]>=1),
              ("尾盘>14×炸0",lambda r:r["ft"]>"140000" and r["zb"]==0),
              ("3板×炸0",lambda r:r["lb"]==3 and r["zb"]==0),
              ("3板×封单>=2%",lambda r:r["lb"]==3 and r["seal"]>=2),
              ("连板>=5×炸>=2×换手>=20%",lambda r:r["lb"]>=5 and r["zb"]>=2 and r["to"]>=20)]:
    rep(tag, [r for r in recs if f(r)], all_b)
