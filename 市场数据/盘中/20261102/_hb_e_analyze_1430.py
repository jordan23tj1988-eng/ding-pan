# -*- coding: utf-8 -*-
import json, os, datetime, glob
D = r"D:\股票数据\市场数据"
os.chdir(D)
now = datetime.datetime.now()
fr = [json.loads(l) for l in open("盘中/20261102/realtime_ticks.jsonl", encoding="utf-8")]
last = fr[-1]
age = (now - datetime.datetime.strptime(last["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds()
print("last_frame", last["ts"], "age_s", round(age), "frames", len(fr), "pool_n", len(last["rows"]), "pool_date", last.get("pool_date"), "stale", last.get("pool_stale"))
# gaps
gaps = []
for a, b in zip(fr, fr[1:]):
    ta = datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")
    tb = datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S")
    if (tb - ta).total_seconds() > 130:
        gaps.append((a["ts"], b["ts"], (tb - ta).total_seconds()))
print("gaps>130s", gaps)

def st(d):
    rows = {r["code"]: r for r in d["rows"]}
    p = [r["pct"] for r in rows.values()]
    return dict(ts=d["ts"], up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                flat=sum(1 for x in p if x == 0),
                ge97=sum(1 for x in p if x >= 9.7), le3=sum(1 for x in p if x <= -3),
                avg=round(sum(p) / len(p), 2))

for tag, lo in (("13:00", "2026-11-02 13:00"), ("13:32", "2026-11-02 13:30"), ("14:00", "2026-11-02 14:00"), ("14:32", "2026-11-02 14:30")):
    seg = [d for d in fr if d["ts"] >= lo]
    if seg:
        print(tag, st(seg[0]), "|end", st(seg[-1]))

aft = [d for d in fr if d["ts"] >= "2026-11-02 13:00"]
dz = 0
worst = (0.0, None)
win_hits = []
for i in range(1, len(aft)):
    pr = {r["code"]: r for r in aft[i - 1]["rows"]}
    cu = {r["code"]: r for r in aft[i]["rows"]}
    c3 = 0
    for c, r in cu.items():
        if c not in pr:
            continue
        dd = r["pct"] - pr[c]["pct"]
        if dd <= -3:
            c3 += 1
        if dd < worst[0]:
            worst = (dd, (aft[i]["ts"], r["name"], round(dd, 2), round(r["pct"], 2)))
    if c3 >= 3:
        dz += 1
        win_hits.append((aft[i]["ts"], c3))
print("nwin_1300_1432", len(aft) - 1, "dz_windows", dz, win_hits, "worst", worst)

# 单票 13:32 -> 14:32 跌幅榜 与 涨幅榜
def snap(lo):
    seg = [d for d in fr if d["ts"] >= lo]
    return {r["code"]: r for r in seg[0]["rows"]} if seg else {}
old = {r["code"]: r for r in [d for d in fr if d["ts"] >= "2026-11-02 13:30"][0]["rows"]}
new = {r["code"]: r for r in last["rows"]}
delta = sorted(((new[c]["pct"] - old[c]["pct"], c, new[c]["name"], old[c]["pct"], new[c]["pct"]) for c in old if c in new), key=lambda x: x[0])
print("worst5_1332_to_1432", [(round(x[0], 2), x[1], x[2], x[3], x[4]) for x in delta[:6]])
print("best5_1332_to_1432", [(round(x[0], 2), x[1], x[2], x[3], x[4]) for x in delta[-6:]])
# 今日涨停/跌停池内状态
print("pool_ge97", [(r["code"], r["name"], r["pct"]) for r in last["rows"] if r["pct"] >= 9.7])
# watch three
for c in ("301132", "601083", "301520", "002365", "001287"):
    r = new.get(c)
    print("watch", c, r["name"], r["latest"], r["pct"], "high", r["high"], "low", r["low"], "open", r["open"])

# 文件存在性
for p in ("盘中/20261102/pulse.json", "盘中/20261102/warboard.json", "盘中/20261102/执行流水.jsonl"):
    print("exists", p, os.path.exists(p))
for g in glob.glob("盘中/20261102/*执行*") + glob.glob("**/执行流水*.jsonl", recursive=True)[:5]:
    print("found", g, datetime.datetime.fromtimestamp(os.path.getmtime(g)))
for p in ("_学习/_模拟盘/master/state.json", "_学习/_模拟盘/盘中作战/state.json"):
    if os.path.exists(p):
        s = json.load(open(p, encoding="utf-8"))
        print(p, "mtime", datetime.datetime.fromtimestamp(os.path.getmtime(p)), "cash", s.get("cash"), "pos", len(s.get("positions") or s.get("持仓") or []))
