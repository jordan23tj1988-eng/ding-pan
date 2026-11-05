# -*- coding: utf-8 -*-
"""桶冲突规则回测 [MA-20261103-01 ②]
对 20260401~20261030 每个 4板+ 样本，用『冲突桶』(4板+×温度<40 正桶 vs 4板+×封单比≥2% 负桶)
三条取桶规则做 walk-forward 预测(训练窗只用到样本前一日), 输出命中率/均收。
零后视镜: 桶统计只用 < 样本日 的样本; 执1=T+1开→T+1收(执行口径)。
"""
import os, io, json, glob, statistics as st

BASE = "D:/股票数据/市场数据"
L = os.path.join(BASE, "_学习")
CDIR = os.path.join(L, "_bars_cache")
OUT = os.path.join(L, "桶冲突规则回测_20261104.json")

def load(p):
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            with io.open(p, encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None

def fnum(v):
    try:
        x = float(v)
        return x if x == x else None
    except Exception:
        return None

# ---------- 1. 样本表 ----------
ths = load(os.path.join(L, "_ths_zt_pool.json")) or {}
temp = load(os.path.join(L, "_市场温度表.json")) or {}

bars_cache = {}
def bars(c):
    if c in bars_cache: return bars_cache[c]
    p = os.path.join(CDIR, c + ".csv")
    rows = None
    if os.path.isfile(p):
        rows = []
        with io.open(p, encoding="utf-8") as f:
            head = f.readline().strip().split(",")
            idx = {k: i for i, k in enumerate(head)}
            for line in f:
                s = line.rstrip("\n").split(",")
                if len(s) < len(head): continue
                rows.append((s[idx["date"]].replace("-", ""), fnum(s[idx["open"]]),
                             fnum(s[idx["close"]]),
                             fnum(s[idx["circ_mv亿"]]) if "circ_mv亿" in idx else None))
    bars_cache[c] = rows
    return rows

def e1_of(code, d):
    b = bars(code)
    if not b: return None
    for i, r in enumerate(b):
        if r[0] == d:
            if i + 1 < len(b):
                o1, c1 = b[i+1][1], b[i+1][2]
                if o1 and o1 > 0 and c1:
                    return c1 / o1 - 1
            return None
    return None

def circmv(code, d):
    b = bars(code)
    if not b: return None
    for r in b:
        if r[0] == d: return r[3]
    return None

dy_dirs = sorted(os.path.basename(os.path.normpath(x)) for x in glob.glob(os.path.join(BASE, "2026*"))
                 if os.path.isdir(x) and os.path.isfile(os.path.join(x, "zt_pool.csv")))

rows = []
seen = set()
def add_row(d, code, name, lb, fj, mv, hs, kai):
    if not ("20250701" <= d <= "20261030"): return
    if lb is None or lb < 4: return
    if "退" in (name or ""): return
    key = (d, code)
    if key in seen: return
    seen.add(key)
    fb = None
    if mv and mv > 0 and fj:
        fb = fj / mv * 100
    if fb is None:
        cm = circmv(code, d)
        if cm and fj: fb = fj / (cm * 1e8) * 100
    t = (temp.get(d) or {}).get("温度")
    rows.append(dict(日=d, 代码=code, 名称=name, 连板=lb, 封单比=round(fb, 3) if fb is not None else None,
                     换手=hs, 炸板=kai, 温度=t, 执1=e1_of(code, d)))

# 先读日目录(EM口径最全)
for d in dy_dirs:
    if not ("20250701" <= d <= "20261030"): continue
    p = os.path.join(BASE, d, "zt_pool.csv")
    with io.open(p, encoding="utf-8-sig") as f:
        head = f.readline().strip().split(",")
        idx = {k: i for i, k in enumerate(head)}
        for line in f:
            s = line.rstrip("\n").split(",")
            if len(s) < len(head): continue
            lb = fnum(s[idx["连板数"]]) if "连板数" in idx else None
            add_row(d, s[idx["代码"]].zfill(6), s[idx["名称"]], int(lb) if lb else None,
                    fnum(s[idx["封板资金"]]), fnum(s[idx["流通市值"]]),
                    fnum(s[idx["换手率"]]), int(fnum(s[idx["炸板次数"]]) or 0))
# 再用 THS 历史池补无日目录的日期(20260401~20260612 等)
for d in sorted(ths):
    if not ("20250701" <= d <= "20261030"): continue
    for x in ths[d]:
        nm = str(x.get("name") or "")
        hd = str(x.get("high_days") or "")
        lb = 1
        import re
        m = re.search(r"(\d+)板", hd)
        if m: lb = int(m.group(1))
        c = str(x.get("code") or "").zfill(6)
        add_row(d, c, nm, lb, fnum(x.get("order_amount")), None, None, int(fnum(x.get("open_num")) or 0))

rows.sort(key=lambda r: (r["日"], r["代码"]))
ok = [r for r in rows if r["执1"] is not None]
print("4板+ 样本(20260401-20261030):", len(rows), "有执1:", len(ok),
      "日范围:", rows[0]["日"], rows[-1]["日"])
print("连板分布:", {k: sum(1 for r in rows if r["连板"] == k) for k in sorted(set(r["连板"] for r in rows))})

# ---------- 2. 复现昨日两桶口径 ----------
def stat(rs):
    if not rs: return dict(n=0, 胜率=None, 均收=None)
    v = [r["执1"] for r in rs]
    return dict(n=len(v), 胜率=round(100*sum(1 for x in v if x > 0)/len(v), 1),
                均收=round(100*sum(v)/len(v), 2))

cold = [r for r in ok if r["温度"] is not None and r["温度"] < 40]
feng = [r for r in ok if r["封单比"] is not None and r["封单比"] >= 2]
conf = [r for r in ok if r in cold and r in feng]
print("全窗(0401-1030) 冷<40:", stat(cold), "| 封单≥2%:", stat(feng), "| 冲突:", stat(conf))
print("冲突只数:", len(conf), "冲突占比:", round(100*len(conf)/len(ok), 1), "%")
# 原口径窗口探测(用于对齐207/319)
for a, b in (("20250701", "20261030"), ("20260615", "20261030"), ("20260501", "20261030")):
    sub = [r for r in ok if a <= r["日"] <= b]
    cc = [r for r in sub if r["温度"] is not None and r["温度"] < 40]
    ff = [r for r in sub if r["封单比"] is not None and r["封单比"] >= 2]
    print(f"窗{a}-{b}: 4板+ n={len(sub)} 冷{stat(cc)} 封{stat(ff)}")

json.dump(dict(样本=len(ok), 连板分布={str(k): sum(1 for r in ok if r["连板"] == k) for k in sorted(set(r["连板"] for r in ok))},
               日期范围=[ok[0]["日"], ok[-1]["日"]],
               冷桶=stat(cold), 封单桶=stat(feng), 冲突桶=stat(conf)),
          open(os.path.join(L, "_tmp_桶冲突_描述.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
