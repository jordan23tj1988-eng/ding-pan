# -*- coding: utf-8 -*-
"""席位强度双条件 + 转债换场 + 涨停票S/A覆盖 + A档可用率。"""
import json, os, csv
from collections import defaultdict
BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, "_学习"); DAY = "20261026"
tier = json.load(open(os.path.join(L, "_席位分档.json"), encoding="utf-8"))["席位"]
rows = list(csv.DictReader(open(os.path.join(L, "_席位动向", DAY + ".csv"), encoding="utf-8-sig")))
dual = json.load(open(os.path.join(L, "龙虎榜双源校验_" + DAY + ".json"), encoding="utf-8"))
lhb = list(csv.DictReader(open(os.path.join(BASE, DAY, "lhb.csv"), encoding="utf-8-sig")))
zt = list(csv.DictReader(open(os.path.join(BASE, DAY, "zt_pool.csv"), encoding="utf-8-sig")))
def is_interval(t): return any(k in t for k in ("连续", "累计", "区间", "严重异常"))
src1 = {r["代码"]: r for r in lhb if not is_interval(r["上榜原因"])}
bad = {}
for k in ("强矛盾清单", "分歧清单"):
    for x in dual[k]: bad[x["代码"]] = k

# 股票口径 dedup
best = {}
for r in rows:
    c = r["代码"]
    if c[:2] in ("11", "12", "90", "20", "13") or is_interval(r["类型"]): continue
    k = (c, r["席位"])
    if k not in best or float(r["买入金额"] or 0) > float(best[k]["买入金额"] or 0): best[k] = r
sa = []
for (c, s), r in best.items():
    t = tier.get(s, {})
    if t.get("档") in ("S", "A"):
        sa.append({"代码": c, "名": r["名称"], "席": s, "档": t["档"], "净万": float(r["净额"] or 0)/1e4,
                   "买万": float(r["买入金额"] or 0)/1e4, "样本": t.get("样本"),
                   "收缩": t.get("收缩执1胜率"), "均涨": t.get("收缩执1均涨"), "小": t.get("小样本")})
sa_pos = [x for x in sa if x["净万"] > 0]
print("S/A 席行=%d 净买>0=%d 净额合计=%.2f亿 单笔最大=%.0f万(%s %s) 单笔≥5000万笔数=%d" % (
    len(sa), len(sa_pos), sum(x["净万"] for x in sa_pos)/1e4,
    max(x["净万"] for x in sa), [x["名"] for x in sa if x["净万"] == max(y["净万"] for y in sa)][0],
    [x["席"] for x in sa if x["净万"] == max(y["净万"] for y in sa)][0],
    sum(1 for x in sa_pos if x["净万"] >= 5000)))
print("S/A 小样本席行=%d/%d" % (sum(1 for x in sa if x["小"]), len(sa)))

# 转债 S/A 换场
bond = [r for r in rows if r["代码"][:2] in ("11", "12")]
bnet = sum(float(r["净额"] or 0) for r in bond if tier.get(r["席位"], {}).get("档") in ("S", "A"))
tot = sum(x["净万"] for x in sa_pos)*1e4 + bnet
print("转债行=%d S/A转债净额=%.2f亿 S/A总净额=%.2f亿 转债占比=%.1f%%" % (
    len(bond), bnet/1e8, tot/1e8, 100*bnet/tot if tot else 0))

# A档可用率（库口径：A档净额中落 双源非强矛盾 ∧ 源1>0 的占比）
a_all = [r for (c, s), r in best.items() if tier.get(s, {}).get("档") == "A" and float(r["净额"] or 0) > 0]
ok = 0; tot_a = 0
for r in a_all:
    c = r["代码"]; n = float(r["净额"] or 0); tot_a += n
    s1 = src1.get(c)
    good = (c not in ("x",)) and (bad.get(c) != "强矛盾") and s1 is not None and float(s1["龙虎榜净买额"]) > 0
    if good: ok += n
print("A档可用率(净额加权)=%.1f%% (A档净买笔=%d)" % (100*ok/tot_a if tot_a else 0, len(a_all)))

# 涨停票的 S/A 覆盖
ztc = {r["代码"]: r for r in zt}
cover = []
for (c, s), r in best.items():
    t = tier.get(s, {})
    if t.get("档") in ("S", "A") and c in ztc:
        cover.append((c, r["名称"], t["档"], round(float(r["净额"] or 0)/1e4), t.get("样本"), t.get("小样本"),
                      ztc[c]["炸板次数"], ztc[c]["连板数"]))
print("\n涨停票中有S/A席的: %d 只" % len(set(x[0] for x in cover)))
for x in sorted(cover, key=lambda y: -y[3]): print(x)

json.dump({"SA行": len(sa), "SA净买行": len(sa_pos), "SA净额亿": round(sum(x["净万"] for x in sa_pos)/1e4, 2),
           "SA单笔最大万": round(max(x["净万"] for x in sa), 0), "SA小样本行": sum(1 for x in sa if x["小"]),
           "转债SA亿": round(bnet/1e8, 2), "转债占比pct": round(100*bnet/tot, 1) if tot else None,
           "A档可用率pct": round(100*ok/tot_a, 1) if tot_a else None,
           "涨停SA覆盖": cover},
          open(os.path.join(L, "_lhb_strength20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE")
