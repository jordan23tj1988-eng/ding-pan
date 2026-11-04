# -*- coding: utf-8 -*-
import json, io, sys, urllib.request, urllib.parse, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

codes = ['002156', '600206', '002916', '002463', '002636', '002821', '600584', '603186',
         '001389', '688409', '603061', '002371', '688072', '688652', '688037', '301583',
         '002365', '603906', '002805', '601123', '002536', '600547', '002827']

URL = ('https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_LICO_FN_CPD'
       '&columns=SECURITY_CODE,SECURITY_NAME_ABBR,REPORTDATE,NOTICE_DATE,TOTAL_OPERATE_INCOME,YSTZ,'
       'PARENT_NETPROFIT,SJLTZ,WEIGHTAVG_ROE&filter=(SECURITY_CODE%3D%22__CODE__%22)'
       '&pageNumber=1&pageSize=12&sortColumns=REPORTDATE&sortTypes=-1')

out = {}
for c in codes:
    try:
        req = urllib.request.Request(URL.replace('__CODE__', c), headers={'User-Agent': 'Mozilla/5.0'})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        rows = (d.get('result') or {}).get('data') or []
        keep = {}
        for r in rows:
            rd = r['REPORTDATE'][:10]
            if rd in ('2026-09-30', '2025-09-30'):
                keep[rd] = r
        out[c] = keep
        a = keep.get('2026-09-30')
        b = keep.get('2025-09-30')
        if a:
            print('%s %s | 2026Q3 营收%.2f亿 YSTZ %.2f%% 归母%.2f亿 SJLTZ %.2f%% ROE %.2f%% 公告%s | 基期归母%s 营收%s' % (
                c, a['SECURITY_NAME_ABBR'], a['TOTAL_OPERATE_INCOME'] / 1e8, a['YSTZ'],
                a['PARENT_NETPROFIT'] / 1e8, a['SJLTZ'], a['WEIGHTAVG_ROE'], a['NOTICE_DATE'][:10],
                ('%.2f亿' % (b['PARENT_NETPROFIT'] / 1e8)) if b else '缺',
                ('%.2f亿' % (b['TOTAL_OPERATE_INCOME'] / 1e8)) if b else '缺'))
        else:
            print('%s 无2026-09-30 行' % c)
    except Exception as e:
        print(c, 'ERR', e)
    time.sleep(0.25)

json.dump(out, open('_学习/_q3_logic_20261104.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote _学习/_q3_logic_20261104.json')
