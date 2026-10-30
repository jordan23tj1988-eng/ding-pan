# -*- coding: utf-8 -*-
"""三季报披露日命中表 (MA-20261028-05③) 东财 RPT_PUBLIC_OP_NEWPREDICT 报告期2026-09-30"""
import sys, io, json, os, csv, urllib.parse
from urllib.request import Request, urlopen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
DATE = '20261029'; CUT = '2026-10-29'

def fetch_all():
    out = []
    for page in range(1, 7):
        q = {"reportName": "RPT_PUBLIC_OP_NEWPREDICT", "columns": "ALL",
             "pageSize": "500", "pageNumber": str(page),
             "sortColumns": "NOTICE_DATE", "sortTypes": "-1",
             "filter": "(REPORT_DATE='2026-09-30')"}
        u = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q)
        r = urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0",
                                        "Referer": "https://data.eastmoney.com/"}), timeout=30)
        j = json.loads(r.read().decode("utf-8"))
        data = (j.get("result") or {}).get("data") or []
        if not data: break
        out += data
        if len(data) < 500: break
    return out

rows = fetch_all()
print('raw rows', len(rows))
pool = {}
for x in rows:
    if x.get("NOTICE_DATE", "")[:10] > CUT: continue
    pf = x.get("PREDICT_FINANCE") or ""
    if "净利润" not in pf or "扣除" in pf: continue
    t = x.get("PREDICT_TYPE") or ""
    if t not in ("预增", "扭亏"): continue
    code = x["SECURITY_CODE"]; nm = x["SECURITY_NAME_ABBR"]
    if any(s in nm for s in ("ST", "退")) or nm.endswith("N") or nm.startswith("C"): continue
    if code in pool: continue
    pool[code] = {"代码": code, "名称": nm, "公告日": x["NOTICE_DATE"][:10], "类型": t,
                  "增幅下%": x.get("ADD_AMP_LOWER"), "增幅上%": x.get("ADD_AMP_UPPER"),
                  "原因": (x.get("CHANGE_REASON_EXPLAIN") or "")[:200]}

zt = list(csv.DictReader(open(B + DATE + '/zt_pool.csv', encoding='utf-8-sig')))
tpl = json.load(open(B + '产业链模板.json', encoding='utf-8-sig'))
tpl_codes = {}
for chain, v in tpl.items():
    if not isinstance(v, dict) or '环节' not in v: continue
    for node, arr in v['环节'].items():
        for c, n in arr: tpl_codes[c] = {'链': chain, '环节': node}

hits = []
for r in zt:
    c = r['代码']
    if c in pool:
        p = dict(pool[c]); p['连板'] = r['连板数']; p['行业'] = r['所属行业']
        p['模板'] = tpl_codes.get(c)
        hits.append(p)
print('\n== 池大小', len(pool), ' 今日涨停∩池', len(hits))
for h in hits:
    print(json.dumps(h, ensure_ascii=False))

win = {c: v for c, v in pool.items() if '2026-10-29' <= v['公告日'] <= '2026-10-31'}
print('\n== 公告日落在 20261029~20261031 的池内票:', len(win))
for c, v in sorted(win.items(), key=lambda kv: kv[1]['公告日']):
    print(v['公告日'], c, v['名称'], v['类型'], v['增幅下%'], v['增幅上%'], '|', v['原因'][:70])
# 公告日=今日 且 非涨停 (明日可能有反应)
today = {c: v for c, v in pool.items() if v['公告日'] == '2026-10-29'}
print('\n== 公告日=20261029 全部', len(today))
for c, v in today.items():
    print(c, v['名称'], v['类型'], '|', v['原因'][:60])

json.dump({'日期': DATE, '口径': '东财RPT_PUBLIC_OP_NEWPREDICT 报告期2026-09-30 预增/扭亏 公告日<=20261029 剔ST; 双源交叉字段=本文件不含(已核实)',
           '池大小': len(pool), '今日涨停_命中': hits,
           '公告日20261029_20261031': list(win.values()),
           '公告日20261029_全部': list(today.values())},
          open(B + '_tmp/_q3_20261029.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE _tmp/_q3_20261029.json')
