# -*- coding: utf-8 -*-
"""今日漏斗：55 涨停 → 可荐。逐关卡数量与名单。"""
import json, os, csv
from collections import defaultdict
BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, "_学习"); DAY = "20261026"
tier = json.load(open(os.path.join(L, "_席位分档.json"), encoding="utf-8"))["席位"]
seat = json.load(open(os.path.join(L, "_lhb_seat20261026.json"), encoding="utf-8"))
rows = list(csv.DictReader(open(os.path.join(L, "_席位动向", DAY + ".csv"), encoding="utf-8-sig")))
dual = json.load(open(os.path.join(L, "龙虎榜双源校验_" + DAY + ".json"), encoding="utf-8"))
lhb = list(csv.DictReader(open(os.path.join(BASE, DAY, "lhb.csv"), encoding="utf-8-sig")))
zt = list(csv.DictReader(open(os.path.join(BASE, DAY, "zt_pool.csv"), encoding="utf-8-sig")))
def is_interval(t): return any(k in t for k in ("连续", "累计", "区间", "严重异常"))
src1 = {r["代码"]: r for r in lhb if not is_interval(r["上榜原因"])}
bad = {}
for k in ("强矛盾清单", "分歧清单"):
    for x in dual[k]: bad[x["代码"]] = k
best = {}
for r in rows:
    c = r["代码"]
    if c[:2] in ("11", "12", "90", "20", "13") or is_interval(r["类型"]): continue
    k = (c, r["席位"])
    if k not in best or float(r["买入金额"] or 0) > float(best[k]["买入金额"] or 0): best[k] = r
sa_by_code = defaultdict(list)
for (c, s), r in best.items():
    t = tier.get(s, {})
    if t.get("档") in ("S", "A"):
        sa_by_code[c].append({"档": t["档"], "净": float(r["净额"] or 0), "买": float(r["买入金额"] or 0),
                              "样本": t.get("样本"), "小": t.get("小样本"), "席": s})
ztc = {r["代码"]: r for r in zt}
print("涨停=%d 当日榜码=%d" % (len(zt), len(src1)))
s1 = [c for c in ztc if c in src1]; print("∩当日榜:", len(s1))
s2 = [c for c in s1 if float(src1[c]["龙虎榜净买额"]) > 0]; print("∩源1净买>0:", len(s2), "剔除", len(s1)-len(s2))
def three(c):
    z = ztc[c]; ent = float(z["成交额"] or 0); feng = float(z["封板资金"] or 0)
    if not ent: return False
    r = 100*feng/ent
    fz = 0 if z["炸板次数"] in ("", None) else int(z["炸板次数"])
    return r >= 5 and fz <= 3 and z["首次封板时间"] <= "140000"
s3 = [c for c in s2 if three(c)]; print("∩封板三项:", len(s3), s3)
s4 = [c for c in s3 if c in sa_by_code]; print("∩S/A在场:", len(s4), [(c, ztc[c]["名称"]) for c in s4])
s5 = [c for c in s4 if any(x["买"] >= 1e7 and x["净"] > 0 for x in sa_by_code[c])]; print("∩SA笔门槛:", len(s5), [(c, ztc[c]["名称"]) for c in s5])
s6 = [c for c in s5 if bad.get(c) != "强矛盾"]; print("∩非强矛盾:", len(s6))
s7 = [c for c in s6 if 0 < float(src1[c]["净买额占总成交比"]) <= 20]; print("∩净买占比≤20%:", len(s7), [(c, ztc[c]["名称"], round(float(src1[c]["净买额占总成交比"]),2)) for c in s7])
s8 = [c for c in s7 if float(src1[c]["龙虎榜净买额"]) - sum(x["净"] for x in sa_by_code[c]) < 1e8]; print("∩不打折过头(席-股票<1亿):", len(s8), [(c, ztc[c]["名称"]) for c in s8])
print("\n每关名单细表:")
for c in s2:
    z = ztc[c]; ent=float(z["成交额"] or 0); feng=float(z["封板资金"] or 0)
    print(c, z["名称"], "占比%.2f%%" % float(src1[c]["净买额占总成交比"]), "封单比%.2f%%" % (100*feng/ent if ent else 0),
          "炸%s" % z["炸板次数"], "首封%s" % z["首次封板时间"], "SA=%d" % len(sa_by_code.get(c, [])),
          "SA净万=%s" % ([round(x["净"]/1e4) for x in sa_by_code.get(c, [])]), "双源=%s" % bad.get(c, "一致"))
json.dump({"涨停": len(zt), "当日榜": len(s1), "源1正": len(s2), "三项": len(s3), "SA": len(s4),
           "SA笔门槛": len(s5), "非强矛盾": len(s6), "占比≤20": len(s7), "不打折过头": len(s8),
           "终选": [{"代码": c, "名称": ztc[c]["名称"]} for c in s8]},
          open(os.path.join(L, "_lhb_funnel20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
