# -*- coding: utf-8 -*-
"""hb-d 13:30 只读分析: 池帧统计/2分钟簇/603370 5分钟跌幅/昨日同刻对比"""
import json, os, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
DEC = "2026-10-23 13:31:00"   # 决断时间戳(本场)
dec = datetime.datetime.strptime(DEC, "%Y-%m-%d %H:%M:%S")

frames = []
for ln in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    j = json.loads(ln)
    t = datetime.datetime.strptime(j["ts"], "%Y-%m-%d %H:%M:%S")
    frames.append((t, j))

print("总帧数", len(frames), "首帧", frames[0][0].time(), "末帧", frames[-1][0].time())
elig = [(t, j) for t, j in frames if t <= dec]
print("决断帧前可用帧", len(elig), "末可用帧", elig[-1][0])
gaps = [(elig[i][0] - elig[i-1][0]).total_seconds() for i in range(1, len(elig))]
print("最大帧间隔 %.0fs 均值 %.1fs" % (max(gaps), statistics.mean(gaps)))

t, j = elig[-1]
rows = j["rows"]
pcts = [r["pct"] for r in rows if r.get("pct") is not None]
print("\n[昨日涨停池 %d 票 @%s] 中位 %+.2f%% 均值 %+.2f%% 涨%d/跌%d 涨停%d 跌停%d"
      % (len(rows), t.time(), statistics.median(pcts), statistics.mean(pcts),
         sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0),
         sum(1 for p in pcts if p > 9.7), sum(1 for p in pcts if p < -9.7)))
if rows and rows[0]["code"] in [r["code"] for r in rows]:
    pass
p603370 = [r for r in rows if r["code"] == "603370"]
print("603370 在池帧中:", p603370[0]["pct"] if p603370 else "不在昨涨停池", "| latest", p603370[0]["latest"] if p603370 else "")

# 2分钟簇: 每帧与 >=100s 前的帧比较
idx = list(range(len(elig)))
clusters = []
for i in idx:
    ti, ji = elig[i]
    base = None
    for k in range(i - 1, -1, -1):
        d = (ti - elig[k][0]).total_seconds()
        if d >= 100:
            base = elig[k]
            break
        if d > 180:
            break
    if base is None:
        continue
    bp = {r["code"]: r["pct"] for r in base[1]["rows"] if r.get("pct") is not None}
    drops = [(r["code"], r["name"], r["pct"] - bp[r["code"]]) for r in ji["rows"]
             if r.get("pct") is not None and r["code"] in bp and (r["pct"] - bp[r["code"]]) <= -3.0]
    if len(drops) >= 2:
        clusters.append((ti.strftime("%H:%M:%S"), len(drops), drops))
print("\n≥2只/2分钟内跌3pp 的簇数:", len(clusters))
for c in clusters[-6:]:
    print(" ", c[0], c[1], [(d[1], round(d[2], 2)) for d in c[2]])
last12 = [c for c in clusters if c[0] >= (elig[-1][0] - datetime.timedelta(minutes=25)).strftime("%H:%M:%S")]
print("最近25分钟最大簇:", max([c[1] for c in last12]) if last12 else 0)

# 603370 分时 5 分钟跌幅
mt = json.load(open(os.path.join(D, "_hb_d_minute_603370.json"), encoding="utf-8"))["minute"]
mins = []
for m in mt:
    s = m.split(" ")
    mins.append((s[0], float(s[1])))
print("\n[603370 分时] 点数", len(mins), "末点", mins[-1])
pre = 28.70  # 昨收? 打印开盘首点辅助核对
print("首点", mins[0], "日内最高", max(p for _, p in mins), "日内最低", min(p for _, p in mins))
# 最近5分钟(用决断时刻前的点)
cut = [x for x in mins if x[0] <= "1331"]
if cut:
    ref = None
    for k in range(len(cut) - 1, -1, -1):
        if int(cut[-1][0]) - int(cut[k][0]) >= 5 or (int(cut[-1][0][:2]) * 60 + int(cut[-1][0][2:])) - (int(cut[k][0][:2]) * 60 + int(cut[k][0][2:])) >= 5:
            ref = cut[k]
            break
    if ref:
        print("5分钟前(%s)=%.2f → 决断前(%s)=%.2f, 变动 %+.2f%%" % (ref[0], ref[1], cut[-1][0], cut[-1][1], (cut[-1][1] / ref[1] - 1) * 100))
    lows = [p for _, p in cut]
    print("决断前日内最低(分时) %.2f; 今日低(报价) 27.62; 触发条件=破27.62且5分钟跌≥2%%" % min(lows))

# 昨日同刻对比: 20261022 hb-d 池
try:
    y = json.load(open(r"D:\股票数据\市场数据\盘中\20261022\_hb_d_pools_1330.json", encoding="utf-8"))
    yzt, yzb = y.get("zt") or [], y.get("zb") or []
    ydt = y.get("dt") or []
    print("\n[昨日 20261022 13:31 同刻] 涨停 %d 炸板 %d 跌停 %d 炸板率 %.4f | fetched %s"
          % (len(yzt), len(yzb), len(ydt), len(yzb) / max(1, len(yzb) + len(yzt)), y.get("fetched")))
except Exception as e:
    print("昨日池读取失败", e)
