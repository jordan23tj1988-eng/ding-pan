# -*- coding: utf-8 -*-
"""hb-e DT池口径复核: 三种sort + 分页 + rc, 并与昨涨停池跌停票互证"""
import json, urllib.request, os, datetime
DATE = "20261023"
D = r"D:\股票数据\市场数据\盘中\20261023"
BASE = ("https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
        "&dpt=wz.ztzt&Pageindex=0&pagesize=300&date=%s" % DATE)
def get(extra):
    r = urllib.request.Request(BASE + extra, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    raw = urllib.request.urlopen(r, timeout=20).read().decode("utf-8")
    j = json.loads(raw)
    d = j.get("data") or {}
    return (d.get("pool") or []), d.get("tc"), j.get("rc"), len(raw)

out = {"fetched": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "date": DATE, "runs": {}}
for tag, extra in [("fbt_asc", "&sort=fbt%3Aasc"), ("zdp_asc", "&sort=zdp%3Aasc"),
                   ("fund_asc", "&sort=fund%3Aasc"), ("default", ""),
                   ("pageidx1", "&sort=zdp%3Aasc&Pageindex=1")]:
    try:
        p, tc, rc, n = get(extra)
        out["runs"][tag] = {"tc": tc, "len": len(p), "rc": rc, "rawlen": n,
                            "codes": [(x.get("c"), x.get("n"), x.get("zdp")) for x in p][:25]}
        print(tag, "tc=", tc, "len=", len(p), "rc=", rc, "raw", n)
        if p:
            print("   ", [(x.get("c"), x.get("n")) for x in p][:20])
    except Exception as e:
        out["runs"][tag] = {"err": str(e)}
        print(tag, "ERR", e)

# 独立互证: 昨涨停池33票中跌停(≤-9.8%) + 全市场跌停需另源
ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
fr = [x for x in ticks if x["ts"] <= "2026-10-23 14:31:15"]
dt_pool = [(r["code"], r["name"], r["pct"]) for r in fr[-1]["rows"] if r["pct"] <= -9.8]
out["yesterday_pool_dt"] = dt_pool
print("\n昨涨停池内跌停:", dt_pool)

# 腾讯校验这两只与全市场跌停数(抽样: 池内跌停票拉实时)
codes = ["sh" + c if c.startswith("6") else "sz" + c for c, _, _ in dt_pool]
if codes:
    u = "https://qt.gtimg.cn/q=" + ",".join(codes)
    raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}), timeout=15).read().decode("gbk", "replace")
    out["dt_quote_check"] = raw.strip()[:1200]
    print(raw.strip()[:600])
json.dump(out, open(os.path.join(D, "_hb_e_dtcheck.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
