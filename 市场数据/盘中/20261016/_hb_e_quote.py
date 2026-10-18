# -*- coding: utf-8 -*-
"""hb-e(2026-10-16 14:30) 决断时点直取行情(池外/在册票): 腾讯 qt.gtimg.cn, 一次性取回并落档。
口径: 本文件即『决断后下一tick留档价』的来源凭证(mtime/行情戳为本场留档时间), 不构成后视镜。
"""
import json, io, os, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = r"D:\股票数据\市场数据\盘中\20261016"
CODES = ["sz000011", "sz002860", "sz000601", "sh603968", "sz000823",
         "sz300111", "sh603230", "sz002815", "sz001318", "sz301282",
         "sz002134", "sh605058", "sh600812", "sz002945", "sh600668", "sh605189",
         "sh000001", "sz399001"]
url = "http://qt.gtimg.cn/q=" + ",".join(CODES)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://gu.qq.com/"})
raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "replace")
out, lines = {}, []
for seg in raw.split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    code = seg[2:seg.index("=")].strip()
    f = seg[seg.index('"')+1:seg.rindex('"')].split("~")
    if len(f) < 45:
        lines.append("%s 字段不足 n=%d" % (code, len(f)))
        continue
    rec = {"name": f[1], "last": float(f[3]), "preClose": float(f[4]), "open": float(f[5]),
           "volume_shou": float(f[6]), "amount_wan": float(f[37]) if f[37] else None,
           "high": float(f[33]), "low": float(f[34]), "pct": float(f[32]),
           "bid1": float(f[9]), "ask1": float(f[19]), "turnover_pct": f[38],
           "time": f[30], "amplitude_pct": f[43]}
    out[code] = rec
    lines.append("%s %-8s last=%.2f pct=%+.2f%% 开=%.2f 高=%.2f 低=%.2f 前收=%.2f bid1=%.2f ask1=%.2f 换手=%s%% 额=%.0f万 振幅=%s%% 戳=%s"
                 % (code, rec["name"], rec["last"], rec["pct"], rec["open"], rec["high"], rec["low"],
                    rec["preClose"], rec["bid1"], rec["ask1"], rec["turnover_pct"],
                    rec["amount_wan"] or 0, rec["amplitude_pct"], rec["time"]))
with io.open(os.path.join(D, "_hb_e_quote.json"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps(out, ensure_ascii=False, indent=1))
print("\n".join(lines))
print("落档: 盘中/20261016/_hb_e_quote.json")
