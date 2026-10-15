# -*- coding: utf-8 -*-
"""深场B(14:45) 尾盘场计算: 只读, 不改任何生产文件。决断时间戳=2026-10-14 14:45:00"""
import json, statistics as st
from datetime import datetime

P = r"D:\股票数据\市场数据\盘中\20261014\realtime_ticks.jsonl"
CUT = "2026-10-14 14:45:00"

frames = []
for line in open(P, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    t = d.get("ts")
    if not t:
        continue
    frames.append(d)

allts = [f["ts"] for f in frames]
legal = [f for f in frames if f["ts"] <= CUT]
print("总帧", len(frames), "首", allts[0], "末", allts[-1])
print("合法帧(<=14:45:00)", len(legal), "末合法帧", legal[-1]["ts"])
print("被剔除帧(>14:45:00)", [t for t in allts if t > CUT])

# 采样间隔
def p2s(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
gaps = [(p2s(legal[i+1]["ts"]) - p2s(legal[i]["ts"])).total_seconds() for i in range(len(legal)-1)]
print("间隔 min/max/mean", min(gaps), max(gaps), round(sum(gaps)/len(gaps), 2))
print(">120s 空档", sum(1 for g in gaps if g > 120))

def idx(ts):
    for i, f in enumerate(legal):
        if f["ts"] == ts:
            return i
    return None

last = legal[-1]
rows = last.get("rows") or last.get("stocks") or last.get("data")
if rows is None:
    # 探测字段
    print("keys", list(last.keys()))
    raise SystemExit(1)
print("帧内票数", len(rows), "| 帧字段", [k for k in last.keys() if k != "rows"])

def snap(f):
    r = f.get("rows")
    return {x["code"]: x for x in r}

S_last = snap(last)
S_1430 = snap(legal[idx("2026-10-14 14:29:54")]) if idx("2026-10-14 14:29:54") is not None else None

def zt_px(x):
    p = x["preClose"]
    lim = 0.20 if x["code"].startswith(("300", "301", "688")) else 0.10
    return round(p * (1 + lim), 2), lim

pool = []
for c, x in S_last.items():
    pct = x["pct"]
    ztp, lim = zt_px(x)
    sealed = x["latest"] >= ztp - 1e-9
    touched = x["high"] >= ztp - 1e-9
    pool.append(dict(code=c, name=x["name"], pct=pct, latest=x["latest"], pre=x["preClose"],
                     high=x["high"], low=x["low"], open=x["open"], ztp=ztp, sealed=sealed, touched=touched))

pcts = sorted(p["pct"] for p in pool)
print("\n== 池截面 @", last["ts"], "n=", len(pool))
print("中位", round(st.median(pcts), 2), "均值", round(sum(pcts)/len(pcts), 3),
      "最低", min(pcts), "最高", max(pcts))
print("红", sum(1 for p in pcts if p > 0), "绿", sum(1 for p in pcts if p < 0), "平", sum(1 for p in pcts if p == 0))
print("封板", sum(1 for p in pool if p["sealed"]), "炸板(触而未封)", sum(1 for p in pool if p["touched"] and not p["sealed"]),
      "跌停", sum(1 for p in pool if p["pct"] <= -9.8))
print("封板名单", [p["code"] + p["name"] + "%+.2f" % p["pct"] for p in pool if p["sealed"]])
print("炸板名单", [p["code"] + p["name"] + "%+.2f" % p["pct"] for p in pool if p["touched"] and not p["sealed"]])
print("跌停名单", [p["code"] + p["name"] + "%+.2f" % p["pct"] for p in pool if p["pct"] <= -9.8])

# 变化速率(以合法帧索引回溯)
def chg(code, n):
    i = len(legal) - 1 - n
    if i < 0:
        return None
    a = snap(legal[i]).get(code)
    b = S_last.get(code)
    if not a or not b:
        return None
    return round(b["pct"] - a["pct"], 2)

print("\n== 变化速率(中位) ==")
for n, lab in [(1, "1分钟"), (2, "2分钟"), (5, "5分钟"), (10, "10分钟"), (20, "20分钟"), (30, "30分钟"), (40, "40分钟"), (60, "60分钟")]:
    vals = [chg(p["code"], n) for p in pool]
    vals = [v for v in vals if v is not None]
    vals_sorted = sorted(vals)
    le3 = sum(1 for v in vals if v <= -3)
    print(lab, "中位", round(st.median(vals), 2), "≤-3pp家数", le3, "≥+2pp家数", sum(1 for v in vals if v >= 2))

# 持仓票
print("\n== 持仓票读数 ==")
for code, cost, sh, src in [("600693", 12.4124, 4000, "09:25 A级承接"), ("605577", 17.6576, 2200, "09:25 A级承接")]:
    x = S_last.get(code)
    if not x:
        print(code, "不在池"); continue
    ztp, _ = zt_px(x)
    print(code, x["name"], src, "| 末帧", x["latest"], "pct", x["pct"], "前收", x["preClose"],
          "涨停价", ztp, "high", x["high"], "low", x["low"], "open", x["open"])
    print("   相对成本 %+.2f%%" % ((x["latest"]/cost - 1)*100), "浮盈", round((x["latest"]-cost)*sh, 2))
    # 窗内极值
    mx = mn = None
    for f in legal:
        r = snap(f)
        if code in r:
            v = r[code]["latest"]
            if mx is None or v > mx[0]:
                mx = (v, f["ts"])
            if mn is None or v < mn[0]:
                mn = (v, f["ts"])
    print("   窗内最高", mx, "窗内最低", mn)
    for n in (2, 5, 10, 20, 30, 40, 60):
        print("   ", n, "分钟变化", chg(code, n))

# 批量跳水(帧对<=120s)
print("\n== 题材批量跳水扫描(全部<=120s帧对) ==")
batches = []
for i in range(len(legal)):
    for j in range(i+1, len(legal)):
        dt = (p2s(legal[j]["ts"]) - p2s(legal[i]["ts"])).total_seconds()
        if dt > 120:
            break
        a, b = snap(legal[i]), snap(legal[j])
        mem = []
        for c in a:
            if c in b:
                d = round(b[c]["pct"] - a[c]["pct"], 2)
                if d <= -3:
                    mem.append(c + "%+.2f->%+.2f(%+.2f)" % (a[c]["pct"], b[c]["pct"], d))
        if len(mem) >= 3:
            batches.append((legal[i]["ts"], legal[j]["ts"], len(mem), mem))
print("达阈批数", len(batches))
for b in batches:
    print("  ", b[0], "->", b[1], b[2], b[3][:8])

# 末40分钟/5分钟/2分钟
for span in (2, 5, 40):
    n = span  # 1帧=1分钟
    i = len(legal) - 1 - n
    if i < 0: continue
    a, b = snap(legal[i]), snap(legal[-1])
    mem = []
    for c in a:
        if c in b:
            d = round(b[c]["pct"] - a[c]["pct"], 2)
            if d <= -3:
                mem.append(c)
    print("末%d分钟内最弱单帧跌幅" % span, min(round(b[c]["pct"]-a[c]["pct"],2) for c in a if c in b), "达阈只数", len(mem))

# 指数/池外(可选)
print("\n== 全池各窗口最弱/最强(60分钟) ==")
v60 = [(chg(p["code"], 60), p["code"], p["name"]) for p in pool]
v60 = [x for x in v60 if x[0] is not None]
v60.sort()
print("最弱5", v60[:5])
print("最强5", v60[-5:])
