# -*- coding: utf-8 -*-
import csv, io, json, os, statistics
B = r"D:/股票数据/市场数据"
def rd(p):
    return list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
zt = rd(B + "/20261103/zt_pool.csv")
zb = rd(B + "/20261103/zb_pool.csv")
dt = rd(B + "/20261103/dt_pool.csv")
zt2 = rd(B + "/20261102/zt_pool.csv")
out = {}
out["today_n"] = len(zt); out["zb_n"] = len(zb); out["dt_n"] = len(dt); out["y_n"] = len(zt2)

# 首封分布
def bucket(t):
    t = str(t).zfill(6)
    hhmm = int(t[:4])
    if hhmm <= 925: return "一字≤9:25"
    if hhmm <= 931: return "秒板≤9:31"
    if hhmm <= 1000: return "早盘≤10:00"
    if hhmm <= 1400: return "盘中10-14"
    return "尾盘>14"
from collections import Counter
c = Counter(bucket(r["首次封板时间"]) for r in zt)
out["首封分布"] = dict(c)
# 一字严格：首封<=0925 且 炸板0
yz = [r for r in zt if int(str(r["首次封板时间"]).zfill(6)[:4]) <= 925 and int(float(r["炸板次数"])) == 0]
out["一字数_严格"] = len(yz); out["一字_名单"] = [(r["代码"], r["名称"]) for r in yz]
# 连板分布
lb = Counter(int(float(r["连板数"])) for r in zt)
out["连板分布"] = dict(sorted(lb.items()))
out["二板加"] = sum(v for k, v in lb.items() if k >= 2)
# 昨日连板分布
lb2 = Counter(int(float(r["连板数"])) for r in zt2)
out["昨日连板分布"] = dict(sorted(lb2.items()))
# 晋级
s_y = {r["代码"]: int(float(r["连板数"])) for r in zt2}
s_t = {r["代码"]: int(float(r["连板数"])) for r in zt}
y_first = sum(1 for v in s_y.values() if v == 1)
y_ge2 = sum(1 for v in s_y.values() if v >= 2)
t_ge2 = sum(1 for v in s_t.values() if v >= 2)
out["一进二率"] = round(100.0 * sum(1 for c_, v in s_t.items() if v == 2 and c_ in s_y and s_y[c_] == 1) / y_first, 1)
out["昨日首板数"] = y_first; out["昨日2板加"] = y_ge2
out["昨日2板及以上今日继续涨停"] = sum(1 for c_, v in s_y.items() if v >= 2 and c_ in s_t)
out["二进三率"] = round(100.0 * sum(1 for c_, v in s_t.items() if v == 3 and c_ in s_y and s_y[c_] == 2) / max(1, sum(1 for v in s_y.values() if v == 2)), 1)
out["三进四以上率"] = round(100.0 * sum(1 for c_, v in s_t.items() if v >= 4 and c_ in s_y and s_y[c_] == 3) / max(1, sum(1 for v in s_y.values() if v == 3)), 1)
out["四进五率"] = round(100.0 * sum(1 for c_, v in s_t.items() if v >= 5 and c_ in s_y and s_y[c_] == 4) / max(1, sum(1 for v in s_y.values() if v == 4)), 1)
# 换手桶 / 封单比桶 今日
def bucket_turn(x):
    x = float(x)
    if x >= 20: return "≥20%"
    if x >= 10: return "10-20%"
    if x >= 3: return "3-10%"
    return "<3%"
out["今日换手桶"] = dict(Counter(bucket_turn(r["换手率"]) for r in zt))
# 封单比 = 封板资金 / 流通市值 *100
def fdb(r):
    return float(r["封板资金"]) / float(r["流通市值"]) * 100
out["今日封单比桶"] = dict(Counter(
    ("超强≥4%" if fdb(r) >= 4 else "强2-4%" if fdb(r) >= 2 else "中1-2%" if fdb(r) >= 1 else "偏弱0.5-1%" if fdb(r) >= 0.5 else "弱<0.5%") for r in zt))
out["今日封单比中位"] = round(statistics.median(fdb(r) for r in zt), 3)
out["今日封单总额亿"] = round(sum(float(r["封板资金"]) for r in zt) / 1e8, 2)
out["今日市值≥100亿只数"] = sum(1 for r in zt if float(r["流通市值"]) / 1e8 >= 100)
out["今日市值≥100亿名单"] = [(r["代码"], r["名称"], round(float(r["流通市值"]) / 1e8, 0)) for r in zt if float(r["流通市值"]) / 1e8 >= 100]
out["跌停市值≥100亿只数"] = sum(1 for r in dt if float(r["流通市值"]) / 1e8 >= 100)
out["跌停市值≥100亿名单"] = [(r["代码"], r["名称"], round(float(r["流通市值"]) / 1e8, 0)) for r in dt if float(r["流通市值"]) / 1e8 >= 100]
out["炸板市值≥100亿只数"] = sum(1 for r in zb if float(r["流通市值"]) / 1e8 >= 100)
out["炸板市值≥100亿名单"] = [(r["代码"], r["名称"], round(float(r["流通市值"]) / 1e8, 0)) for r in zb if float(r["流通市值"]) / 1e8 >= 100]
# 跌停行业
out["跌停行业"] = dict(Counter(r["所属行业"] for r in dt))
# 昨日125只今日执1（开→收）与gap 实测
bars = {}
def load(code):
    p = B + "/_学习/_bars_cache/%s.csv" % code
    if not os.path.exists(p): return None
    rows = [l.split(",") for l in io.open(p, encoding="utf-8-sig").read().strip().splitlines()]
    d = {}
    for r in rows:
        if len(r) < 5: continue
        try:
            d[r[0]] = (float(r[1]), float(r[2]), float(r[3]), float(r[4]))  # open,high,low,close
        except ValueError:
            continue
    return d
ex1, gaps, miss = [], [], []
for r in zt2:
    b = load(r["代码"])
    if not b or "2026-11-02" not in b or "2026-11-03" not in b:
        miss.append(r["代码"]); continue
    o2, o3, c2, c3 = b["2026-11-02"][0], b["2026-11-03"][0], b["2026-11-02"][3], b["2026-11-03"][3]
    ex1.append((c3 / o3 - 1) * 100)
    gaps.append((o3 / c2 - 1) * 100)
out["昨日池今日执1_均收"] = round(sum(ex1) / len(ex1), 2) if ex1 else None
out["昨日池今日执1_胜率"] = round(100.0 * sum(1 for x in ex1 if x > 0) / len(ex1), 1) if ex1 else None
out["昨日池今日gap_中位"] = round(statistics.median(gaps), 2) if gaps else None
out["昨日池今日gap>3%占比"] = round(100.0 * sum(1 for g in gaps if g > 3) / len(gaps), 1) if gaps else None
out["昨日池结算样本"] = len(ex1); out["缺bar"] = miss
# 昨日荐票逐票结算
for code in ["002172", "001219", "600259"]:
    b = load(code)
    if not b: out["settle_" + code] = "no bar"; continue
    o2, c2 = b["2026-11-02"][0], b["2026-11-02"][3]
    o3, c3 = b["2026-11-03"][0], b["2026-11-03"][3]
    out["settle_" + code] = {"1103gap": round((o3 / c2 - 1) * 100, 2), "执1": round((c3 / o3 - 1) * 100, 2),
                             "执2": round((c3 / o2 - 1) * 100, 2), "1103close": c3}
# 今日池按换手≥20 + 质量分
qr = json.load(io.open(B + "/_学习/涨停质量荐票_20261103.json", encoding="utf-8-sig"))
rows = qr["明细"]
for r in rows:
    r["_fdb"] = round(fdb({"封板资金": 0, "流通市值": 1}), 3)
out["top5"] = [(r["代码"], r["名称"], r["质量分"], r["换手"], r["封单比"], r["预测执1胜率"], r["预测执1均涨"], r["预测执2胜率"], r["预测执2均涨"]) for r in qr["top5"]]
out["全池预测执1_max"] = max(r["预测执1胜率"] for r in rows)
out["全池预测执1_中位"] = statistics.median(r["预测执1胜率"] for r in rows)
out["全池预测执1均涨_max"] = max(r["预测执1均涨"] for r in rows)
out["全池预测执2_max"] = max(r["预测执2胜率"] for r in rows)
out["换手≥20名单"] = [(r["代码"], r["名称"], round(r["换手"], 2), r["连板"], r["质量分"]) for r in rows if r["换手"] >= 20]
out["换手10-20数"] = sum(1 for r in rows if 10 <= r["换手"] < 20)
out["换手3-10数"] = sum(1 for r in rows if 3 <= r["换手"] < 10)
out["换手<3数"] = sum(1 for r in rows if r["换手"] < 3)
print(json.dumps(out, ensure_ascii=False, indent=1))
