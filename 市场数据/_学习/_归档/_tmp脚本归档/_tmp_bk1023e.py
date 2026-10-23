# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
cold = [r for r in recs if r["temp"] < 25]
allm = sum(r["e1"] for r in cold)/len(cold)
tr = [r for r in cold if r["tradeable"]]
trm = sum(r["e1"] for r in tr)/len(tr)
print("精修剔除法(分板阈值): 冰点 n=%d 全池均%.3f%% | 可成交 n=%d 均%.3f%% 剔%.1f%%" % (len(cold), allm, len(tr), trm, 100*(1-len(tr)/len(cold))))
def cell(tag, f):
    a=[r for r in cold if f(r)]; b=[r for r in a if r["tradeable"]]
    if not a: print(tag,"empty"); return
    m=sum(r["e1"] for r in a)/len(a); mb=sum(r["e1"] for r in b)/len(b) if b else 0
    print("  %-24s 全池n=%3d 均%+.3f%% 超%+.3fpp | 剔%2d 可成交n=%3d 均%+.3f%% 超%+.3fpp 胜率%5.1f%%" % (
        tag,len(a),m,m-allm,len(a)-len(b),len(b),mb,mb-trm,100*sum(1 for r in b if r["e1"]>0)/len(b) if b else 0))
cell("①薄封<0.5%×换手3-10%", lambda r: r["seal"]<0.5 and 3<=r["to"]<=10)
cell("②强封>=4%×炸0", lambda r: r["seal"]>=4 and r["zb"]==0)
cell("③首封>14:30×首板", lambda r: r["ft"]>"143000" and r["lb"]==1)
print("\n不可成交构成: 一字%d 开盘即封%d" % (sum(1 for r in cold if r["yizi"]), sum(1 for r in cold if r["open_seal"])))

# 质量荐票结算
p = os.path.join(L,"质量荐票结算_20261023.json")
print("\n结算文件存在:", os.path.exists(p))
if os.path.exists(p):
    d=json.load(open(p, encoding="utf-8"))
    print(json.dumps(d, ensure_ascii=False)[:1500])
