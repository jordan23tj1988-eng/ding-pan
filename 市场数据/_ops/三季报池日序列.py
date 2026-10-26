# -*- coding: utf-8 -*-
"""三季报池日序列补齐（MA-20261022-04 ③）
源: 东财 datacenter RPT_PUBLIC_OP_NEWPREDICT 报告期=2026-09-30（与 _学习/三季报临时池_20261021.json 同源）
口径: 预测指标含净利润; 预告类型∈{预增,扭亏}; 公告日<=当日(零后视镜); 按代码去重; 剔ST/退/N/C
输出: 追加到 _学习/三季报池日序列_20261023.json
"""
import glob
import json
import os
import sys
import urllib.parse
from urllib.request import Request, urlopen

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = sys.argv[1] if len(sys.argv) > 1 else "20261023"
CUT = "%s-%s-%s" % (DATE[:4], DATE[4:6], DATE[6:8])


def fetch_all():
    out = []
    for page in range(1, 6):
        q = {"reportName": "RPT_PUBLIC_OP_NEWPREDICT", "columns": "ALL",
             "pageSize": "500", "pageNumber": str(page),
             "sortColumns": "NOTICE_DATE", "sortTypes": "-1",
             "filter": "(REPORT_DATE='2026-09-30')"}
        u = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q)
        r = urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0",
                                        "Referer": "https://data.eastmoney.com/"}), timeout=30)
        j = json.loads(r.read().decode("utf-8"))
        data = (j.get("result") or {}).get("data") or []
        if not data:
            break
        out += data
        if len(data) < 500:
            break
    return out


def main():
    rows = fetch_all()
    pool = {}
    for x in rows:
        if x.get("NOTICE_DATE", "")[:10] > CUT:
            continue
        pf = x.get("PREDICT_FINANCE") or ""
        if "净利润" not in pf or "扣除" in pf:
            continue
        t = x.get("PREDICT_TYPE") or ""
        if t not in ("预增", "扭亏"):
            continue
        code = x["SECURITY_CODE"]
        nm = x["SECURITY_NAME_ABBR"]
        if any(s in nm for s in ("ST", "退")) or nm.endswith("N") or nm.startswith("C"):
            continue
        if code in pool:
            continue
        pool[code] = {"代码": code, "名称": nm, "公告日": x["NOTICE_DATE"][:10],
                      "类型": t, "增幅下%": x.get("ADD_AMP_LOWER"), "增幅上%": x.get("ADD_AMP_UPPER"),
                      "原因": (x.get("CHANGE_REASON_EXPLAIN") or "")[:180]}

    zt = open(os.path.join(BASE, DATE, "zt_pool.csv"), encoding="utf-8-sig").read().splitlines()
    import csv
    ztrows = list(csv.DictReader(zt))
    hits = [[r["代码"], r["名称"], pool[r["代码"]]["公告日"], r["连板数"], r["所属行业"]]
            for r in ztrows if r["代码"] in pool]

    # 主营驱动: 原因文本含当日题材/主营关键词(粗筛, 仅作参考)
    tpl = json.load(open(os.path.join(BASE, "产业链模板.json"), encoding="utf-8"))
    tpl_codes = {}
    for chain, v in tpl.items():
        if not isinstance(v, dict) or "环节" not in v:
            continue
        for node, arr in v["环节"].items():
            for c, n in arr:
                tpl_codes[c] = {"链": chain, "环节": node}

    day = {
        "cutoff": DATE,
        "raw_total_upto": len(rows),
        "池大小": len(pool),
        "∩涨停": len(hits),
        "∩涨停_名单": hits,
        "∩模板": len([c for c in pool if c in tpl_codes]),
        "三交叉": len([h for h in hits if h[0] in tpl_codes]),
        "三交叉_名单": [[h[0], h[1]] for h in hits if h[0] in tpl_codes],
        "主营驱动只数": len([c for c, v in pool.items()
                       if any(k in v["原因"] for k in ("价格", "量价", "订单", "产能", "销量", "需求", "涨价"))]),
        "含非经常词只数": len([c for c, v in pool.items()
                        if any(k in v["原因"] for k in ("非经常", "政府补助", "投资收益", "资产处置", "公允价值"))]),
        "当日涨停总数": len(ztrows),
    }

    prev = sorted(glob.glob(os.path.join(BASE, "_学习", "三季报池日序列_*.json")))
    prev = [x for x in prev if os.path.basename(x)[-13:-5] < DATE]
    series = {}
    if prev:
        series = json.load(open(prev[-1], encoding="utf-8")).get("明细", {})
    series[DATE] = day
    keys = sorted(series)
    by_date = {k: series[k]["∩涨停"] for k in keys}
    out = {"日期": DATE, "口径": "东财RPT_PUBLIC_OP_NEWPREDICT 报告期2026-09-30, 预增/扭亏, 公告日<=当日, 剔ST",
           "序列": by_date, "明细": series}
    p = os.path.join(BASE, "_学习", "三季报池日序列_%s.json" % DATE)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", p, os.path.getsize(p))
    print("序列", json.dumps(by_date, ensure_ascii=False))
    print("今日", json.dumps(day, ensure_ascii=False))


if __name__ == "__main__":
    main()
