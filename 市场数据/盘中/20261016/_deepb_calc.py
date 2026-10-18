# -*- coding: utf-8 -*-
"""深场B(14:45) 尾盘场计算: 只读, 不改任何生产文件。
决断时间戳 = 2026-10-16 14:45:00 CST (job sentiment-intraday-deepb, cron 45 14 * * 1-5)
一切输入 ts <= 14:45:00; 排他登记 > 14:45:00 的帧。"""
import json, statistics as st, csv, os
from collections import Counter
from datetime import datetime

BASE = r"D:\股票数据\市场数据"
D = "20261016"
DAY = os.path.join(BASE, "盘中", D)
P = os.path.join(DAY, "realtime_ticks.jsonl")
CUT = "2026-10-16 14:45:00"

frames = []
for line in open(P, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("ts"):
        frames.append(d)

allts = [f["ts"] for f in frames]
legal = [f for f in frames if f["ts"] <= CUT]
print("总帧", len(frames), "首", allts[0], "末", allts[-1])
print("合法帧(<=14:45:00)", len(legal), "末合法帧", legal[-1]["ts"])
print("被剔除帧(>14:45:00)", [t for t in allts if t > CUT])

def p2s(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

gaps = [(p2s(legal[i+1]["ts"]) - p2s(legal[i]["ts"])).total_seconds() for i in range(len(legal)-1)]
print("间隔 min/max/mean", min(gaps), max(gaps), round(sum(gaps)/len(gaps), 2))
print(">120s 空档", sum(1 for g in gaps if g > 120))
lag = (p2s(CUT) - p2s(legal[-1]["ts"])).total_seconds()
print("末合法帧距决断秒", lag)

# 午休窗冻结核验
noon = [f for f in legal if "11:31:00" <= f["ts"][-8:] <= "12:59:00"]
if noon:
    a = {x["code"]: x["pct"] for x in noon[0]["rows"]}
    same = sum(1 for f in noon if {(x["code"], x["pct"]) for x in f["rows"]} == {(c, v) for c, v in a.items()})
    print("午休窗帧", len(noon), "首", noon[0]["ts"], "末", noon[-1]["ts"], "逐票价全等帧", same)

def snap(f):
    return {x["code"]: x for x in (f.get("rows") or [])}

last = legal[-1]
rows = last.get("rows")
print("帧内票数", len(rows), "| 帧字段", [k for k in last.keys() if k != "rows"])
print("池元信息 pool_date=", last.get("pool_date"), "pool_kind=", last.get("pool_kind"),
      "pool_stale=", last.get("pool_stale"), "src=", last.get("src"), "phase=", last.get("phase"))

def zt_px(x):
    p = x["preClose"]
    lim = 0.20 if x["code"].startswith(("300", "301", "688")) else 0.10
    return round(p * (1 + lim), 2), lim

pool = []
for c, x in snap(last).items():
    ztp, lim = zt_px(x)
    pool.append(dict(code=c, name=x["name"], pct=x["pct"], latest=x["latest"], pre=x["preClose"],
                     high=x["high"], low=x["low"], open=x["open"], ztp=ztp, lim=lim,
                     sealed=x["latest"] >= ztp - 1e-9, touched=x["high"] >= ztp - 1e-9))

pcts = sorted(p["pct"] for p in pool)
print("\n== 池截面 @", last["ts"], "n=", len(pool))
print("中位", round(st.median(pcts), 2), "均值", round(sum(pcts)/len(pcts), 3),
      "最低", min(pcts), "最高", max(pcts))
print("红", sum(1 for p in pcts if p > 0), "绿", sum(1 for p in pcts if p < 0), "平", sum(1 for p in pcts if p == 0))
print(">=+5%", sum(1 for p in pcts if p >= 5), ">=+3%", sum(1 for p in pcts if p >= 3),
      "<=-5%", sum(1 for p in pcts if p <= -5), "<=-3%", sum(1 for p in pcts if p <= -3))
print("封板", sum(1 for p in pool if p["sealed"]),
      "炸板(触而未封)", sum(1 for p in pool if p["touched"] and not p["sealed"]),
      "跌停", sum(1 for p in pool if p["pct"] <= -9.8))
print("封板名单", [p["code"]+p["name"]+"%+.2f" % p["pct"] for p in pool if p["sealed"]])
print("炸板名单", [p["code"]+p["name"]+"%+.2f" % p["pct"] for p in pool if p["touched"] and not p["sealed"]])
print("跌停名单", [p["code"]+p["name"]+"%+.2f" % p["pct"] for p in pool if p["pct"] <= -9.8])
print("触板(含封)数", sum(1 for p in pool if p["touched"]))

def chg(code, n):
    i = len(legal) - 1 - n
    if i < 0:
        return None
    a = snap(legal[i]).get(code)
    b = snap(last).get(code)
    if not a or not b:
        return None
    return round(b["pct"] - a["pct"], 2)

print("\n== 变化速率 ==")
for n, lab in [(1, "1分钟"), (2, "2分钟"), (5, "5分钟"), (10, "10分钟"), (20, "20分钟"), (30, "30分钟"), (40, "40分钟"), (60, "60分钟")]:
    vals = [chg(p["code"], n) for p in pool]
    vals = [v for v in vals if v is not None]
    print(lab, "中位", round(st.median(vals), 2), "最弱", min(vals), "≤-3pp家数", sum(1 for v in vals if v <= -3),
          "≥+2pp家数", sum(1 for v in vals if v >= 2))

print("\n== 全池60分钟变化 最弱/最强 ==")
v60 = [(chg(p["code"], 60), p["code"], p["name"], p["pct"]) for p in pool]
v60 = [x for x in v60 if x[0] is not None]
v60.sort()
print("最弱5", v60[:5])
print("最强5", v60[-5:])

print("\n== 题材批量跳水扫描(全部<=120s帧对, 阈<=-3pp) ==")
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
                dd = round(b[c]["pct"] - a[c]["pct"], 2)
                if dd <= -3:
                    mem.append(c + "%+.2f->%+.2f" % (a[c]["pct"], b[c]["pct"]))
        if len(mem) >= 3:
            batches.append((legal[i]["ts"], legal[j]["ts"], len(mem), mem))
print("达阈批数", len(batches))
for b in batches:
    print("  ", b[0], "->", b[1], b[2], b[3][:8])

print("\n== 末窗最弱单帧跌幅 ==")
for span in (2, 5, 40):
    i = len(legal) - 1 - span
    if i < 0:
        continue
    a, b = snap(legal[i]), snap(legal[-1])
    ds = [(round(b[c]["pct"] - a[c]["pct"], 2), c) for c in a if c in b]
    print("末%d分钟 最弱单帧" % span, min(ds), "达阈(<=-3)只数", sum(1 for d, _ in ds if d <= -3))

print("\n== 日内轨迹 ==")
marks = ["09:31", "09:40", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:15", "14:30", "14:44"]
print("时点 | 中位 | 均值 | 涨/跌 | 封板 | 炸板 | 跌停")
traj = {}
for m in marks:
    target = "2026-10-16 " + m + ":00"
    i = None
    for k, f in enumerate(legal):
        if p2s(f["ts"]) <= p2s(target):
            i = k
        else:
            break
    if i is None:
        continue
    S = snap(legal[i])
    ps = sorted(x["pct"] for x in S.values())
    sealed = sum(1 for c, x in S.items() if x["latest"] >= zt_px(x)[0] - 1e-9)
    touched = sum(1 for c, x in S.items() if x["high"] >= zt_px(x)[0] - 1e-9)
    dt = sum(1 for x in S.values() if x["pct"] <= -9.8)
    traj[m] = round(st.median(ps), 2)
    print(m, legal[i]["ts"][-8:], "|", round(st.median(ps), 2), "|", round(sum(ps)/len(ps), 3), "|",
          str(sum(1 for p in ps if p > 0))+"/"+str(sum(1 for p in ps if p < 0)), "|",
          sealed, "|", touched - sealed, "|", dt)
print("轨迹字典", traj)

print("\n== 连板列(读 zt_pool.csv 20261015) ==")
try:
    zf = os.path.join(BASE, "20261015", "zt_pool.csv")
    rows2 = list(csv.DictReader(open(zf, encoding="utf-8-sig")))
    print("csv 列", list(rows2[0].keys())[:14], "行数", len(rows2))
    lb = {r["代码"]: int(float(r["连板数"])) for r in rows2 if r.get("连板数")}
    print("池内连板分布", Counter(lb.values()), "最高板", max(lb.values()))
    for p in sorted(pool, key=lambda z: (-lb.get(z["code"], 0), z["pct"])):
        if lb.get(p["code"], 0) >= 2:
            print("  高度票", p["code"], p["name"], "连板", lb.get(p["code"]), "pct %+.2f" % p["pct"],
                  "封" if p["sealed"] else ("炸" if p["touched"] else "未触"))
except Exception as e:
    print("连板读取失败", e)

print("\n== 持仓票读数 (第七账 盘中作战) ==")
hb = json.load(open(os.path.join(DAY, "_hb_e_quote.json"), encoding="utf-8"))
for c, q in hb.items():
    if "latest" not in q and "last" in q:
        q["latest"] = q["last"]
S_last = snap(last)
for code, cost, sh, src in [("000011", 10.11, 5900, "第七账·账本在持(10/03)"),
                            ("002860", 20.08, 2900, "第七账·引擎09:26自机制买入")]:
    inpool = S_last.get(code)
    q = hb.get("sz"+code) or hb.get("sh"+code)
    print(code, (q or {}).get("name"), src,
          "| 池内:", ("是 @%s latest=%s pct=%s" % (last["ts"], inpool["latest"], inpool["pct"])) if inpool else "否",
          "| hb-e留档:", (q or {}).get("time"), "last", (q or {}).get("latest"), "pct", (q or {}).get("pct"),
          "| 相对成本%%", round(((q or {}).get("latest", 0)/cost-1)*100, 2))

print("\n== 持仓票读数 (master账 本日持仓, 经09:25四笔调整) ==")
master_hold = [("600668", 8.15, 6100), ("605189", 17.97, 1100), ("000601", 6.68, 6000),
               ("603968", 14.30, 2100), ("000823", 25.13, 800)]
for code, cost, sh in master_hold:
    inpool = S_last.get(code)
    q = hb.get("sz"+code) or hb.get("sh"+code)
    print(code, (q or {}).get("name"),
          "| 池内:", ("是 @%s latest=%s pct=%s" % (last["ts"], inpool["latest"], inpool["pct"])) if inpool else "否",
          "| hb-e:", (q or {}).get("time"), (q or {}).get("latest"), (q or {}).get("pct"),
          "| 相对成本%%", round(((q or {}).get("latest", 0)/cost-1)*100, 2))

print("\n== 池内持仓票在实时帧的最新(≤14:45) ==")
for code in ("605189", "600668", "002815"):
    x = S_last.get(code)
    if x:
        print(code, x["name"], "latest", x["latest"], "pct", x["pct"], "high", x["high"], "low", x["low"], "open", x["open"], "pre", x["preClose"])
