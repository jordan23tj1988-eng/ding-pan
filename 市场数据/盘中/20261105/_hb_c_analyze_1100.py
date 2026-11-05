# -*- coding: utf-8 -*-
"""hb-c 11:00 分析：宽度趋势 / 2分钟批量跳水 / 个股Δ / 持仓风险"""
import json, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261105"
allf = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
allf.sort(key=lambda f: f["ts"])
frames = allf
print("frames", len(frames), frames[0]["ts"], "->", frames[-1]["ts"], "rows", len(frames[-1]["rows"]))
# 帧间隔
gaps = []
for a, b in zip(frames, frames[1:]):
    ta = datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")
    tb = datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S")
    gaps.append((tb - ta).total_seconds())
print("max_gap_sec", max(gaps), "min_gap", min(gaps), "n_gaps>180", sum(1 for g in gaps if g > 180))

def snap(f):
    return {r["code"]: r for r in f["rows"]}

def near(t):
    tt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    return min(frames, key=lambda f: abs(datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - tt))

pts = ["09:31", "09:43", "09:55", "10:07", "10:19", "10:33", "10:45", "10:57", "11:01"]
width = []
for t in pts:
    f = near("2026-11-05 " + t + ":00")
    S = snap(f)
    p = sorted(x["pct"] for x in S.values())
    width.append({"帧": f["ts"], "n": len(p), "均涨": round(sum(p) / len(p), 2),
                  "中位": round(p[len(p) // 2], 2),
                  "红盘": sum(1 for v in p if v > 0), "绿盘": sum(1 for v in p if v < 0),
                  "贴板>=9.6": sum(1 for v in p if v >= 9.6), "破-3": sum(1 for v in p if v <= -3),
                  "破-8": sum(1 for v in p if v <= -8)})
for w in width:
    print(w)

PIN = frames[-1]["ts"]
# 2分钟窗批量跳水（10:20 起，本场窗口；同时给全场最大）
win = []
for i in range(2, len(frames)):
    if frames[i]["ts"] < "2026-11-05 10:20":
        continue
    S1, S2 = snap(frames[i - 2]), snap(frames[i])
    d = [(round(S2[c]["pct"] - S1[c]["pct"], 2), c, S2[c]["name"]) for c in S2 if c in S1]
    sub = [x for x in d if x[0] <= -3]
    win.append({"帧": frames[i]["ts"], "n-3pp": len(sub), "池均Δ": round(sum(x[0] for x in d) / len(d), 2),
                "票": [x[1] + x[2] for x in sub]})
print("win_n", len(win))
mx = max(win, key=lambda w: w["n-3pp"])
print("max_cnt_win", mx)
print("worst_by_mean", min(win, key=lambda w: w["池均Δ"]))
print("windows_with>=3", [w for w in win if w["n-3pp"] >= 3][:5])

# 个股Δ 10:33 → 末帧
A0 = snap(near("2026-11-05 10:33:00"))
L = snap(frames[-1])
delta = sorted([(round(L[c]["pct"] - A0[c]["pct"], 2), c, L[c]["name"], A0[c]["pct"], L[c]["pct"]) for c in L if c in A0])
print("delta_n", len(delta))
print("worst10", [(d[1], d[2], d[0], d[3], d[4]) for d in delta[:10]])
print("best5", [(d[1], d[2], d[0]) for d in delta[-5:]])
print("le-3pp", [(d[1], d[2], d[0]) for d in delta if d[0] <= -3])
print("ge3pp", [(d[1], d[2], d[0]) for d in delta if d[0] >= 3])

# 持仓逐只：全程最低/最高 pct，最近2分钟Δ
POS = ["600299", "600259", "603906", "002292"]
for c in POS:
    ser = [(f["ts"], snap(f)[c]["pct"], snap(f)[c]["px"]) for f in frames if c in snap(f)]
    if not ser:
        print("POS", c, "不在昨日涨停池(116只)内 → 分时改用东财")
        continue
    lo = min(ser, key=lambda x: x[1]); hi = max(ser, key=lambda x: x[1])
    print("POS", c, ser[-1], "low", lo, "high", hi, "last2m_delta", round(ser[-1][1] - ser[-3][1], 2) if len(ser) >= 3 else None)

# 涨停池/炸板池 是否含持仓
pools = json.load(open(os.path.join(D, "_hb_c_pools_1100.json"), encoding="utf-8"))
ztset = {x["c"] for x in pools["zt"]}
zbset = {x["c"] for x in pools["zb"]}
print("pos in zt", [c for c in POS if c in ztset], "pos in zb", [c for c in POS if c in zbset])
print("zb_codes", [(x["c"], x["n"], round(x["zdp"], 2), x.get("hybk")) for x in pools["zb"]])
json.dump({"width": width, "pin": PIN, "win": win[-12:], "max_cnt_win": mx,
           "delta": delta[:20]}, open(os.path.join(D, "_hb_c_analyze_1100.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
