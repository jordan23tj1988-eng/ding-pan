# -*- coding: utf-8 -*-
"""第二刀:今日(20261023)池结构对应的桶值 —— V型修复日 / 未炸 / 封单比档 / 一字 / 连板"""
import os, json
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
S = json.load(open(B + "/_tmp/auction_samples_1023.json", encoding="utf-8"))
wdt = json.load(open(L + "/_市场温度表.json", encoding="utf-8"))
days = sorted(wdt.keys())
prev = {d: days[i - 1] for i, d in enumerate(days) if i}
wmap = {d: (wdt.get(d) or {}).get("温度") for d in days}


def vrev(x):
    p = prev.get(x["日"])
    return bool(p) and (wmap.get(p) or 99) < 25 and (x["温度"] or 0) >= 45


def agg(s, tag):
    if not s: print(f"{tag:42s} n=0"); return
    ex = [x["执行"] for x in s]
    cb = [x for x in s if not (x["剔1"] or x["剔2"])]
    exc = [x["执行"] for x in cb]
    print(f"{tag:42s} n={len(s):4d} {sum(1 for e in ex if e>0)/len(ex)*100:5.1f}% /{sum(ex)/len(ex):+6.2f}%  封{sum(1 for x in s if x['次日封板'])/len(s)*100:5.1f}%"
          f" | 可成交 n={len(cb):4d} {sum(1 for e in exc if e>0)/max(len(exc),1)*100:5.1f}% /{(sum(exc)/len(exc) if exc else 0):+6.2f}%")


def fdb(x, lo, hi): return x["封单比"] is not None and lo <= x["封单比"] < hi


print("== V型修复日(前日<25,当日>=45) 细分 ==")
v = [x for x in S if vrev(x)]
agg(v, "V型日 全档")
agg([x for x in v if x["信号"] == "一字"], "└ 一字")
agg([x for x in v if x["信号"] == "秒板"], "└ 秒板")
agg([x for x in v if x["炸板"] == 0], "└ 未炸(炸0)")
agg([x for x in v if x["炸板"] >= 1], "└ 炸1+")
agg([x for x in v if x["连板"] == 1], "└ 首板")
agg([x for x in v if x["连板"] >= 2], "└ 2板+")
agg([x for x in v if fdb(x, 0, 0.5)], "└ 封单比<0.5%")
agg([x for x in v if fdb(x, 0.5, 1.5)], "└ 封单比0.5~1.5%")
agg([x for x in v if fdb(x, 1.5, 4)], "└ 封单比1.5~4%")
agg([x for x in v if fdb(x, 4, 999)], "└ 封单比>=4%")
agg([x for x in v if x["T1高开"] <= 0], "└ 低开<=0")
agg([x for x in v if 0 < x["T1高开"] < 5], "└ 高开0~5")
agg([x for x in v if x["T1高开"] >= 5], "└ 高开>=5")

print("\n== 交叉 V型日 × 封单比档 × 高开档 ==")
for lo, hi, nm in [(0, 0.5, "<0.5%"), (0.5, 1.5, "0.5~1.5%"), (1.5, 4, "1.5~4%"), (4, 999, ">=4%")]:
    sub = [x for x in v if fdb(x, lo, hi)]
    agg(sub, f"V|封单{nm}")
    for g, gn in [(-99, "低开≤0"), (0, "0~5"), (5, "≥5")]:
        if gn == "低开≤0": s2 = [x for x in sub if x["T1高开"] <= 0]
        elif gn == "0~5": s2 = [x for x in sub if 0 < x["T1高开"] < 5]
        else: s2 = [x for x in sub if x["T1高开"] >= 5]
        agg(s2, f"   └ {gn}")

print("\n== 交叉 V型日 × 未炸/炸1+ × 高开档 ==")
for nm, cond in [("未炸", lambda x: x["炸板"] == 0), ("炸1+", lambda x: x["炸板"] >= 1)]:
    sub = [x for x in v if cond(x)]
    agg(sub, f"V|{nm}")
    agg([x for x in sub if x["T1高开"] <= 0], f"   └ 低开≤0")
    agg([x for x in sub if 0 < x["T1高开"] < 5], f"   └ 0~5")
    agg([x for x in sub if x["T1高开"] >= 5], f"   └ ≥5")

print("\n== 一字票次日高开分布(闸门弃单概率) ==")
yz = [x for x in S if x["信号"] == "一字"]
n = len(yz); hi = sum(1 for x in yz if x["T1高开"] >= 5)
print(f"一字 n={n} 次日≥5% {hi} = {hi/n*100:.1f}%  0~5 {sum(1 for x in yz if 0<x['T1高开']<5)/n*100:.1f}%  低开 {sum(1 for x in yz if x['T1高开']<=0)/n*100:.1f}%")
mz = [x for x in S if x["信号"] == "秒板"]
n2 = len(mz); hi2 = sum(1 for x in mz if x["T1高开"] >= 5)
print(f"秒板 n={n2} 次日≥5% {hi2} = {hi2/n2*100:.1f}%")
print("\n== 今日池 7 只逐票的桶归属自检 ==")
for x in sorted(v, key=lambda y: y["日"]):
    pass
