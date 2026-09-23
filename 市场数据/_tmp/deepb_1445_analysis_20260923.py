# -*- coding: utf-8 -*-
"""深场B 14:45 场 · 决策时点(14:45:00)前留档 tick 分析"""
import json, io, os, statistics, collections

BASE = r"D:\股票数据\市场数据"
TDIR = os.path.join(BASE, "盘中", "20260923")
DEC = "2026-09-23 14:45:00"   # 名义决断时点
W0, W1 = "2026-09-23 14:30:00", DEC  # 尾盘段

snaps = []
for l in io.open(os.path.join(TDIR, "realtime_ticks.jsonl"), encoding="utf-8-sig"):
    if l.strip():
        snaps.append(json.loads(l))
ok = [s for s in snaps if s["ts"] <= DEC]
last = ok[-1]
print("== 留档核验 ==")
print("总快照", len(snaps), "| <=14:45:00", len(ok), "| 首", ok[0]["ts"], "| 末", last["ts"])
gaps = []
prev = None
import datetime
def P(t): return datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
for s in ok:
    if prev:
        d = (P(s["ts"]) - P(prev)).total_seconds()
        if d > 120: gaps.append((prev, s["ts"], d))
    prev = s["ts"]
print(">120s 间隔:", gaps if gaps else "0 处")
print("末条滞后(相对写档):", "见终端 date")

# 限价
def lim(c):
    return 0.20 if c[:3] in ("300", "301", "688") else 0.10
def lp(pre, c):
    return round(pre * (1 + lim(c)) + 1e-9, 2)
def dp(pre, c):
    return round(pre * (1 - lim(c)) + 1e-9, 2)

# 题材归位
th = json.load(io.open(os.path.join(BASE, "_学习", "题材归位_20260922.json"), encoding="utf-8-sig"))
M = th["映射"]
ind = {k: v.get("所属行业") for k, v in M.items()}
lb = {k: int(v.get("连板数") or 0) for k, v in M.items()}

print("\n== 池级轨迹 (20260922涨停池 62只) ==")
marks = ["2026-09-23 09:31:00", "2026-09-23 10:00:00", "2026-09-23 10:30:00", "2026-09-23 11:00:00",
         "2026-09-23 11:30:00", "2026-09-23 13:00:00", "2026-09-23 13:30:00", "2026-09-23 14:00:00",
         "2026-09-23 14:30:00", "2026-09-23 14:44:55"]
def stat(s):
    rows = s["rows"]; p = [r["pct"] for r in rows]
    seal = sum(1 for r in rows if r["latest"] >= lp(r["preClose"], r["code"]) - 0.001)
    dt = sum(1 for r in rows if r["latest"] <= dp(r["preClose"], r["code"]) + 0.001)
    return len(rows), sum(1 for x in p if x > 0), sum(1 for x in p if x < 0), round(statistics.median(p), 2), round(statistics.mean(p), 2), seal, dt
for m in marks:
    cand = [s for s in ok if s["ts"] <= m]
    if not cand: continue
    s = cand[-1]
    n, up, dn, med, mean, seal, dt = stat(s)
    print(f"{s['ts'][11:16]}  n={n} 涨{up}/跌{dn} 中位{med:+.2f} 均值{mean:+.2f} 封板{seal} 跌停{dt}")

# 末条明细
print("\n== 14:44:55 明细 ==")
rows = last["rows"]
sealed, zb, dn = [], [], []
for r in rows:
    L, D = lp(r["preClose"], r["code"]), dp(r["preClose"], r["code"])
    if r["latest"] >= L - 0.001: sealed.append(r)
    elif r["high"] >= L - 0.001: zb.append(r)
    if r["latest"] <= D + 0.001: dn.append(r)
print("封板(%d): %s" % (len(sealed), " ".join(f"{r['code']}{r['name']}[{lb.get(r['code'],0)}板]{r['pct']:+.1f}" for r in sealed)))
print("炸板未封(%d): %s" % (len(zb), " ".join(f"{r['code']}{r['name']}[{lb.get(r['code'],0)}板]{r['pct']:+.1f}" for r in zb)))
print("跌停(%d): %s" % (len(dn), " ".join(f"{r['code']}{r['name']}[{lb.get(r['code'],0)}板]{r['pct']:+.1f}" for r in dn)))

# 高度梯队
print("\n== 高度梯队(9/22连板数 → 今日14:45) ==")
bylb = collections.defaultdict(list)
for r in rows:
    bylb[lb.get(r["code"], 0)].append(r)
for k in sorted(bylb, reverse=True):
    for r in sorted(bylb[k], key=lambda x: -x["pct"]):
        L = lp(r["preClose"], r["code"])
        tag = "封板" if r["latest"] >= L - 0.001 else ("炸板" if r["high"] >= L - 0.001 else "未封")
        print(f"  {k}板 {r['code']} {r['name']:<6} {r['pct']:+6.2f}% {tag} 高{r['high']} 现{r['latest']}")

# 行业聚合
print("\n== 行业聚合(所属行业, n>=3) ==")
g = collections.defaultdict(list)
for r in rows:
    g[ind.get(r["code"], "?")].append(r)
for k, v in sorted(g.items(), key=lambda x: -statistics.mean([r["pct"] for r in x[1]])):
    if len(v) < 3: continue
    ps = [r["pct"] for r in v]
    sl = sum(1 for r in v if r["latest"] >= lp(r["preClose"], r["code"]) - 0.001)
    print(f"  {k:<8} n={len(v)} 均{statistics.mean(ps):+6.2f}% 封{sl}/{len(v)}  {','.join(r['name'] for r in v)}")

# 尾盘段
print("\n== 尾盘段 14:30:00 → 14:44:55 ==")
s0 = [s for s in ok if s["ts"] <= W0][-1]
m0 = {r["code"]: r for r in s0["rows"]}
delta = []
for r in rows:
    a = m0.get(r["code"])
    if a: delta.append((r["pct"] - a["pct"], r))
delta.sort(key=lambda x: x[0])
print(" 池级: 中位 %+.2f→%+.2f  均值 %+.2f→%+.2f  封板 %d→%d" % (
    statistics.median([a["pct"] for a in m0.values()]), statistics.median([r["pct"] for r in rows]),
    statistics.mean([a["pct"] for a in m0.values()]), statistics.mean([r["pct"] for r in rows]),
    sum(1 for a in m0.values() if a["latest"] >= lp(a["preClose"], a["code"]) - 0.001), len(sealed)))
print(" 最强5:", " | ".join(f"{r['name']}{d:+.2f}pp" for d, r in delta[-5:][::-1]))
print(" 最弱5:", " | ".join(f"{r['name']}{d:+.2f}pp" for d, r in delta[:5]))
print(" 涨超5%% %d 只 / 跌超5%% %d 只" % (sum(1 for r in rows if r["pct"] > 5), sum(1 for r in rows if r["pct"] < -5)))

# 风险扫描
print("\n== 风险扫描(池内62只) ==")
# 自当日高点回撤
dd = sorted((((r["latest"] / r["high"] - 1) * 100, r) for r in rows if r["high"] > 0), key=lambda x: x[0])
print(" 自日高回撤>=5%%: %d 只; 最深5: %s" % (sum(1 for d, _ in dd if d <= -5), " ".join(f"{r['name']}{d:.1f}%%" for d, r in dd[:5])))
# 2分钟批量跳水
seq = [s for s in ok if s["ts"] >= "2026-09-23 14:00:00"]
worst = None
for i in range(len(seq) - 2):
    a = {r["code"]: r["pct"] for r in seq[i]["rows"]}
    b = {r["code"]: r["pct"] for r in seq[i + 2]["rows"]}
    drops = [(b[c] - a[c], c) for c in a if c in b]
    n3 = [x for x in drops if x[0] <= -3]
    if n3 and (worst is None or len(n3) > len(worst[0])):
        worst = (n3, seq[i]["ts"], seq[i + 2]["ts"])
print(" 2分钟批量跳水(>=3只跌>=3pp) 命中: %s" % ("0 命中" if not worst else worst))
mx = None
for i in range(len(seq) - 1):
    a = {r["code"]: r["pct"] for r in seq[i]["rows"]}
    b = {r["code"]: r["pct"] for r in seq[i + 1]["rows"]}
    for c in a:
        if c in b and (mx is None or b[c] - a[c] < mx[0]):
            mx = (b[c] - a[c], c, seq[i]["ts"], seq[i + 1]["ts"])
print(" 单分钟最大单票急跌: %s" % (f"{mx[0]:+.2f}pp {mx[1]} {mx[2][11:16]}→{mx[3][11:16]}" if mx else "无"))

# A级对象
print("\n== 002080 在池核验 ==")
print(" 池内 tick 含 002080:", any(r["code"] == "002080" for r in rows))
