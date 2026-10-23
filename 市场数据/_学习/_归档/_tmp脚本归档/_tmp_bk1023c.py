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
neu = [r for r in recs if 45 <= r["temp"] < 65]
nb = sum(r["e1"] for r in neu if r["tradeable"])/sum(1 for r in neu if r["tradeable"])
allb = sum(r["e1"] for r in recs if r["tradeable"])/sum(1 for r in recs if r["tradeable"])

def rep(tag, rs, b):
    tr = [r for r in rs if r["tradeable"]]
    if not tr: print("  %-34s n=%d 全不可成交" % (tag, len(rs))); return
    m = sum(r["e1"] for r in tr)/len(tr); w = 100*sum(1 for r in tr if r["e1"]>0)/len(tr)
    sr = 100*sum(r["seal_next"] for r in rs)/len(rs)
    print("  %-34s 全池n=%3d 剔%2d 可成交n=%3d 均%+.2f%% 超额%+.2fpp 胜率%5.1f%% 次日封板%5.1f%%" % (tag, len(rs), len(rs)-len(tr), len(tr), m, m-b, w, sr))

print("中性基线 %.3f%%  全窗基线 %.3f%%" % (nb, allb))
print("\n=== 中性环境 候选复合桶 ===")
for tag,f in [("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),
              ("连板>=5×炸0",lambda r:r["lb"]>=5 and r["zb"]==0),
              ("连板>=4×炸>=2",lambda r:r["lb"]>=4 and r["zb"]>=2),
              ("炸>=5×换手>=20%",lambda r:r["zb"]>=5 and r["to"]>=20),
              ("炸>=5×换手10-20%",lambda r:r["zb"]>=5 and 10<=r["to"]<20),
              ("炸>=5×封单<1%",lambda r:r["zb"]>=5 and r["seal"]<1),
              ("炸>=5×封单>=1%",lambda r:r["zb"]>=5 and r["seal"]>=1),
              ("换手>=20%×首封<=10:00",lambda r:r["to"]>=20 and r["ft"]<="100000"),
              ("换手>=20%×炸>=3",lambda r:r["to"]>=20 and r["zb"]>=3),
              ("2板×炸>=5",lambda r:r["lb"]==2 and r["zb"]>=5),
              ("炸>=5×首封10-14",lambda r:r["zb"]>=5 and "100000"<r["ft"]<="140000"),
              ("封单0.5-2%×炸>=5",lambda r:0.5<=r["seal"]<2 and r["zb"]>=5),
              ("首封14-14:30×炸>=1",lambda r:"140000"<r["ft"]<="143000" and r["zb"]>=1),
              ("20cm×换手>=20%",lambda r:r["lp"]==20 and r["to"]>=20)]:
    rep(tag, [r for r in neu if f(r)], nb)
print("\n=== 同桶全窗 ===")
for tag,f in [("连板>=5×炸>=2",lambda r:r["lb"]>=5 and r["zb"]>=2),
              ("炸>=5×换手>=20%",lambda r:r["zb"]>=5 and r["to"]>=20),
              ("炸>=5×换手10-20%",lambda r:r["zb"]>=5 and 10<=r["to"]<20),
              ("炸>=5×封单<1%",lambda r:r["zb"]>=5 and r["seal"]<1),
              ("2板×炸>=5",lambda r:r["lb"]==2 and r["zb"]>=5),
              ("20cm×换手>=20%",lambda r:r["lp"]==20 and r["to"]>=20)]:
    rep(tag, [r for r in recs if f(r)], allb)
