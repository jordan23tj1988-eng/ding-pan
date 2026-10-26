# -*- coding: utf-8 -*-
"""今日候选全景：席位数 + 源1净买/净买占比 + 双源判定 + zt_pool 封板读数。"""
import json, os, csv
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_学习")
DAY = "20261026"

seat = json.load(open(os.path.join(L, "_lhb_seat20261026.json"), encoding="utf-8"))
dual = json.load(open(os.path.join(L, "龙虎榜双源校验_" + DAY + ".json"), encoding="utf-8"))
zt = list(csv.DictReader(open(os.path.join(os.path.dirname(L), DAY, "zt_pool.csv"), encoding="utf-8-sig")))
lhb = list(csv.DictReader(open(os.path.join(os.path.dirname(L), DAY, "lhb.csv"), encoding="utf-8-sig")))
print("lhb字段:", list(lhb[0].keys()))

def is_interval(t):
    return ("连续" in t) or ("累计" in t) or ("严重异常" in t) or ("区间" in t)

# 源1 当日榜 股票级净买
src1 = {}
for r in lhb:
    if is_interval(r.get("上榜原因", "") or ""):
        print("INTERVAL ROW?", r.get("代码"), r.get("上榜原因"))
    src1[r["代码"]] = r

status = {}
for k in ("强矛盾清单", "分歧清单", "打折清单"):
    for x in dual[k]:
        status[x["代码"]] = (k, x["源1净买亿"], x["源2买侧净额亿"])

ztmap = {r["代码"]: r for r in zt}

codes = [c["代码"] for c in seat["候选"]] + ["002696", "301428", "000810", "600558", "600178", "003021"]
codes = list(dict.fromkeys(codes))
out = []
for c in codes:
    p = seat["个股"].get(c, {})
    s1 = src1.get(c)
    z = ztmap.get(c)
    row = {"代码": c, "名称": p.get("名") or (s1 or {}).get("名称"),
           "席位净万": p.get("净万"), "S": p.get("S"), "A": p.get("A"), "非小SA": p.get("非小SA"),
           "机构净万": p.get("机构净万"), "北向净万": p.get("北向净万"),
           "源1净买亿": round(float(s1["净买额"])/1e8, 4) if s1 and s1.get("净买额") else None,
           "源1占成交pct": round(float(s1["净买额占成交"])*100, 2) if s1 and s1.get("净买额占成交") else None,
           "上榜原因": s1.get("上榜原因") if s1 else None,
           "双源": (status.get(c)[0] if c in status else "一致/未列"),
           "zt": None}
    if z:
        ent = float(z["成交额"] or 0); feng = float(z["封板资金"] or 0)
        row["zt"] = {"涨跌幅": round(float(z["涨跌幅"]), 2), "连板数": z["连板数"],
                     "炸板次数": z["炸板次数"], "首封": z["首次封板时间"], "末封": z["最后封板时间"],
                     "封单比_成交": round(100*feng/ent, 2) if ent else None,
                     "换手": round(float(z["换手率"]), 2), "流通亿": round(float(z["流通市值"])/1e8, 2),
                     "行业": z["所属行业"], "封单万": round(feng/1e4)}
    out.append(row)
    print(json.dumps(row, ensure_ascii=False))

json.dump(out, open(os.path.join(L, "_lhb_cand20261026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE _lhb_cand20261026.json")
