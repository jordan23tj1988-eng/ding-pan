# -*- coding: utf-8 -*-
"""hb-f 跌停池 46 真值交叉验证(腾讯逐票, 只读)"""
import json, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261022"
pools = json.load(open(D + r"\_hb_f_pools_1445.json", encoding="utf-8"))
dt = pools["dt"]
print("DT池条数", len(dt))

def mkt(c):
    c = str(c).zfill(6)
    return ("sh" if c[0] in "56" else ("bj" if c[0] in "48" or c[:2] in ("92",) else "sz")) + c

codes = []
for p in dt:
    c = str(p["c"]).zfill(6)
    codes.append(("sz" if c[0] in "0123" else ("sh" if c[0] in "56" else "bj")) + c)

rows = {}
for i in range(0, len(codes), 40):
    url = "https://qt.gtimg.cn/q=" + ",".join(codes[i:i + 40])
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("gbk", "replace")
    for seg in raw.strip().split(";"):
        seg = seg.strip()
        if not seg.startswith("v_"):
            continue
        _, _, body = seg.partition("=")
        f = body.strip().strip('"').split("~")
        if len(f) < 40:
            continue
        rows[f[2]] = {"name": f[1], "px": float(f[3]), "pre": float(f[4]), "pct": float(f[32]), "t": f[30]}

confirmed, not_dt = [], []
for p in dt:
    c = str(p["c"]).zfill(6)
    q = rows.get(c)
    if not q:
        not_dt.append((c, p.get("n"), "无报价"))
        continue
    lim = round(q["pre"] * 0.9, 2) if c[0] in "036" else round(q["pre"] * 0.9, 2)  # 主板/创业板 10% 近似; 双创20%须单独判
    is_dt = abs(q["px"] - lim) < 0.011
    (confirmed if is_dt else not_dt).append((c, q["name"], q["px"], "%.2f%%" % q["pct"], "限价%.2f" % lim))

print("\n腾讯确认在跌停价: %d" % len(confirmed))
print("未确认(非跌停价或无报价): %d" % len(not_dt))
for x in not_dt:
    print("  ", x)
json.dump({"fetched": pools["fetched"], "dt_pool_n": len(dt), "confirmed": len(confirmed),
           "unconfirmed": not_dt, "rows": rows},
          open(D + r"\_hb_f_dtcheck.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
