# -*- coding: utf-8 -*-
"""今日候选全景 v2：源1只取当日榜行(剔连续/累计/区间/严重异常) + 双源 + zt_pool。"""
import json, os, csv
BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
DAY = "20261026"
seat = json.load(open(os.path.join(L, "_lhb_seat20261026.json"), encoding="utf-8"))
dual = json.load(open(os.path.join(L, "龙虎榜双源校验_" + DAY + ".json"), encoding="utf-8"))
zt = list(csv.DictReader(open(os.path.join(BASE, DAY, "zt_pool.csv"), encoding="utf-8-sig")))
lhb = list(csv.DictReader(open(os.path.join(BASE, DAY, "lhb.csv"), encoding="utf-8-sig")))

def is_interval(t): return any(k in t for k in ("连续", "累计", "区间", "严重异常"))
src1, onlyint = {}, set()
for r in lhb:
    if is_interval(r["上榜原因"]):
        onlyint.add(r["代码"]); continue
    src1[r["代码"]] = r
status = {}
for k in ("强矛盾清单", "分歧清单", "打折清单"):
    for x in dual[k]: status[x["代码"]] = (k, x["源1净买亿"], x["源2买侧净额亿"])
ztmap = {r["代码"]: r for r in zt}

codes = list(dict.fromkeys([c["代码"] for c in seat["候选"]] + ["002696","301428","000810","600558","600178","603186","000559"]))
out = []
for c in codes:
    p = seat["个股"].get(c, {}); s1 = src1.get(c); z = ztmap.get(c)
    row = {"代码": c, "名称": p.get("名") or (s1 or z or {}).get("名称"),
           "席位净万": p.get("净万"), "S": p.get("S"), "A": p.get("A"), "非小SA": p.get("非小SA"),
           "机构净万": p.get("机构净万"), "北向净万": p.get("北向净万"),
           "源1净买亿": round(float(s1["龙虎榜净买额"])/1e8, 4) if s1 else None,
           "源1净买占成交pct": round(float(s1["净买额占总成交比"]), 2) if s1 else None,
           "源1解读": s1["解读"] if s1 else None,
           "仅区间榜": c in onlyint and c not in src1,
           "上榜原因": (s1 or {}).get("上榜原因") or ("仅区间榜" if c in onlyint else None),
           "双源": status.get(c, ("一致/未列", None, None))[0],
           "源2买侧亿": status.get(c, (None, None, None))[2],
           "zt": None}
    if z:
        ent = float(z["成交额"] or 0); feng = float(z["封板资金"] or 0)
        row["zt"] = {"涨跌幅": round(float(z["涨跌幅"]), 2), "连板": z["连板数"], "炸": z["炸板次数"],
                     "首封": z["首次封板时间"], "末封": z["最后封板时间"],
                     "封单比成交pct": round(100*feng/ent, 2) if ent else None,
                     "封单比流通pct": round(100*feng/float(z["流通市值"]), 2) if z["流通市值"] else None,
                     "换手": round(float(z["换手率"]), 2), "流通亿": round(float(z["流通市值"])/1e8, 2),
                     "行业": z["所属行业"]}
    out.append(row); print(json.dumps(row, ensure_ascii=False))

json.dump(out, open(os.path.join(L, "_lhb_cand20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE; 当日榜代码数=%d 仅区间榜=%d" % (len(src1), len(onlyint)))
