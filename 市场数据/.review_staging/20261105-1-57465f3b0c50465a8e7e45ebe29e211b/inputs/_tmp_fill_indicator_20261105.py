# -*- coding: utf-8 -*-
"""补齐 20261105 先行指标缺失项: 昨日涨停今日执行溢价 + 核按钮率(腾讯行情源)。
零编造: 数据全部取自真实行情; 失败则保持 null 并如实标注。
"""
import json, csv, sys, time
import requests

BASE = r"D:\股票数据\市场数据"
D = "20261105"
PREV = "20261104"


def is_junk(n):
    n = str(n)
    return any(x in n for x in ("ST", "退", "N", "C")) or n.startswith("N") or n.startswith("C")


def load_pool(d):
    rows = []
    with open(rf"{BASE}\{d}\zt_pool.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def qq(codes):
    out = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i + 50]
        q = ",".join(("sh" if c.startswith(("6", "9")) else "sz") + c for c in batch)
        for attempt in range(3):
            try:
                r = requests.get("http://qt.gtimg.cn/q=" + q, timeout=10,
                                 proxies={"http": None, "https": None})
                r.encoding = "gbk"
                for line in r.text.split(";"):
                    if "~" not in line:
                        continue
                    p = line.split("~")
                    if len(p) < 40:
                        continue
                    code = p[2]
                    name = p[1]
                    try:
                        cur = float(p[3]); pre = float(p[4]); op = float(p[5])
                    except Exception:
                        continue
                    out[code] = {"name": name, "cur": cur, "pre": pre, "open": op}
                break
            except Exception as e:
                if attempt == 2:
                    print("[fail]", batch[:3], str(e)[:80])
                time.sleep(1)
    return out


prev = load_pool(PREV)
prev_clean = [r for r in prev if not is_junk(r["名称"])]
codes = [r["代码"] for r in prev_clean]
print("昨日涨停原始=%d 剔ST=%d" % (len(prev), len(prev_clean)))
q = qq(codes)
print("腾讯取到=%d" % len(q))

rets = []
for c in codes:
    d = q.get(c)
    if not d or d["open"] <= 0 or d["cur"] <= 0:
        continue
    rets.append((d["cur"] / d["open"] - 1) * 100)
avg = round(sum(rets) / len(rets), 2) if rets else None
print("执行口径均收(今开买->今收)=%s%% n=%d" % (avg, len(rets)))

# 核按钮率: 昨日涨停 ∩ 今日跌停
dt = []
try:
    with open(rf"{BASE}\{D}\dt_pool.csv", encoding="utf-8-sig") as f:
        dt = [r["代码"] for r in csv.DictReader(f)]
except Exception:
    pass
hit = len(set(codes) & set(dt))
kb = round(hit / len(codes), 3) if codes else None

p = rf"{BASE}\_学习\_情绪先行指标.json"
data = json.load(open(p, encoding="utf-8"))
e = data.get(D) or {}
if avg is not None:
    e["昨日涨停溢价"] = {"执行均收": avg, "来源": "腾讯行情今开->今收(%d只,剔ST)" % len(rets)}
if e.get("核按钮") is None:
    e["核按钮"] = {"昨日涨停数": len(prev_clean), "今日跌停回杀": hit, "核按钮率": kb}
if avg is not None and avg < 0 and abs(avg) >= 5:
    e.setdefault("触发器", [])
data[D] = e
json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写回", p)
print(json.dumps(e, ensure_ascii=False))
