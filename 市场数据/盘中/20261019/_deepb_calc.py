import json, os, statistics, urllib.request, datetime, csv

BASE = r"D:\股票数据\市场数据"
D = os.path.join(BASE, "盘中", "20261019")
os.chdir(D)

# ---------- 1. 交易日校验证据链 ----------
frames = []
for line in open("realtime_ticks.jsonl", encoding="utf-8"):
    fr = json.loads(line)
    frames.append(fr)
first_ts, last_ts = frames[0]["ts"], frames[-1]["ts"]
gaps = []
for a, b in zip(frames, frames[1:]):
    ta = datetime.datetime.strptime(a["ts"], "%Y-%m-%d %H:%M:%S")
    tb = datetime.datetime.strptime(b["ts"], "%Y-%m-%d %H:%M:%S")
    gaps.append((tb - ta).total_seconds())
maxgap = max(gaps)

# ---------- 2. 池内截面（封板=最新价≥板块涨停价） ----------
def limit_px(pre, code):
    r = 0.2 if code.startswith(("30", "68")) else 0.1
    return round(pre * (1 + r), 2)

def snap(fr):
    rs = fr["rows"]; p = [r["pct"] for r in rs]
    sealed = [r for r in rs if r["latest"] >= limit_px(r["preClose"], r["code"]) - 0.001]
    touched = [r for r in rs if r["high"] >= limit_px(r["preClose"], r["code"]) - 0.001]
    dn = [r for r in rs if r["pct"] <= -9.8]
    return dict(ts=fr["ts"], n=len(rs), 封板=len(sealed), 触板=len(touched),
                炸板=len(touched) - len(sealed),
                池内再封率=round(len(sealed) / len(touched), 3),
                中位=round(statistics.median(p), 2), 均值=round(sum(p) / len(p), 2),
                涨=len([x for x in p if x > 0]), 跌=len([x for x in p if x < 0]),
                跌gt5=len([x for x in p if x <= -5]), 跌gt8=len([x for x in p if x <= -8]),
                跌停=[[r["code"], r["name"], r["pct"]] for r in dn],
                封板票=[[r["code"], r["name"], r["pct"]] for r in sealed],
                炸板票=[[r["code"], r["name"], r["pct"]] for r in touched if r not in sealed])

by_min = {fr["ts"][11:16]: fr for fr in frames}
S = {k: snap(by_min[k]) for k in ("14:37", "14:45", "14:54") if k in by_min}
last = frames[-1]

# ---------- 3. 持仓行情（池内帧 + 腾讯直取） ----------
hold = {"600668": ("尖峰集团", 6100, 8.15, 49739.86), "000601": ("韶能股份", 6000, 6.68, 40100.04),
        "000823": ("超声电子", 800, 25.13, 20114.05)}
raw = urllib.request.urlopen("http://qt.gtimg.cn/q=sh600668,sz000601,sz000823", timeout=10).read().decode("gbk")
q = {}
for seg in raw.split(";"):
    if "=" not in seg:
        continue
    f = seg.split('"')[1].split("~")
    q[f[2]] = dict(name=f[1], last=float(f[3]), pct=float(f[32]), open=float(f[5]), high=float(f[33]),
                   low=float(f[34]), ts=f[30], amt_wan=float(f[37]), bid1=float(f[9]), ask1=float(f[19]))
fetch_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 600668 tick 轨迹
t6 = [(fr["ts"], [r for r in fr["rows"] if r["code"] == "600668"][0]) for fr in frames]
t6 = [(ts, r["latest"], r["high"], r["low"]) for ts, r in t6]

# MA
def ma(code, n):
    rows = [r for r in csv.reader(open(f"{BASE}/_学习/_bars_cache/{code}.csv", encoding="utf-8")) if r and r[0][:2] == "20"]
    c = [float(r[4]) for r in rows]
    return round(sum(c[-n:]) / n, 3), rows[-1][0]

out = dict(
    date="20261019",
    生成时刻=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    实时帧=dict(首帧=first_ts, 末帧=last_ts, 帧数=len(frames), 最大间隔秒=maxgap,
        源=last["src"], n=last["n"], pool_date=last["pool_date"], pool_stale=last["pool_stale"]),
    池内截面=S,
    腾讯直取=dict(取数时刻=fetch_at, 行情戳={k: v["ts"] for k, v in q.items()}, rows=q),
    持仓=({k: dict(name=v[0], shares=v[1], buy_px=v[2], cost=v[3],
                  last=q[k]["last"], pct=q[k]["pct"], high=q[k]["high"], low=q[k]["low"],
                  市值=round(v[1] * q[k]["last"], 2),
                  浮盈=round(v[1] * q[k]["last"] - v[3], 2),
                  相对成本pct=round((q[k]["last"] - v[2]) / v[2] * 100, 2)) for k, v in hold.items()}),
    尖峰600668轨迹=t6[-14:],
    MA=dict(m600668=ma("600668", 10), m000601=ma("000601", 10), m000823=ma("000823", 20)),
)
json.dump(out, open("_deepb_calc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("实时帧", "池内截面", "腾讯直取", "持仓", "MA")}, ensure_ascii=False, indent=1))
