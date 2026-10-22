# -*- coding: utf-8 -*-
"""14:45 深场B: 池内截面序列 + 炸板未回封 + 与 14:33 帧对比"""
import json, statistics, os

F = r"D:\股票数据\市场数据\盘中\20261021\realtime_ticks.jsonl"
frames = []
for line in open(F, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        frames.append(json.loads(line))
    except Exception:
        pass
print("frames", len(frames), "first", frames[0]["ts"], "last", frames[-1]["ts"])


def cap(code):
    return 20.0 if code[:2] in ("30", "68") else 10.0


def limit_px(pre, c):
    return round(pre * (1 + c / 100.0), 2)


def frame_stats(fr):
    rows = fr["rows"]
    pcts = [r["pct"] for r in rows]
    up = sum(1 for p in pcts if p > 0.05)
    dn = sum(1 for p in pcts if p < -0.05)
    flat = len(pcts) - up - dn
    seal, zb = [], []
    for r in rows:
        lp = limit_px(r["preClose"], cap(r["code"]))
        if r["latest"] >= lp - 0.005:
            seal.append((r["code"], r["name"], r["pct"]))
        elif r["high"] >= lp - 0.005:
            zb.append((r["code"], r["name"], round(r["pct"], 2), round((r["latest"] / lp - 1) * 100, 2)))
    return {
        "ts": fr["ts"], "n": len(rows), "up": up, "dn": dn, "flat": flat,
        "median": round(statistics.median(pcts), 2),
        "mean": round(statistics.mean(pcts), 2),
        "seal": len(seal), "seal_list": seal,
        "zb": len(zb), "zb_list": zb,
        "zb_rate": round(len(zb) / (len(seal) + len(zb)) * 100, 1) if (seal or zb) else None,
    }


targets = {"09:47": "09:47", "10:00": "10:00", "11:00": "11:00", "11:30": "11:30",
           "13:30": "13:30", "14:00": "14:00", "14:15": "14:15", "14:30": "14:30",
           "14:33": "14:33", "14:45": "14:45"}
out = {}
for label, hhmm in targets.items():
    cand = [f for f in frames if f["ts"][11:16] == hhmm]
    if not cand:
        cand = sorted(frames, key=lambda f: abs(int(f["ts"][14:16]) - int(hhmm[3:])))[:1]
    if cand:
        out[label] = frame_stats(cand[0])
out["LAST"] = frame_stats(frames[-1])

for k, v in out.items():
    print(f"{k:6s} ts={v['ts']} up={v['up']:2d} dn={v['dn']:2d} med={v['median']:6.2f} seal={v['seal']:2d} zb={v['zb']} zbrate={v['zb_rate']}")

last = out["LAST"]
print("\n=== LAST seal_list ===")
for s in last["seal_list"]:
    print(" ", s)
print("=== LAST zb_list ===")
for s in last["zb_list"]:
    print(" ", s)

# 个股 Δ 14:33 -> LAST, 找跌≥2pp / ≥3pp
def rows_by(fr_label):
    fr = [f for f in frames if f["ts"] == out[fr_label]["ts"]][0]
    return {r["code"]: r for r in fr["rows"]}

a, b = rows_by("14:33"), rows_by("LAST")
deltas = []
for c in a:
    if c in b:
        deltas.append((c, b[c]["name"], round(a[c]["pct"], 2), round(b[c]["pct"], 2), round(b[c]["pct"] - a[c]["pct"], 2)))
deltas.sort(key=lambda x: x[4])
print("\n=== 14:33 -> LAST worst 8 ===")
for d in deltas[:8]:
    print(" ", d)
print("跌≥2pp:", sum(1 for d in deltas if d[4] <= -2), " 跌≥3pp:", sum(1 for d in deltas if d[4] <= -3))
print("涨≥2pp:", sum(1 for d in deltas if d[4] >= 2))

json.dump({"series": out, "deltas_1433_last": deltas},
          open(os.path.join(os.path.dirname(F), "_hb_f_series.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nsaved _hb_f_series.json")
