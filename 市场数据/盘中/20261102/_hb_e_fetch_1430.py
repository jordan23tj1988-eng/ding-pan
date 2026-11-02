# -*- coding: utf-8 -*-
"""hb-e 14:30 取数：腾讯 qt 报价 + 东财 push2ex 涨停/跌停池宽度。只落盘，不写决断。"""
import json, os, sys, time, urllib.request

D = r"D:\股票数据\市场数据"
OUT = os.path.join(D, "盘中", "20261102")
CODES = [
    ("sh603037", "603037"), ("sh603533", "603533"), ("sh601188", "601188"),
    ("sz002365", "002365"), ("sz001287", "001287"), ("sz001219", "001219"), ("sz000995", "000995"),
    ("sz301132", "301132"), ("sh601083", "601083"), ("sz301520", "301520"),
    ("sh000001", "000001"), ("sz399001", "399001"), ("sz399006", "399006"),
]

def fetch(url, enc="gbk", timeout=10):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(enc, "ignore")

q = ",".join(c for c, _ in CODES)
txt = fetch("http://qt.gtimg.cn/q=" + q)
rows = []
for seg in txt.split(";"):
    seg = seg.strip()
    if "=" not in seg:
        continue
    f = seg.split("=\"")[1].rstrip("\"").split("~")
    if len(f) < 40:
        continue
    rows.append(dict(code=f[2], name=f[1], last=float(f[3] or 0), pre=float(f[4] or 0),
                     open=float(f[5] or 0), high=float(f[33] or 0), low=float(f[34] or 0),
                     pct=float(f[32] or 0), amt_wan=float(f[37] or 0),
                     bid1=float(f[9] or 0), ask1=float(f[19] or 0), ts=f[30]))
tsv = os.path.join(OUT, "_hb_e_quote_1430.tsv")
with open(tsv, "w", encoding="utf-8") as fh:
    fh.write("code\tname\tlast\tpre\topen\thigh\tlow\tpct\tamt_wan\tbid1\task1\tts\n")
    for r in rows:
        fh.write("%s\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.0f\t%.2f\t%.2f\t%s\n" % (
            r["code"], r["name"], r["last"], r["pre"], r["open"], r["high"], r["low"],
            r["pct"], r["amt_wan"], r["bid1"], r["ask1"], r["ts"]))
print("QUOTE_ROWS", len(rows), "->", tsv)
print(open(tsv, encoding="utf-8").read())

# 东财 push2ex 涨停池 / 跌停池
def push2ex(fid, pz=300):
    url = ("https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
           "&dpt=wz.ztzt&Pageindex=0&pagesize=%d&sort=fbt:asc&date=20261102" % pz) if fid == "zt" else \
          ("https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
           "&dpt=wz.ztzt&Pageindex=0&pagesize=%d&sort=fund:asc&date=20261102" % pz)
    txt = fetch(url, enc="utf-8")
    j = json.loads(txt)
    d = j.get("data") or {}
    pool = d.get("pool") or []
    return j.get("tc"), len(pool), pool

res = {}
for k in ("zt", "dt"):
    tc, n, pool = push2ex(k)
    res[k] = dict(tc=tc, n=n, pool=pool)
    print(k, "tc=", tc, "pool=", n)
json.dump(res, open(os.path.join(OUT, "_hb_e_breadth_1430.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
zbc = [p for p in res["zt"]["pool"] if (p.get("zbc") or 0) >= 1]
print("ZT_pool", res["zt"]["n"], "zbc>=1", len(zbc))
for p in res["zt"]["pool"]:
    if p.get("c") in ("603533", "601083", "301132", "002365", "001287"):
        print("POOL_HIT", p.get("c"), p.get("n"), "zbc", p.get("zbc"), "lbc", p.get("lbc"),
              "fbt", p.get("fbt"), "lbt", p.get("lbt"), "fund", p.get("fund"), "amount", p.get("amount"), "hybk", p.get("hybk"))
