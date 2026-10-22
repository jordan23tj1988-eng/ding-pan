# -*- coding: utf-8 -*-
"""hb-e 14:30 尾盘前哨取数: 腾讯实时报价 + 东财涨停/炸板/跌停池(DT池用 sort=fund:asc 规避 fbt 陷阱)"""
import json, urllib.request, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261022"
DATE = "20261022"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

codes = "sz002242,sz002639,sz002076,sz001239,sh000001,sz399001,sz399006"
# 高位板/炸板观察票
extra = "sz002696,sz000530,sz002724,sh603278,sh600293,sh600202,sz002520,sh601091"
url = "https://qt.gtimg.cn/q=" + codes + "," + extra
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "replace")
rows = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    key, _, body = seg.partition("=")
    key = key.strip()[2:]
    f = body.strip().strip('"').split("~")
    if len(f) < 40:
        continue
    rows[key] = {"code": f[2], "name": f[1], "px": float(f[3]), "pre": float(f[4]), "open": float(f[5]),
                 "pct": float(f[32]), "high": float(f[33]), "low": float(f[34]),
                 "amt_wan": float(f[37]) if f[37] else None, "bid1": f[9], "ask1": f[19], "t": f[30],
                 "limit_up": f[47] if len(f) > 47 else None}
json.dump({"fetched": NOW, "rows": rows}, open(os.path.join(D, "_hb_e_quote_1430.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 腾讯", NOW, "===")
for k, v in rows.items():
    print(k, v["name"], v["px"], "%+.2f%%" % v["pct"], "hi", v["high"], "lo", v["low"], "t", v["t"])


def pool(kind, extra_q, sort):
    u = ("https://push2ex.eastmoney.com/getTopic%s?ut=7eea3edcaed734bea9cbfc24409ed989"
         "&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=%s&date=%s%s" % (kind, sort, DATE, extra_q))
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
    d = j.get("data") or {}
    return d.get("pool") or [], j.get("rc"), j.get("rt")


zt, rc1, _ = pool("ZTPool", "", "fbt%3Aasc")
zb, rc2, _ = pool("ZBPool", "", "fbt%3Aasc")
dt, rc3, _ = pool("DTPool", "", "fund%3Aasc")   # 关键: DT 池禁用 fbt 排序
dt_bad, rc3b, _ = pool("DTPool", "", "fbt%3Aasc")  # 对照: 验证陷阱是否仍在
out = {"fetched": NOW, "zt": zt, "zb": zb, "dt": dt, "dt_fbt_sort_count": len(dt_bad),
       "rc": [rc1, rc2, rc3, rc3b]}
json.dump(out, open(os.path.join(D, "_hb_e_pools_1430.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 涨停池 %d / 炸板池 %d / 跌停池 %d (rc %s/%s/%s) | DT用fbt排序对照=%d(rc %s) ==="
      % (len(zt), len(zb), len(dt), rc1, rc2, rc3, len(dt_bad), rc3b))
lb = {}
for p in zt:
    lb[p.get("lbc", 0)] = lb.get(p.get("lbc", 0), 0) + 1
print("连板分布", dict(sorted(lb.items())))
print("涨停:", [(p.get("c"), p.get("n"), p.get("lbc")) for p in zt])
print("炸板:", [(p.get("c"), p.get("n"), p.get("zbc")) for p in zb])
print("跌停:", [(p.get("c"), p.get("n")) for p in dt])
if zt or zb:
    print("炸板率 = %d/(%d+%d) = %.4f" % (len(zb), len(zt), len(zb), len(zb) / (len(zt) + len(zb))))
