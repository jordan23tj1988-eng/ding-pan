# -*- coding: utf-8 -*-
"""hb-e 14:30 尾盘前哨取数: 腾讯实时报价(含exec前价) + 603370分时 + 东财ZT/ZB/DT(tc+fund明细)"""
import json, urllib.request, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
DATE = "20261023"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
codes = "sh603370,sz002242,sh000001,sz399001,sz399006"
url = "https://qt.gtimg.cn/q=" + codes
raw = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=15).read().decode("gbk", "replace")
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
                 "amt_wan": float(f[37]) if f[37] else None, "vol_shou": float(f[36]) if f[36] else None,
                 "bid1": f[9], "ask1": f[19], "t": f[30],
                 "limit_up": f[47] if len(f) > 47 else None, "limit_dn": f[48] if len(f) > 48 else None}
json.dump({"fetched": NOW, "rows": rows}, open(os.path.join(D, "_hb_e_quote_1430.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 腾讯实时", NOW, "===")
for k, v in rows.items():
    print(k, v["name"], v["px"], "%+.2f%%" % v["pct"], "hi", v["high"], "lo", v["low"], "amt(万)", v["amt_wan"], "t", v["t"])

def minute(code):
    u = "https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=" + code
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
    d = j.get("data", {}).get(code, {})
    return d.get("data", {}).get("data", []), d.get("qt", {})

mt, qt = minute("sh603370")
json.dump({"fetched": NOW, "minute": mt, "qt": qt}, open(os.path.join(D, "_hb_e_minute_603370.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n=== 603370 分时点数 %d, 末点 %s ===" % (len(mt), mt[-1] if mt else None))

def pool(kind, extra=""):
    u = ("https://push2ex.eastmoney.com/getTopic%s?ut=7eea3edcaed734bea9cbfc24409ed989"
         "&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%%3Aasc&date=%s%s" % (kind, DATE, extra))
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    j = json.loads(urllib.request.urlopen(r, timeout=15).read().decode("utf-8"))
    d = j.get("data") or {}
    return d.get("pool") or [], d.get("tc"), j.get("rc")

zt, tc1, rc1 = pool("ZTPool")
zb, tc2, rc2 = pool("ZBPool")
dt_a, tc3a, _ = pool("DTPool")
dt_f, tc3f, _ = pool("DTPool", "&sort=fund%3Aasc")
out = {"fetched": NOW, "date": DATE, "zt": zt, "zb": zb, "dt": dt_f or dt_a,
       "tc": {"zt": tc1, "zb": tc2, "dt_fbt": tc3a, "dt_fund": tc3f},
       "dt_len_fbt": len(dt_a), "dt_len_fund": len(dt_f), "rc": {"zt": rc1, "zb": rc2}}
json.dump(out, open(os.path.join(D, "_hb_e_pools_1430.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 东财池 %s ===" % NOW)
print("涨停 tc=%s len=%d | 炸板 tc=%s len=%d | 跌停 tc(fbt)=%s len=%d / tc(fund)=%s len=%d"
      % (tc1, len(zt), tc2, len(zb), tc3a, len(dt_a), tc3f, len(dt_f)))
lb = {}
for p in zt:
    lb[p.get("lbc", 0)] = lb.get(p.get("lbc", 0), 0) + 1
print("连板分布", dict(sorted(lb.items())))
print("涨停:", [(p.get("c"), p.get("n"), p.get("lbc"), p.get("hybk")) for p in zt])
print("炸板:", [(p.get("c"), p.get("n"), p.get("zbc"), p.get("hybk")) for p in zb])
print("跌停:", [(p.get("c"), p.get("n")) for p in (dt_f or dt_a)])
if (len(zt) + len(zb)) > 0:
    print("炸板率 = %d/%d = %.4f" % (len(zb), len(zt) + len(zb), len(zb) / (len(zt) + len(zb))))
