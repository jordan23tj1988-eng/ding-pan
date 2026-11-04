# -*- coding: utf-8 -*-
"""20261029 连板梯队/晋级率/昨停溢价 复算 + 周期投票所需输入"""
import csv, io, json, os, collections

BASE = r"D:\股票数据\市场数据"
D, DP = "20261029", "20261028"


def pool(d):
    p = os.path.join(BASE, d, "zt_pool.csv")
    rows = list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
    out = []
    for r in rows:
        name = (r.get("名称") or "")
        if "ST" in name or "退" in name:
            continue
        try:
            n = int(float(r.get("连续涨停天数") or r.get("涨停天数") or 0))
        except Exception:
            n = 0
        out.append({"code": (r.get("代码") or "").zfill(6), "name": name, "n": n,
                    "close": r.get("最新价") or r.get("收盘价"), "ind": r.get("所属行业")})
    return out


t, y = pool(D), pool(DP)
lad = collections.Counter(x["n"] for x in t)
print("今日涨停(剔ST)", len(t), "梯队", dict(sorted(lad.items(), reverse=True)))
print("昨日涨停(剔ST)", len(y), "昨梯队", dict(sorted(collections.Counter(x["n"] for x in y).items(), reverse=True)))
first_today = [x for x in t if x["n"] == 1]
two_plus_today = [x for x in t if x["n"] >= 2]
first_y = [x for x in y if x["n"] == 1]
two_y = [x for x in y if x["n"] == 2]
print("一进二率 = 今日2板+ %d / 昨日首板 %d = %.3f" % (len(two_plus_today), len(first_y), len(two_plus_today) / max(1, len(first_y))))
print("二进三率 = 今日3板+ %d / 昨日2板 %d = %.3f" % (len([x for x in t if x["n"] >= 3]), len(two_y), len([x for x in t if x["n"] >= 3]) / max(1, len(two_y))))
code2n = {x["code"]: x["n"] for x in t}
print("高标:", [(x["code"], x["name"], x["n"]) for x in t if x["n"] >= 3])

# 昨停溢价: 昨日涨停今日涨跌幅 均值
import subprocess
zt_y = {x["code"] for x in y}
# 从今日 zt/dt 池拿不到涨跌；用 bars_cache 或 全A日K
prem = None
try:
    kp = os.path.join(BASE, "_学习", "_全A日K", D + ".csv")
    if os.path.isfile(kp):
        px = {}
        for r in csv.DictReader(io.open(kp, encoding="utf-8-sig")):
            c = (r.get("code") or r.get("THSCODE") or r.get("thscode") or "").split(".")[0].zfill(6)
            px[c] = r
        vals = []
        for c in zt_y:
            r = px.get(c)
            if not r:
                continue
            try:
                ch = float(r.get("changeRatio") or r.get("chg") or 0)
            except Exception:
                continue
            vals.append(ch)
        if vals:
            prem = sum(vals) / len(vals)
            print("昨停溢价(全A日K changeRatio均值) n=%d 均值=%.2f%%" % (len(vals), prem))
except Exception as e:
    print("溢价计算失败", repr(e))

# 温度表近5日
tm = json.load(io.open(os.path.join(BASE, "_学习", "_市场温度表.json"), encoding="utf-8"))
for k in sorted(tm)[-6:]:
    v = tm[k]
    print("TEMP", k, {kk: v.get(kk) for kk in ("温度", "涨停家数", "两市成交额_亿", "最高板", "炸板率") if isinstance(v, dict)})

lead = json.load(io.open(os.path.join(BASE, "_学习", "_情绪先行指标.json"), encoding="utf-8"))
print("LEAD keys:", list(lead.get(D, {}).keys()))
print(json.dumps(lead.get(D, {}), ensure_ascii=False)[:1200])
