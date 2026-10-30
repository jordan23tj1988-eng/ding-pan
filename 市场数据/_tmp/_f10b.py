# -*- coding: utf-8 -*-
import sys, io, json, time, gzip
from urllib.request import Request, urlopen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}
def secu(c): return ('SH'+c) if c[0] in '65' else (('SZ'+c) if c[0] in '023' else ('BJ'+c))
def f10(c):
    url = "https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax?code=" + secu(c)
    for i in range(3):
        try:
            raw = urlopen(Request(url, headers=UA), timeout=25).read()
            if raw[:2] == bytes([0x1F, 0x8B]): raw = gzip.decompress(raw)
            return json.loads(raw.decode('utf-8'))
        except Exception as e:
            if i == 2: return {"_error": str(e)}
            time.sleep(1.2)
for c in ['001219','605338','603536','605179','002862','600592']:
    j = f10(c); z = j.get('zygcfx') or []
    if not z: print(c, 'NO DATA'); continue
    rp = sorted({x.get('REPORT_DATE','')[:10] for x in z}, reverse=True)[0]
    rows = [x for x in z if x.get('REPORT_DATE','')[:10] == rp and str(x.get('MAINOP_TYPE')) == '2']
    print('##', c, rp, ' | '.join(f"{x.get('ITEM_NAME','').strip()} {round(float(x.get('MBI_RATIO') or 0)*100,2)}%" for x in rows[:5]))
    time.sleep(0.2)
