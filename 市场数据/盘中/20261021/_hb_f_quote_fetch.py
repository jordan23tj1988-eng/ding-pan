# -*- coding: utf-8 -*-
"""14:45 深场B 取数: 腾讯实时帧(持仓两票不在池内) + 池内截面序列"""
import json, urllib.request, os, io

D = r"D:\股票数据\市场数据\盘中\20261021"
now = "2026-10-21 14:47"

codes = "sz000601,sz000823,sh000001,sz399006,sh603278,sz002076,sh600293,sh603636,sz002929,sz301313,sz300115,sz002881,sz001283,sz002940,sh603696,sh600267"
url = "https://qt.gtimg.cn/q=" + codes
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
    rows[key] = {
        "code": f[2], "name": f[1], "px": float(f[3]), "pre": float(f[4]), "open": float(f[5]),
        "pct": float(f[32]), "high": float(f[33]), "low": float(f[34]),
        "amt_wan": float(f[37]) if f[37] else None, "vol": f[36],
        "bid1": f[9], "bid1_qty": f[10], "ask1": f[19], "ask1_qty": f[20],
        "limit_up": f[47] if len(f) > 47 else None, "limit_dn": f[48] if len(f) > 48 else None,
        "t": f[30],
    }
out = {"fetched": now, "url": url, "rows": rows, "raw_len": len(raw)}
p = os.path.join(D, "_hb_f_quote_exec.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", p)
for k, v in rows.items():
    print(k, v["name"], v["px"], v["pct"], "bid1", v["bid1"], "ask1", v["ask1"], "t", v["t"], "limup", v["limit_up"], "limdn", v["limit_dn"])
