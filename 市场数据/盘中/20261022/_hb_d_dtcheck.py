# -*- coding: utf-8 -*-
"""核验跌停池 0 是否真实: 11:04 名单逐票取价 + 跌停池二次取数(不同排序)"""
import json, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261022"
codes = "sh603669,sh600661,sz002990,sz001368,sz002835,sz002172,sz002388"
url = "https://qt.gtimg.cn/q=" + codes
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "replace")
print("=== 11:04 跌停名单 13:32 现状 ===")
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    f = seg.partition("=")[2].strip().strip('"').split("~")
    if len(f) < 40:
        continue
    px, pre = float(f[3]), float(f[4])
    print("%s %s px=%.2f pre=%.2f pct=%+.2f%% 跌停价=%s" % (f[2], f[1], px, pre, float(f[32]),
          f[48] if len(f) > 48 else "?"))

for sort in ["fund%3Aasc", "fbt%3Aasc", ""]:
    u = ("https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
         "&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=%s&date=20261022" % sort)
    try:
        r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
        j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
        d = j.get("data") or {}
        pl = d.get("pool") or []
        print("sort=%-12s rc=%s pool=%d %s" % (sort or "(none)", j.get("rc"), len(pl),
                                               [(p.get("c"), p.get("n")) for p in pl]))
    except Exception as e:
        print("sort=%s ERR %s" % (sort, e))
