# -*- coding: utf-8 -*-
import json, statistics, gzip, os, datetime

DIR = r"D:\股票数据\市场数据\盘中\20261012"
frames = [json.loads(l) for l in open(os.path.join(DIR, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
LOCK = "2026-10-12 14:45:00"
legal = [f for f in frames if f["ts"] <= LOCK]
lockf = legal[-1]
print("== 帧核验 ==")
print("首帧", frames[0]["ts"], "末帧(全量)", frames[-1]["ts"], "共", len(frames))
print("锁定帧", lockf["ts"], "n=", lockf["n"], "pool_date=", lockf["pool_date"], "stale=", lockf["pool_stale"], "src=", lockf["src"])
ts = [datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") for f in frames]
gaps = [(ts[i+1]-ts[i]).seconds for i in range(len(ts)-1)]
print("合法帧数(<=14:45:00):", len(legal), "最大相邻间隔s=", max(gaps), ">600s 次数=", sum(1 for g in gaps if g > 600))
print("窗后新写入帧:", [f["ts"] for f in frames if f["ts"] > LOCK][:6])


def lim(pc, code):
    if code[:3] in ("688", "300", "301"):
        return round(pc * 1.2, 2), 20
    return round(pc * 1.1, 2), 10


def snap(f):
    rows = f["rows"]
    pcts = [r["pct"] for r in rows]
    return rows, pcts


rows, pcts = snap(lockf)
med = statistics.median(pcts)
mean = sum(pcts) / len(pcts)
up = sum(1 for p in pcts if p > 0); dn = sum(1 for p in pcts if p < 0); fl = len(pcts) - up - dn
print("\n== 锁定帧池内宽度 ==")
print("n=%d 中位 %.2f%% 均值 %.2f%% 涨/跌/平 %d/%d/%d 区间 %.2f%%~%.2f%%" % (len(rows), med, mean, up, dn, fl, min(pcts), max(pcts)))

seal, zha, deep, dt, touch = [], [], [], [], []
for r in rows:
    L, g = lim(r["preClose"], r["code"])
    if r["pct"] >= 9.8:
        seal.append(r)
    if r["high"] >= L - 1e-6:
        touch.append(r)
        if r["latest"] < L - 1e-6:
            zha.append(r)
    if r["pct"] <= -5:
        deep.append(r)
    if r["pct"] <= -9.8:
        dt.append(r)
print("封板(pct>=9.8) %d 只:" % len(seal), " ".join("%s %s %.2f" % (r["code"], r["name"], r["pct"]) for r in sorted(seal, key=lambda x: -x["pct"])))
print("触板(独立口径) %d 只 / 其中触而未封 %d 只:" % (len(touch), len(touch) - len(seal)))
print("  触而未封:", " ".join("%s %s %.2f(高%.2f|涨停价%.2f)" % (r["code"], r["name"], r["pct"], r["high"], lim(r["preClose"], r["code"])[0]) for r in touch if r["pct"] < 9.8 or r["latest"] < lim(r["preClose"], r["code"])[0]))
print("炸板(latest<涨停价) %d 只:" % len(zha), " ".join("%s %s %.2f" % (r["code"], r["name"], r["pct"]) for r in zha))
print("深跌(<=-5) %d 只:" % len(deep), " ".join("%s %s %.2f" % (r["code"], r["name"], r["pct"]) for r in sorted(deep, key=lambda x: x["pct"])))
print("跌停(<=-9.8) %d 只:" % len(dt), " ".join("%s %s %.2f" % (r["code"], r["name"], r["pct"]) for r in dt))
print(">=+5%% %d 只 / <=-5%% %d 只" % (sum(1 for p in pcts if p >= 5), len(deep)))

# 轨迹
print("\n== 日内轨迹(池中位/均值/封板/涨跌) ==")
for mark in ["09:31", "09:45", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:15", "14:30", "14:44", "14:45"]:
    cand = [f for f in legal if f["ts"][11:16] <= mark]
    if not cand: continue
    f = cand[-1]
    p = [r["pct"] for r in f["rows"]]
    s = sum(1 for x in p if x >= 9.8)
    u = sum(1 for x in p if x > 0); d = sum(1 for x in p if x < 0)
    print("  %s (帧%s) 中位 %.2f 均值 %.2f 封板 %d 涨/跌 %d/%d" % (mark, f["ts"][11:19], statistics.median(p), sum(p)/len(p), s, u, d))

# 决断窗
print("\n== 决断窗 14:35:00-14:45:00 ==")
w = [f for f in legal if "2026-10-12 14:35:00" <= f["ts"] <= LOCK]
print("帧数", len(w), w[0]["ts"], "->", w[-1]["ts"])
p0 = {r["code"]: r["pct"] for r in w[0]["rows"]}
p1 = {r["code"]: r["pct"] for r in w[-1]["rows"]}
d = {c: p1[c] - p0[c] for c in p1 if c in p0}
print("窗内 Δ中位 %.2f / Δ均值 %.2f" % (statistics.median(list(d.values())), sum(d.values())/len(d)))
print("窗内跌幅最大5:", sorted(d.items(), key=lambda x: x[1])[:5])


def maxconc(win_sec, thr=-3.0):
    best = 0; who = []
    for i in range(len(w)):
        t0 = datetime.datetime.strptime(w[i]["ts"], "%Y-%m-%d %H:%M:%S")
        base = {r["code"]: r["pct"] for r in w[i]["rows"]}
        for j in range(i + 1, len(w)):
            t1 = datetime.datetime.strptime(w[j]["ts"], "%Y-%m-%d %H:%M:%S")
            if (t1 - t0).seconds > win_sec: break
            cur = {r["code"]: r["pct"] for r in w[j]["rows"]}
            hits = [c for c in cur if c in base and cur[c] - base[c] <= thr]
            if len(hits) > best:
                best = len(hits); who = (w[i]["ts"], w[j]["ts"], hits)
    return best, who


for sec in (120, 300):
    b, who = maxconc(sec)
    print("  <=%ds 内跌>=3pp 并发最大 = %d %s" % (sec, b, who))

# 跨场炸板窗 13:30-14:44
print("\n== 本场窗(13:30:51-14:44:05)炸板事件 ==")
cw = [f for f in legal if f["ts"] >= "2026-10-12 13:30:51"]
seen = {}
for f in cw:
    for r in f["rows"]:
        L, g = lim(r["preClose"], r["code"])
        st = seen.setdefault(r["code"], {"name": r["name"], "sealed": False, "broke": None, "resealed": None, "last": None})
        if r["latest"] >= L - 1e-6:
            if st["broke"] and st["resealed"] is None:
                st["resealed"] = f["ts"][11:19]
            st["sealed"] = True
        else:
            if st["sealed"] and st["broke"] is None:
                st["broke"] = f["ts"][11:19]
        st["last"] = (f["ts"][11:19], r["pct"])
for c, st in seen.items():
    if st["broke"]:
        print("  %s %s 首破 %s 回封 %s 末帧 %s" % (c, st["name"], st["broke"], st["resealed"] or "未回封", st["last"]))
