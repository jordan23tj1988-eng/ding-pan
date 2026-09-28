# -*- coding: utf-8 -*-
"""hb-e 补充探针: 封板集合差分 / 高标尾盘轨迹 / lhb 收盘腿对象核验"""
import json, csv, os, collections, datetime
D = r"D:\股票数据\市场数据"; DAY = "20260924"; CUT = "2026-09-24 14:30:00"
pool = {}
for r in csv.DictReader(open(os.path.join(D, "20260923", "zt_pool.csv"), encoding="utf-8-sig")):
    pool[r["代码"]] = {"name": r["名称"], "ind": r["所属行业"], "boards": r["连板数"],
                       "close_prev": float(r["最新价"])}
def lim_pct(c, n):
    if "ST" in n.upper(): return 0.05
    if c.startswith(("300", "301", "688", "689")): return 0.20
    if c.startswith(("4", "8", "92")): return 0.30
    return 0.10
for c, m in pool.items():
    m["up"] = round(m["close_prev"] * (1 + lim_pct(c, m["name"])), 2)
    m["dn"] = round(m["close_prev"] * (1 - lim_pct(c, m["name"])), 2)

frames = []
for line in open(os.path.join(D, "盘中", DAY, "realtime_ticks.jsonl"), encoding="utf-8"):
    o = json.loads(line)
    if o["ts"] <= CUT: frames.append(o)

def sealed_set(fr):
    s = set()
    for r in fr["rows"]:
        c = r["code"]; up = pool.get(c, {}).get("up")
        if up and abs(r["latest"] - up) < 0.005: s.add(c)
    return s
def touched_set(fr):
    s = set()
    for r in fr["rows"]:
        c = r["code"]; up = pool.get(c, {}).get("up")
        if up and r["high"] >= up - 0.005: s.add(c)
    return s

def frame_at(t):
    cand = [f for f in frames if f["ts"] <= "2026-09-24 " + t]
    return cand[-1] if cand else None

f1329, f1430 = frame_at("13:29:48"), frames[-1]
a, b = sealed_set(f1329), sealed_set(f1430)
print("封板集合差分 13:29:48 -> 14:30:00")
print("  新增封板:", [(c, pool[c]["name"], pool[c]["boards"] + "板") for c in sorted(b - a)])
print("  失去封板:", [(c, pool[c]["name"], pool[c]["boards"] + "板") for c in sorted(a - b)])
ta, tb = touched_set(f1329), touched_set(f1430)
print("  新增触板(未封):", [(c, pool[c]["name"]) for c in sorted(tb - ta - b)])
print("  触板总数 13:29 %d -> 14:30 %d" % (len(ta), len(tb)))

print("\n高标/关键票 13:00 -> 13:30 -> 14:00 -> 14:15 -> 14:30")
for c in ["601811", "600825", "000910", "688056", "002614", "603949", "603396", "002238", "603636", "600503", "002080"]:
    line = []
    for t in ["13:00:00", "13:29:48", "14:00:00", "14:15:00", "14:30:00"]:
        fr = frame_at(t)
        v = next((r["pct"] for r in fr["rows"] if r["code"] == c), None) if fr else None
        line.append("%+.2f" % v if v is not None else "NA")
    nm = pool.get(c, {}).get("name", "非池内/未取")
    print("  %s %s(%s) %s" % (c, nm, pool.get(c, {}).get("ind", "?"), " -> ".join(line)))

print("\n通用设备 n=6 逐票 14:30")
for c, m in pool.items():
    if m["ind"] == "通用设备":
        v = next((r["pct"] for r in f1430["rows"] if r["code"] == c), None)
        print("  %s %s %+.2f" % (c, m["name"], v))

# 尾盘 14:00-14:30 恶化/改善排序
def pct_at(fr, c):
    return next((r["pct"] for r in fr["rows"] if r["code"] == c), None)
f1400 = frame_at("14:00:00")
print("\n14:00 -> 14:30 变动最大(降序前8/升序前8)")
d = [(c, pct_at(f1400, c), pct_at(f1430, c)) for c in pool if pct_at(f1400, c) is not None and pct_at(f1430, c) is not None]
d.sort(key=lambda x: x[2] - x[1])
print("  降:", [(c, pool[c]["name"], round(p0, 2), round(p1, 2)) for c, p0, p1 in d[:8]])
print("  升:", [(c, pool[c]["name"], round(p0, 2), round(p1, 2)) for c, p0, p1 in d[-8:]])

# lhb 收盘腿对象
print("\n=== lhb 交易计划 20260923 ===")
p = os.path.join(D, "_学习", "交易计划_lhb_20260923.json")
if os.path.exists(p):
    o = json.load(open(p, encoding="utf-8"))
    print("keys", list(o.keys()))
    print(json.dumps(o, ensure_ascii=False)[:2500])
else:
    print("缺件")

print("\n=== 链上缺件核验 ===")
for rel in ["盘中/%s/pulse.json" % DAY, "盘中/%s/warboard.json" % DAY, "盘中/%s/执行流水.jsonl" % DAY,
            "盘中/%s/playbook.json" % DAY, "盘中/20260923/warboard.json"]:
    fp = os.path.join(D, rel)
    print("  %s exists=%s mtime=%s" % (rel, os.path.exists(fp),
          datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M:%S") if os.path.exists(fp) else "-"))
