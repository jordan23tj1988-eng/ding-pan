# -*- coding: utf-8 -*-
import json, ssl, urllib.request, urllib.parse, csv, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
EM = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_CTX = ssl.create_default_context(); _CTX.check_hostname=False; _CTX.verify_mode=ssl.CERT_NONE
def get(report, flt, ps=500, page=1, sort=None):
    url = f"{EM}?reportName={report}&columns=ALL&pageSize={ps}&pageNumber={page}&filter=" + urllib.parse.quote(flt)
    if sort: url += "&sortColumns=%s&sortTypes=-1" % sort
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=_CTX))
    req = urllib.request.Request(url, headers={"Referer":"https://data.eastmoney.com/","User-Agent":"Mozilla/5.0"})
    try:
        with op.open(req, timeout=30) as r: j = json.loads(r.read().decode("utf-8","replace"))
    except Exception as e:
        return None
    if not j.get("success"): return None
    return (j.get("result") or {})

# 30日前瞻解禁窗口 20261015~20261113
rows=[]; 
for pg in range(1,4):
    r = get("RPT_LIFT_STAGE", "(FREE_DATE>='2026-10-15')(FREE_DATE<='2026-11-13')", ps=500, page=pg, sort="FREE_DATE")
    if not r: break
    d = r.get('data') or []
    if not d: break
    rows += d
print('30日前瞻解禁 count(单页)=', (get("RPT_LIFT_STAGE","(FREE_DATE>='2026-10-15')(FREE_DATE<='2026-11-13')") or {}).get('count'), '取回', len(rows))
rr = list(csv.reader(open('D:/股票数据/市场数据/20261014/zt_pool.csv', encoding='utf-8')))
zt = {r[1].strip(): r[2].strip() for r in rr[1:]}
w = {}
for x in rows: w.setdefault(str(x['SECURITY_CODE']), []).append(x)
print('窗口内涨停命中:', [(c, zt[c], [str(y['FREE_DATE'])[:10] for y in w[c]]) for c in zt if c in w] or '无')
CAND = ['000823','002552','605189','000601','002343','603096','002696']
print('窗口内候选命中:', [(c, [str(y['FREE_DATE'])[:10] for y in w[c]]) for c in CAND if c in w] or '无')

# 昨日观察3只 今日表现
B='D:/股票数据/市场数据/_学习/_bars_cache/'
def last2(code):
    p=B+code+'.csv'
    if not os.path.exists(p): return None
    r=list(csv.reader(open(p,encoding='utf-8'))); h=r[0]
    d=[dict(zip(h,x)) for x in r[1:] if x and x[0]]
    return d[-2], d[-1]
print()
print('昨日观察3只 今日(20261014)表现:')
for c in ['001229','000833','603042']:
    l=last2(c)
    if not l: print(c,'NODATA'); continue
    p0,p1=l
    print(f"  {c} {p0['date']}收{p0['close']} → {p1['date']}收{p1['close']} 涨{round((float(p1['close'])/float(p0['close'])-1)*100,2)}% 开{p1['open']} 高{p1['high']} 低{p1['low']}")
