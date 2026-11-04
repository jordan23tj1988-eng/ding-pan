# -*- coding: utf-8 -*-
"""hb-e 分析: ticks 广度/跳水阈值 + 池内读数 + 独立源指数校验"""
import json, datetime, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261104"

# ---------- 1. ticks 分析 ----------
frames = []
for line in open(D + r"\realtime_ticks.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        j = json.loads(line)
    except Exception:
        continue
    frames.append(j)

today = "2026-11-04"
fr = [f for f in frames if f.get("ts", "").startswith(today) and f.get("rows")]
print("今日帧数", len(fr), "首帧", fr[0]["ts"], "末帧", fr[-1]["ts"], "池", len(fr[-1]["rows"]), "pool_date", fr[-1].get("pool_date"))
ts = [datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") for f in fr]
gaps = [(ts[i+1]-ts[i]).total_seconds() for i in range(len(ts)-1)]
print("帧间隔 中位", sorted(gaps)[len(gaps)//2], "最大空档", max(gaps))


def breadth(f):
    r = f["rows"]
    p = [x["pct"] for x in r if x.get("pct") is not None]
    s = {
        "ts": f["ts"], "n": len(r), "red": sum(1 for x in p if x > 0), "green": sum(1 for x in p if x < 0),
        "up97": sum(1 for x in p if x >= 9.7), "dn3": sum(1 for x in p if x <= -3), "dn8": sum(1 for x in p if x <= -8),
        "mean": round(sum(p)/len(p), 2), "median": round(sorted(p)[len(p)//2], 2),
    }
    return s

for f in fr:
    if f["ts"][11:16] in ("09:31", "10:37", "11:05", "13:00", "13:38", "14:00", "14:10", "14:20", "14:25", "14:30", "14:31", "14:32"):
        print("BREADTH", breadth(f))

# 跳水阈值: 相邻两帧 pct 差 <= -3pp 的家数 (同一窗口 >=3 只)
def dmap(f):
    return {x["code"]: x["pct"] for x in f["rows"] if x.get("pct") is not None}

hits = []
for i in range(len(fr)-2):
    a, b = dmap(fr[i]), dmap(fr[i+2])
    cnt = 0
    worst = 0
    worstc = None
    for c, p in b.items():
        if c in a:
            d = p - a[c]
            if d <= -3:
                cnt += 1
            if d < worst:
                worst, worstc = d, c
    if cnt >= 3:
        hits.append((fr[i]["ts"], fr[i+2]["ts"], cnt, worst, worstc))
print("2分钟窗(>=3只 -3pp) 命中窗数", len(hits), hits[:5])

# 13:30 以来 单票最大 2 分钟跌幅
seg = [(i) for i in range(len(fr)-2) if fr[i]["ts"] >= today + " 13:30"]
mx = None
for i in seg:
    a, b = dmap(fr[i]), dmap(fr[i+2])
    for c, p in b.items():
        if c in a:
            d = p - a[c]
            if mx is None or d < mx[0]:
                nm = next((x["name"] for x in fr[i+2]["rows"] if x["code"] == c), c)
                mx = (round(d, 2), c, nm, fr[i]["ts"], fr[i+2]["ts"], a[c], p)
print("13:30后单票最大2分钟跌幅", mx)

# 最近 30 分钟池内变动
f0 = next(f for f in fr if f["ts"] >= today + " 14:00")
print("14:00 vs 末帧:", breadth(f0), breadth(fr[-1]))

# ---------- 2. 独立源指数校验 (新浪) ----------
try:
    u = "https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,s_sh000688"
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "replace")
    print("=== 新浪指数 ===")
    for seg_ in raw.strip().split(";"):
        if "=" in seg_:
            print(seg_.strip())
except Exception as e:
    print("sina err", repr(e))

# ---------- 3. 池内 zt 复核 (002652 / 600261 / 603906) ----------
pools = json.load(open(D + r"\_hb_e_pools_1430.json", encoding="utf-8"))
zt = {x["c"]: x for x in pools["zt"]}
zb = {x["c"]: x for x in pools["zb"]}
for c in ("002652", "600261", "603906", "002292"):
    print("POOL", c, "zt" if c in zt else ("zb" if c in zb else "none"),
          zt.get(c) or zb.get(c))
