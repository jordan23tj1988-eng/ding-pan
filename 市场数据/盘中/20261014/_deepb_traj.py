# -*- coding: utf-8 -*-
"""深场B 预收盘复盘辅助: 只读, 输出日内轨迹(池中位/封板/涨跌)与线级统计。"""
import json, statistics as st

P = r"D:\股票数据\市场数据\盘中\20261014\realtime_ticks.jsonl"
CUT = "2026-10-14 14:45:00"
frames = [json.loads(l) for l in open(P, encoding="utf-8") if l.strip()]
legal = [f for f in frames if f["ts"] <= CUT]

def zt(r):
    lim = 0.20 if r["code"].startswith(("300", "301", "688")) else 0.10
    return round(r["preClose"] * (1 + lim), 2)

def rowat(ts):
    for f in legal:
        if f["ts"][11:16] == ts:
            return f
    return None

print("| 时点 | 中位 | 均值 | 涨/跌 | 封板 | 炸板 | 跌停 |")
print("|---|---|---|---|---|---|---|")
for ts in ["09:31", "09:40", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:15", "14:30", "14:44"]:
    f = rowat(ts)
    if not f:
        print(ts, "无帧"); continue
    rs = f["rows"]
    pcts = [r["pct"] for r in rs]
    seal = sum(1 for r in rs if r["latest"] >= zt(r) - 1e-9)
    zb = sum(1 for r in rs if r["high"] >= zt(r) - 1e-9 and r["latest"] < zt(r) - 1e-9)
    dt = sum(1 for r in rs if r["pct"] <= -9.8)
    up = sum(1 for r in pcts if r > 0); dn = sum(1 for r in pcts if r < 0)
    print(f"| {ts} | {round(st.median(pcts),2)} | {round(sum(pcts)/len(pcts),3)} | {up}/{dn} | {seal} | {zb} | {dt} |")

# 线级@末帧
LX = {
 "AI漫剧": ["002343", "603096", "605577"],
 "数据中心温控": ["600202", "000530", "002639"],
 "PCB": ["000823", "605058", "605258", "603328", "603386", "603956", "301041", "002579", "688655", "600237", "002623"],
 "冰雪经济": ["601188", "000715", "301010", "600593", "600853", "603099", "002878", "000558"],
 "出版": ["605577", "603096", "600825"],
}
last = legal[-1]
S = {r["code"]: r for r in last["rows"]}
print("\n| 线 | n(在池) | 封板 | 炸板 | 中位 | 均值 | 最强 | 最弱 |")
print("|---|---|---|---|---|---|---|---|")
for k, cs in LX.items():
    mem = [S[c] for c in cs if c in S]
    if not mem: continue
    pcts = [m["pct"] for m in mem]
    seal = sum(1 for m in mem if m["latest"] >= zt(m) - 1e-9)
    zb = sum(1 for m in mem if m["high"] >= zt(m) - 1e-9 and m["latest"] < zt(m) - 1e-9)
    mx = max(mem, key=lambda m: m["pct"]); mn = min(mem, key=lambda m: m["pct"])
    print(f"| {k} | {len(mem)} | {seal} | {zb} | {round(st.median(pcts),2)} | {round(sum(pcts)/len(pcts),2)} | {mx['name']}{mx['pct']:+.2f} | {mn['name']}{mn['pct']:+.2f} |")

# 关窗前后对照: 600825 是否仍零成交退化
for c in ("600825",):
    r = S.get(c)
    print("\n", c, r["name"] if r else "不在池", r)
