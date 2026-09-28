# -*- coding: utf-8 -*-
"""hb-e 14:30 探针: 锁定时点 2026-09-24 14:30:00, 只用 <= 该时刻留档数据"""
import json, csv, os, collections, datetime

D = r"D:\股票数据\市场数据"
DAY = "20260924"
CUT = "2026-09-24 14:30:00"   # 决断时点
TICK = os.path.join(D, "盘中", DAY, "realtime_ticks.jsonl")

# ---------- 池元数据 ----------
pool = {}
for r in csv.DictReader(open(os.path.join(D, "20260923", "zt_pool.csv"), encoding="utf-8-sig")):
    pool[r["代码"]] = {
        "name": r["名称"], "ind": r["所属行业"],
        "boards": r["连板数"], "zt_stat": r["涨停统计"],
        "close_prev": float(r["最新价"]),
        "zhaban_cnt": r["炸板次数"],
    }
print("pool n =", len(pool))

def lim_pct(code, name):
    if "ST" in name.upper():
        return 0.05
    if code.startswith(("300", "301", "688", "689")):
        return 0.20
    if code.startswith(("4", "8", "92")):
        return 0.30
    return 0.10

for c, m in pool.items():
    p = lim_pct(c, m["name"])
    m["lim_pct"] = p
    m["up"] = round(m["close_prev"] * (1 + p), 2)
    m["dn"] = round(m["close_prev"] * (1 - p), 2)

# ---------- 载入 tick (严格 <= CUT) ----------
frames = []
bad_ts = 0
with open(TICK, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        ts = o["ts"]
        if ts > CUT:
            bad_ts += 1
            continue
        frames.append(o)
print("采用帧数(<= %s) = %d ; 被排除(未来帧) = %d" % (CUT, len(frames), bad_ts))
print("首帧", frames[0]["ts"], "末帧", frames[-1]["ts"], "声明n", frames[-1]["n"],
      "pool_stale", frames[-1].get("pool_stale"))

# 断更检查
gaps = []
prev = None
for fr in frames:
    t = datetime.datetime.strptime(fr["ts"], "%Y-%m-%d %H:%M:%S")
    if prev is not None:
        gaps.append((t - prev).total_seconds())
    prev = t
print("最大帧间隔 %.0fs  >120s帧数 %d" % (max(gaps), sum(1 for g in gaps if g > 120)))
last_dt = datetime.datetime.strptime(frames[-1]["ts"], "%Y-%m-%d %H:%M:%S")
print("末帧距决断时点 %.0fs" % (datetime.datetime.strptime(CUT, "%Y-%m-%d %H:%M:%S") - last_dt).total_seconds())

# ---------- 单帧统计 ----------
def snap(fr):
    st = {}
    for r in fr["rows"]:
        c = r["code"]
        m = pool.get(c, {})
        st[c] = {
            "name": r["name"], "ind": m.get("ind", "?"), "boards": m.get("boards", "?"),
            "latest": r["latest"], "pct": r["pct"], "high": r["high"], "low": r["low"],
            "open": r["open"], "preClose": r["preClose"], "amount": r["amount"],
            "up": m.get("up"), "dn": m.get("dn"),
        }
        s = st[c]
        s["sealed"] = (s["up"] is not None and abs(s["latest"] - s["up"]) < 0.005)
        s["limitdn"] = (s["dn"] is not None and abs(s["latest"] - s["dn"]) < 0.005)
        s["touched"] = (s["up"] is not None and s["high"] >= s["up"] - 0.005)
        s["zhaban"] = s["touched"] and not s["sealed"]
    return st

def stats(st):
    pcts = [v["pct"] for v in st.values()]
    n = len(pcts)
    sp = sorted(pcts)
    med = sp[n // 2] if n % 2 else (sp[n // 2 - 1] + sp[n // 2]) / 2
    return {
        "n": n,
        "med": round(med, 2),
        "mean": round(sum(pcts) / n, 2),
        "red": sum(1 for p in pcts if p > 0),
        "ge5": sum(1 for p in pcts if p >= 5),
        "le_m5": sum(1 for p in pcts if p <= -5),
        "sealed": sum(1 for v in st.values() if v["sealed"]),
        "zd": sum(1 for v in st.values() if v["limitdn"]),
        "touched": sum(1 for v in st.values() if v["touched"]),
        "zhaban": sum(1 for v in st.values() if v["zhaban"]),
    }

# 检查点帧
targets = ["09:59:00", "10:59:00", "11:29:00", "13:00:00", "13:29:00", "13:29:48", "13:59:00", "14:29:00"]
picks = {}
for tg in targets:
    key = "2026-09-24 " + tg
    cand = [f for f in frames if f["ts"] <= key]
    if cand:
        picks[tg] = cand[-1]

print("\n=== 检查点统计 ===")
for tg, fr in picks.items():
    st = snap(fr)
    s = stats(st)
    print("%s (帧 %s) med %+.2f mean %+.2f red %d/%d ge5 %d le-5 %d 封 %d 跌停 %d 触板 %d 炸板 %d (炸板率 %.1f%%)" % (
        tg, fr["ts"][11:], s["med"], s["mean"], s["red"], s["n"], s["ge5"], s["le_m5"],
        s["sealed"], s["zd"], s["touched"], s["zhaban"],
        100.0 * s["zhaban"] / s["touched"] if s["touched"] else 0))

# ---------- 14:30 明细 ----------
lastfr = frames[-1]
st = snap(lastfr)
s = stats(st)
print("\n=== 14:30 锁定帧明细 (ts %s) ===" % lastfr["ts"])
print("中位 %+.2f 均值 %+.2f 红盘 %d/%d >=+5%% %d <=-5%% %d 封板 %d 跌停 %d 触板 %d 炸板未回封 %d" % (
    s["med"], s["mean"], s["red"], s["n"], s["ge5"], s["le_m5"], s["sealed"], s["zd"], s["touched"], s["zhaban"]))

print("\n-- 炸板未回封 --")
for c, v in sorted(st.items(), key=lambda kv: -kv[1]["pct"]):
    if v["zhaban"]:
        print("  %s %s(%s /%s板) %+.2f latest %.2f 涨停价 %s 最高 %.2f 炸板次数(昨) %s" % (
            c, v["name"], v["ind"], v["boards"], v["pct"], v["latest"], v["up"], v["high"], pool[c]["zhaban_cnt"]))
print("-- 封板 --")
for c, v in sorted(st.items(), key=lambda kv: -kv[1]["pct"]):
    if v["sealed"]:
        print("  %s %s(%s /%s板) %+.2f" % (c, v["name"], v["ind"], v["boards"], v["pct"]))
print("-- 跌停 --")
for c, v in sorted(st.items(), key=lambda kv: kv[1]["pct"]):
    if v["limitdn"]:
        print("  %s %s(%s) %+.2f" % (c, v["name"], v["ind"], v["pct"]))
print("-- <=-5% 非跌停 --")
for c, v in sorted(st.items(), key=lambda kv: kv[1]["pct"]):
    if v["pct"] <= -5 and not v["limitdn"]:
        print("  %s %s(%s /%s板) %+.2f" % (c, v["name"], v["ind"], v["boards"], v["pct"]))

# 分档
print("\n-- 连板分档 --")
by_b = collections.defaultdict(list)
for c, v in st.items():
    by_b[v["boards"]].append(v)
for b in sorted(by_b, key=lambda x: -int(x)):
    vs = by_b[b]
    print("  %s板 n=%d 均值 %+.2f (封 %d / 炸 %d)" % (
        b, len(vs), sum(x["pct"] for x in vs) / len(vs),
        sum(1 for x in vs if x["sealed"]), sum(1 for x in vs if x["zhaban"])))

print("\n-- 行业聚合 n>=3 --")
by_i = collections.defaultdict(list)
for c, v in st.items():
    by_i[v["ind"]].append(v)
for i, vs in sorted(by_i.items(), key=lambda kv: -len(kv[1])):
    if len(vs) >= 3:
        print("  %s n=%d 均值 %+.2f (红 %d/%d)" % (i, len(vs), sum(x["pct"] for x in vs) / len(vs),
                                                sum(1 for x in vs if x["pct"] > 0), len(vs)))

# ---------- 批量跳水检测 (2分钟跌>=3pp) ----------
print("\n=== 2分钟跌>=3pp 事件 (全窗) ===")
evs = []
for i in range(2, len(frames)):
    a, b = frames[i - 2], frames[i]
    dta = datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")
    dtb = datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S")
    if (dtb - dta).total_seconds() > 240:
        continue
    ma = {r["code"]: r["pct"] for r in a["rows"]}
    for r in b["rows"]:
        c = r["code"]
        if c in ma and ma[c] - r["pct"] >= 3.0:
            evs.append((b["ts"], c, r["name"], pool[c]["ind"], round(ma[c], 2), r["pct"]))
for e in evs:
    print("  %s %s %s(%s) %+.2f -> %+.2f" % e)
print("总事件数 %d" % len(evs))

# 同刻同行业聚类
print("\n=== 同刻同行业同时跳水聚类(>=2只同行业同刻) ===")
grp = collections.defaultdict(list)
for ts, c, nm, ind, p0, p1 in evs:
    grp[(ts, ind)].append((c, nm, p0, p1))
hit = {k: v for k, v in grp.items() if len(v) >= 2}
for k, v in sorted(hit.items()):
    print("  %s %s -> %s" % (k[0], k[1], v))
print("聚类数 %d" % len(hit))

# ---------- 午后期观察票 ----------
print("\n=== 观察票 14:00->14:30 (池内留档价) ===")
watch = ["601811", "600825", "600843", "000850", "605058", "002937", "603803",
         "000910", "603124", "603328", "600825"]
seen = set()
for c in watch:
    if c in seen:
        continue
    seen.add(c)
    seg = [(f["ts"][11:16], next((r["pct"] for r in f["rows"] if r["code"] == c), None)) for f in frames
           if f["ts"] >= "2026-09-24 14:00:00"]
    seg = [x for x in seg if x[1] is not None]
    if not seg:
        print("  %s 无留档" % c)
        continue
    mid = [x for x in seg if x[0] <= "14:15"]
    print("  %s %s 14:00 %+.2f -> 14:15 %+.2f -> 14:30 %+.2f" % (
        c, pool[c]["name"], seg[0][1], mid[-1][1] if mid else float("nan"), seg[-1][1]))

# ---------- 尾盘候选(卖预案备料): 走弱/炸板/深绿 ----------
print("\n=== 14:45 备料: 卖侧候选(本账零持仓→仅列结构风险对象) ===")
for c, v in sorted(st.items(), key=lambda kv: kv[1]["pct"]):
    if v["pct"] <= -4:
        print("  %s %s(%s /%s板) %+.2f" % (c, v["name"], v["ind"], v["boards"], v["pct"]))
