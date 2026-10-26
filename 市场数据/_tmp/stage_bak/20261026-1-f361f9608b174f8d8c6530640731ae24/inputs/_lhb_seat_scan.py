# -*- coding: utf-8 -*-
"""席位路 20261026 定量底稿：席位档聚合 + 个股级 S/A 在场 + 风格构成。"""
import json, os, csv
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")

tier = json.load(open(os.path.join(L, "_席位分档.json"), encoding="utf-8"))
tiers = tier["席位"]

rows = list(csv.DictReader(open(os.path.join(L, "_席位动向", "20261026.csv"), encoding="utf-8-sig")))
print("席位明细行:", len(rows), " 代码数:", len(set(r["代码"] for r in rows)))

for r in rows:
    r["净额"] = float(r["净额"] or 0)
    r["买入"] = float(r["买入金额"] or 0)
    t = tiers.get(r["席位"], {})
    r["档"] = t.get("档")
    r["样本"] = t.get("样本")
    r["收缩胜率"] = t.get("收缩执1胜率")
    r["收缩均涨"] = t.get("收缩执1均涨")
    r["小样本"] = t.get("小样本")
    r["通道"] = t.get("通道")

known = [r for r in rows if r["档"]]
print("可分档席位行:", len(known), " 未入档(新席/未知):", len(rows) - len(known))

# 档级聚合
agg = defaultdict(lambda: {"行": 0, "买": 0.0, "卖": 0.0, "净": 0.0})
for r in rows:
    k = r["档"] or "未入档"
    agg[k]["行"] += 1
    agg[k]["买"] += r["买入"]
    agg[k]["卖"] += r["买入"] - r["净额"]
    agg[k]["净"] += r["净额"]
print("\n== 档级聚合(万元) ==")
for k in ["S", "A", "B", "C", "P", "未入档"]:
    if k in agg:
        a = agg[k]
        print(k, "行=%d 买=%.0f 净=%.0f" % (a["行"], a["买"]/1e4, a["净"]/1e4))

# 通道/风格
def style(name):
    if "机构专用" in name: return "机构"
    if "股通" in name: return "北向"
    if "总部" in name or "分公司" in name: return "总部/分公司"
    return "营业部"
sty = defaultdict(lambda: {"行": 0, "净": 0.0, "买": 0.0})
for r in rows:
    s = style(r["席位"])
    sty[s]["行"] += 1; sty[s]["净"] += r["净额"]; sty[s]["买"] += r["买入"]
print("\n== 风格聚合(万元) ==")
for k, v in sorted(sty.items(), key=lambda x: -abs(x[1]["净"])):
    print(k, "行=%d 买=%.0f 净=%.0f" % (v["行"], v["买"]/1e4, v["净"]/1e4))

# 个股级
per = defaultdict(lambda: {"名": "", "净": 0.0, "买": 0.0, "S": 0, "A": 0, "S非小": 0, "A非小": 0,
                           "机构": 0, "北向": 0, "席": [], "max档": None})
order = {"S": 0, "A": 1, "B": 2, "C": 3, "P": 4}
for r in rows:
    p = per[r["代码"]]
    p["名"] = r["名称"]; p["净"] += r["净额"]; p["买"] += r["买入"]
    t = r["档"]
    if t in ("S", "A"):
        p[t] += 1
        if not r["小样本"]: p[t + "非小"] += 1
    if style(r["席位"]) == "机构": p["机构"] += r["净额"]
    if style(r["席位"]) == "北向": p["北向"] += r["净额"]
    p["席"].append({"名": r["席位"], "档": t, "净万": round(r["净额"]/1e4, 0),
                    "样本": r["样本"], "收缩胜率": r["收缩胜率"], "收缩均涨": r["收缩均涨"], "小样本": r["小样本"]})
    if t and (p["max档"] is None or order[t] < order[p["max档"]]): p["max档"] = t

print("\n== 个股级 S/A 在场(按净额降序, 前15) ==")
for code, p in sorted(per.items(), key=lambda x: -x[1]["净"])[:15]:
    print(code, p["名"], "净=%.0f万" % (p["净"]/1e4), "S=%d A=%d 非小S=%d 非小A=%d" % (p["S"], p["A"], p["S非小"], p["A非小"]),
          "机构=%.0f 北向=%.0f" % (p["机构"]/1e4, p["北向"]/1e4), "max=", p["max档"], "席位n=", len(p["席"]))
print("\n== 个股级 净卖前8 ==")
for code, p in sorted(per.items(), key=lambda x: x[1]["净"])[:8]:
    print(code, p["名"], "净=%.0f万" % (p["净"]/1e4), "S=%d A=%d" % (p["S"], p["A"]), "max=", p["max档"], "席位n=", len(p["席"]))

out = {"日期": "20261026", "行数": len(rows), "可分档行": len(known),
       "档级": {k: {"行": v["行"], "买万": round(v["买"]/1e4), "净万": round(v["净"]/1e4)} for k, v in agg.items()},
       "风格": {k: {"行": v["行"], "净万": round(v["净"]/1e4)} for k, v in sty.items()},
       "个股": {c: {k: (round(v, 0) if isinstance(v, float) else v) for k, v in p.items() if k != "席"}
                for c, p in per.items()},
       "个股席位": {c: p["席"] for c, p in per.items()}}
json.dump(out, open(os.path.join(L, "_lhb_seat20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nWROTE _lhb_seat20261026.json")
