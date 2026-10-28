# -*- coding: utf-8 -*-
import urllib.request, json
def get(u, gbk=False, t=12):
    req=urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0','Referer':'http://quote.eastmoney.com/'})
    raw=urllib.request.urlopen(req, timeout=t).read()
    return raw.decode('gbk','ignore') if gbk else raw.decode('utf-8','ignore')
raw=get('http://qt.gtimg.cn/q=sh000001,sz399001,sz399006', gbk=True)
for seg in raw.split(';'):
    seg=seg.strip()
    if '="' not in seg: continue
    f=seg.split('="')[1].strip('"').split('~')
    if len(f)<40: continue
    print(f[1], 'px', f[3], 'pct', f[32], 'time', f[30], 'vol', f[36], 'amt', f[37])
print('--- 东财涨停池 20261028 ---')
try:
    j=json.loads(get('http://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date=20261028'))
    print('err', j.get('data') is None, 'pool_n', len(((j.get('data') or {}).get('pool') or [])))
except Exception as e:
    print('ERR', e)
