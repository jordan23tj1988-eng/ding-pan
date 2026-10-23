# -*- coding: utf-8 -*-
import os, json, csv
L = r"D:/股票数据/市场数据/_学习"
B = r"D:/股票数据/市场数据"
recs = json.load(open(os.path.join(L, "_tmp_cold_recs.json"), encoding="utf-8"))
yi = [r for r in recs if r["yizi"]]
os_ = [r for r in recs if r["open_seal"] and not r["yizi"]]
print("一字 n=%d 均e1=%+.3f%% 胜率%.1f%%" % (len(yi), sum(r["e1"] for r in yi)/len(yi), 100*sum(1 for r in yi if r["e1"]>0)/len(yi)))
print("开盘即封(非一字) n=%d 均e1=%+.3f%% 胜率%.1f%%" % (len(os_), sum(r["e1"] for r in os_)/len(os_), 100*sum(1 for r in os_ if r["e1"]>0)/len(os_)))
print("一字里e1!=0的只数:", sum(1 for r in yi if abs(r["e1"])>1e-9))
# ② 桶内不可成交构成
a = [r for r in recs if r["seal"]>=4 and r["zb"]==0]
ex = [r for r in a if not r["tradeable"]]
print("\n②桶内不可成交 n=%d: 一字%d 开盘即封%d 均e1=%+.3f%%" % (len(ex), sum(1 for r in ex if r["yizi"]), sum(1 for r in ex if r["open_seal"] and not r["yizi"]), sum(r["e1"] for r in ex)/len(ex)))
a1 = [r for r in recs if r["seal"]<0.5 and 3<=r["to"]<=10]
print("①桶内不可成交明细:", [(r["d"],r["code"],r["name"],round(r["e1"],2)) for r in a1 if not r["tradeable"]])

# 今日池结构
rows = list(csv.DictReader(open(os.path.join(B,"20261023","zt_pool.csv"), encoding="utf-8-sig")))
def f(r,k): return float(r[k])
seals = sorted(f(r,"封板资金")/f(r,"流通市值")*100 for r in rows)
tos = sorted(f(r,"换手率") for r in rows)
print("\n=== 今日82只结构 ===")
print("封单比 中位%.3f%% 最小%.3f%% 最大%.3f%% | <0.5%%: %d | ≥4%%: %d" % (seals[len(seals)//2], seals[0], seals[-1],
      sum(1 for s in seals if s<0.5), sum(1 for s in seals if s>=4)))
print("换手 中位%.2f%% | <3%%: %d | 3-10%%: %d | 10-20%%: %d | ≥20%%: %d" % (tos[len(tos)//2],
      sum(1 for t in tos if t<3), sum(1 for t in tos if 3<=t<=10), sum(1 for t in tos if 10<t<=20), sum(1 for t in tos if t>20)))
from collections import Counter
zb = Counter(int(float(r["炸板次数"])) for r in rows)
lb = Counter(int(float(r["连板数"])) for r in rows)
ft = Counter()
for r in rows:
    t = str(r["首次封板时间"]).zfill(6)
    if t <= "092500": ft["≤09:25"] += 1
    elif t <= "093100": ft["09:26-09:31"] += 1
    elif t <= "100000": ft["09:32-10:00"] += 1
    elif t <= "130000": ft["10:01-13:00"] += 1
    elif t <= "140000": ft["13:01-14:00"] += 1
    elif t <= "143000": ft["14:01-14:30"] += 1
    else: ft[">14:30"] += 1
print("炸板分布", dict(zb), "| 连板分布", dict(sorted(lb.items())), "| 首封", dict(ft))
print("成交额均值%.2f亿" % (sum(f(r,"成交额") for r in rows)/len(rows)/1e8))
print("今日封单额合计 %.2f亿" % (sum(f(r,"封板资金") for r in rows)/1e8))
