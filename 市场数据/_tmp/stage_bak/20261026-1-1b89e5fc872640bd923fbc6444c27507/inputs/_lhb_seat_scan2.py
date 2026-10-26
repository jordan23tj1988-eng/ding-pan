# -*- coding: utf-8 -*-
"""席位路 20261026 定量底稿 v2：股票口径(剔区间榜/按(代码,席位)去重/剔债与退/N) + S/A候选复算。"""
import json, os, csv
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
DAY = "20261026"

tier = json.load(open(os.path.join(L, "_席位分档.json"), encoding="utf-8"))["席位"]
rows = list(csv.DictReader(open(os.path.join(L, "_席位动向", DAY + ".csv"), encoding="utf-8-sig")))

def bad_code(c):
    return c[:2] in ("11", "12", "90", "20", "13")

def is_interval(t):
    return ("连续" in t) or ("累计" in t) or ("严重异常" in t) or ("区间" in t)

best = {}
for r in rows:
    c = r["代码"]
    if bad_code(c) or is_interval(r["类型"]):
        continue
    key = (c, r["席位"])
    buy = float(r["买入金额"] or 0)
    if key not in best or buy > float(best[key]["买入金额"] or 0):
        best[key] = r

recs = []
for (c, seat), r in best.items():
    t = tier.get(seat, {})
    recs.append({"代码": c, "名称": r["名称"], "席位": seat,
                 "买": float(r["买入金额"] or 0), "净": float(r["净额"] or 0),
                 "档": t.get("档"), "样本": t.get("样本"), "小样本": t.get("小样本"),
                 "收缩胜率": t.get("收缩执1胜率"), "收缩均涨": t.get("收缩执1均涨"),
                 "通道": t.get("通道")})
print("去重后席位笔:", len(best), " 代码数:", len(set(x["代码"] for x in recs)))

笔 = [x for x in recs if x["净"] > 0 and x["买"] >= 1e7]
sa = [x for x in 笔 if x["档"] in ("S", "A")]
allbuy = sum(x["买"] for x in 笔)
print("笔=%d 全榜买额=%.2f亿 SA笔=%d SA占比=%.2f%% SA买额=%.2f亿(%.2f%% of 全榜) SA净额=%.2f亿" % (
    len(笔), allbuy/1e8, len(sa), 100.*len(sa)/len(笔), sum(x["买"] for x in sa)/1e8,
    100.*sum(x["买"] for x in sa)/allbuy if allbuy else 0, sum(x["净"] for x in sa)/1e8))
print("S档笔=%d A档笔=%d" % (sum(1 for x in sa if x["档"] == "S"), sum(1 for x in sa if x["档"] == "A")))
print("SA小样本笔=%d / %d" % (sum(1 for x in sa if x["小样本"]), len(sa)))

def style(n):
    if "机构专用" in n: return "机构"
    if "股通" in n: return "北向"
    if "总部" in n or "分公司" in n: return "总部/分公司"
    return "营业部"
sty = defaultdict(lambda: [0, 0.0, 0.0])
for x in recs:
    s = style(x["席位"])
    sty[s][0] += 1; sty[s][1] += x["买"]; sty[s][2] += x["净"]
print("\n== 风格(去重后, 万元) ==")
for k, v in sorted(sty.items(), key=lambda x: -abs(x[1][2])):
    print("%s 行=%d 买=%.0f 净=%.0f" % (k, v[0], v[1]/1e4, v[2]/1e4))

per = defaultdict(lambda: {"名": "", "买": 0.0, "净": 0.0, "S": [], "A": [], "机构": 0.0, "北向": 0.0})
for x in recs:
    p = per[x["代码"]]
    p["名"] = x["名称"]; p["买"] += x["买"]; p["净"] += x["净"]
    if x["档"] in ("S", "A"): p[x["档"]].append(x)
    if style(x["席位"]) == "机构": p["机构"] += x["净"]
    if style(x["席位"]) == "北向": p["北向"] += x["净"]

print("\n== 个股 S/A 在场（净额降序前12） ==")
for c, p in sorted(per.items(), key=lambda x: -x[1]["净"])[:12]:
    print(c, p["名"], "净=%.0f万 买=%.0f万 S=%d A=%d 非小SA=%d 机构=%.0f 北向=%.0f" % (
        p["净"]/1e4, p["买"]/1e4, len(p["S"]), len(p["A"]),
        sum(1 for x in p["S"]+p["A"] if not x["小样本"]), p["机构"]/1e4, p["北向"]/1e4))

cand = []
for c, p in per.items():
    if not (p["S"] or p["A"]): continue
    if p["净"] <= 0: continue
    strong = [x for x in p["S"] + p["A"] if x["净"] >= 1e7]
    if not strong: continue
    key = lambda x: (x["档"] == "S", x["净"])
    top = max(strong, key=key)
    cand.append({"代码": c, "名称": p["名"], "股票净额万": round(p["净"]/1e4),
                 "SA净买≥1000万席数": len(strong),
                 "非小样本SA席": sum(1 for x in strong if not x["小样本"]),
                 "最强席": top["席位"], "最强档": top["档"], "最强席收缩胜率": top["收缩胜率"],
                 "最强席均涨": top["收缩均涨"], "最强席样本": top["样本"], "最强席小样本": top["小样本"],
                 "席位": [{"席": x["席位"], "档": x["档"], "净万": round(x["净"]/1e4), "样本": x["样本"],
                           "收缩胜率": x["收缩胜率"], "收缩均涨": x["收缩均涨"], "小样本": x["小样本"]} for x in strong]})
cand.sort(key=lambda x: -x["股票净额万"])
print("\n== S/A候选（净额降序） n=%d ==" % len(cand))
for x in cand:
    print(x["代码"], x["名称"], x["股票净额万"], "席数%d 非小%d" % (x["SA净买≥1000万席数"], x["非小样本SA席"]),
          x["最强档"], x["最强席收缩胜率"], "n=%s" % x["最强席样本"])

json.dump({"日期": DAY, "笔": len(笔), "全榜买额亿": round(allbuy/1e8, 2), "SA笔": len(sa),
           "SA占比pct": round(100.*len(sa)/len(笔), 2), "SA买额亿": round(sum(x["买"] for x in sa)/1e8, 2),
           "SA净额亿": round(sum(x["净"] for x in sa)/1e8, 2),
           "风格": {k: {"行": v[0], "买万": round(v[1]/1e4), "净万": round(v[2]/1e4)} for k, v in sty.items()},
           "个股": {c: {"名": p["名"], "买万": round(p["买"]/1e4), "净万": round(p["净"]/1e4),
                        "S": len(p["S"]), "A": len(p["A"]),
                        "非小SA": sum(1 for x in p["S"]+p["A"] if not x["小样本"]),
                        "机构净万": round(p["机构"]/1e4), "北向净万": round(p["北向"]/1e4)} for c, p in per.items()},
           "候选": cand},
          open(os.path.join(L, "_lhb_seat20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nWROTE _lhb_seat20261026.json")
