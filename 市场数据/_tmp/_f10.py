# -*- coding: utf-8 -*-
"""商业航天10只 F10主营构成快照(按产品, 最新报告期) — 环节卡位量化, 不改共享口径"""
import sys, io, json, time, gzip
from urllib.request import Request, urlopen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}
def secu(c):
    return ('SH' + c) if c[0] in '65' else ('SZ' + c) if c[0] in '023' else ('BJ' + c)
def f10(c, retries=3):
    url = "https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax?code=" + secu(c)
    for i in range(retries):
        try:
            raw = urlopen(Request(url, headers=UA), timeout=25).read()
            if raw[:2] == bytes([0x1F, 0x8B]): raw = gzip.decompress(raw)
            return json.loads(raw.decode('utf-8'))
        except Exception as e:
            if i == retries - 1: return {"_error": str(e)}
            time.sleep(1.2*(i+1))

codes = ['600261','603131','002565','002865','301079','605598','603703','600118','600501','002149']
out = {}
for c in codes:
    j = f10(c)
    z = j.get('zygcfx') or []
    if not z:
        print(c, 'NO DATA', str(j)[:120]); out[c] = None; time.sleep(0.2); continue
    rp = sorted({x.get('REPORT_DATE','')[:10] for x in z}, reverse=True)[0]
    rows = [x for x in z if x.get('REPORT_DATE','')[:10] == rp and str(x.get('MAINOP_TYPE')) == '2'] or \
           [x for x in z if x.get('REPORT_DATE','')[:10] == rp]
    items = [(x.get('ITEM_NAME','').strip(), round(float(x.get('MBI_RATIO') or 0)*100, 2)) for x in rows]
    out[c] = {'报告期': rp, 'items': items}
    print('##', c, '报告期', rp)
    for n, r in items[:7]:
        print(f'    {n:<24} {r:>6}%')
    time.sleep(0.2)
json.dump(out, open(B + '_tmp/_f10_space_20261029.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE _tmp/_f10_space_20261029.json')
