# -*- coding: utf-8 -*-
"""hb-b 20260923 高标/炸板/趋势确认段 专项扫描 (锁定窗 <=10:30:00)"""
import json, csv, collections, statistics

d = "20260923"
base = "盘中/%s" % d
ls = [json.loads(l) for l in open(base + "/realtime_ticks.jsonl", encoding="utf-8")]
lk = [r for r in ls if r["ts"] <= "2026-09-23 10:30:00"]

ind = {}
for row in csv.DictReader(open("20260922/zt_pool.csv", encoding="utf-8-sig")):
    ind[row["代码"]] = dict(name=row["名称"], ind=row["所属行业"], lb=row["连板数"],
                            zt=row["涨停统计"], close=float(row["最新价"]), zb=row["炸板次数"],
                            seal=row["封板资金"])

ser = collections.defaultdict(dict)   # code -> ts -> row
tsl = [t["ts"] for t in lk]
for t in lk:
    for r in t["rows"]:
        ser[r["code"]][t["ts"]] = r

def at(c, ts):
    return ser.get(c, {}).get(ts)

# 时点采样
keyts = [tsl[0], "2026-09-23 09:42:02", "2026-09-23 10:00:05", tsl[-1]]
keyts = [k for k in keyts if k in tsl]
print("采样时点:", keyts)

print("\n=== ① 高标(连板数>=3)今日轨迹 ===")
hi = [(c, v) for c, v in ind.items() if v["lb"] not in ("", None) and v["lb"].isdigit() and int(v["lb"]) >= 3]
hi.sort(key=lambda kv: -int(kv[1]["lb"]))
for c, v in hi:
    if c not in ser:
        print("  %s %-6s %s板 %s → 无 tick(不在观察池)" % (c, v["name"], v["lb"], v["ind"]))
        continue
    line = "  %s %-6s %s板 %-8s" % (c, v["name"], v["lb"], v["ind"])
    for ts in keyts:
        r = at(c, ts)
        line += " %s:%+.2f%%" % (ts[-8:-3], r["pct"] if r else float("nan"))
    mx = max(x["pct"] for x in ser[c].values())
    line += " | 窗内峰值%+.2f%% 末%+.2f%%" % (mx, ser[c][tsl[-1]]["pct"])
    print(line)

print("\n=== ② 触板→炸板 明细(今日涨停价核算) ===")
zb = []
for c, v in ind.items():
    if c not in ser:
        continue
    lmt = round(v["close"] * 1.1, 2)
    # 处理 20% 板(创业板/科创板 300/301/688/689)
    if c[:3] in ("300", "301", "688", "689"):
        lmt = round(v["close"] * 1.2, 2)
    hits = [(ts, r) for ts, r in ser[c].items() if r["latest"] >= lmt - 0.005]
    if hits:
        last = ser[c][tsl[-1]]
        zb.append((c, v["name"], v["ind"], v["lb"], lmt, hits[0][0], hits[-1][0], len(hits),
                   last["pct"], last["latest"]))
for z in sorted(zb, key=lambda x: x[8]):
    print("  %s %-6s %-8s %s板 涨停价%.2f 触板%s~%s(%d tick) → 末%+.2f%%(%.2f)" %
          (z[0], z[1], z[2], z[3], z[4], z[5][-8:], z[6][-8:], z[7], z[8], z[9]))
print("  触板总数=%d" % len(zb))

print("\n=== ③ 锁定末条(10:29:10) 贴板名单 ===")
for r in sorted(lk[-1]["rows"], key=lambda r: -r["pct"]):
    if r["pct"] >= 5:
        v = ind.get(r["code"], {})
        print("  %s %-6s %-8s %s板 %+.2f%% last=%.2f high=%.2f" %
              (r["code"], r["name"], v.get("ind", "池外"), v.get("lb", "-"), r["pct"], r["latest"], r["high"]))

print("\n=== ④ 三个采样时点的池内结构 ===")
for ts in keyts:
    t = [x for x in lk if x["ts"] == ts][0]
    p = [r["pct"] for r in t["rows"]]
    print("  %s n=%d 中位%+.2f 均值%+.2f 红%d/%d 贴板%d ≥5%%%d 跌≤-5%%%d 跌停%d" %
          (ts[-8:], len(p), statistics.median(p), statistics.mean(p),
           sum(1 for x in p if x > 0), len(p), sum(1 for x in p if x >= 9.5),
           sum(1 for x in p if x >= 5), sum(1 for x in p if x <= -5),
           sum(1 for x in p if x <= -9.5)))

print("\n=== ⑤ 2分钟内跌>=3pp 事件(按时间归段) ===")
seg = collections.Counter()
for c, s in ser.items():
    for i in range(2, len(tsl)):
        dpp = ser[c][tsl[i]]["pct"] - ser[c][tsl[i - 2]]["pct"]
        if dpp <= -3.0:
            seg[tsl[i][11:16]] += 1
print("  事件时间分布:", dict(sorted(seg.items())))
print("  事件总数:", sum(seg.values()))
# 09:43 之后的新增事件
late = [(tsl[i][-8:-3], c, ind.get(c, {}).get("name"), ind.get(c, {}).get("ind"),
         round(ser[c][tsl[i]]["pct"] - ser[c][tsl[i - 2]]["pct"], 2)) for c in ser for i in range(2, len(tsl))
        if tsl[i] > "2026-09-23 09:43:00" and ser[c][tsl[i]]["pct"] - ser[c][tsl[i - 2]]["pct"] <= -2.5]
print("  09:43 之后 2分钟跌>=-2.5pp 明细:")
for x in sorted(late):
    print("   ", x)

print("\n=== ⑥ 行业横截面(锁定末条, n>=3) ===")
gi = collections.defaultdict(list)
for r in lk[-1]["rows"]:
    gi[ind.get(r["code"], {}).get("ind", "池外")].append(r["pct"])
for k, v in sorted(gi.items(), key=lambda kv: statistics.mean(kv[1])):
    if len(v) >= 3:
        print("    %-10s n=%d 均值%+.2f 中位%+.2f %s" % (k, len(v), statistics.mean(v), statistics.median(v),
              [x for x in lk[-1]["rows"] if ind.get(x["code"], {}).get("ind") == k]))
