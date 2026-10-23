import csv,json,os,glob
from collections import Counter,defaultdict
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dg(s):
    v=pj.get(s);return v['档'] if v else '未入档'
days=sorted([os.path.basename(p)[:-4] for p in glob.glob('_学习/_席位动向/2026*.csv')])[-12:]
out=[]
for d in days:
    rows=list(csv.DictReader(open(f'_学习/_席位动向/{d}.csv',encoding='utf-8')))
    dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
    seen=set();Q=[]
    for r in dd:
        k=(r['代码'],r['席位'])
        if k in seen: continue
        seen.add(k);Q.append(r)
    P=[r for r in Q if float(r['净额'])>0 and float(r['买入金额'])>=1e7]
    allamt=sum(float(r['买入金额']) for r in Q)
    sa=[r for r in P if dg(r['席位']) in ('S','A')]
    saa=sum(float(r['买入金额']) for r in sa); san=sum(float(r['净额']) for r in sa)
    mx=max([float(r['买入金额']) for r in sa] or [0])
    s=[r for r in P if dg(r['席位'])=='S']
    out.append(dict(日=d,笔=len(P),SA笔=len(sa),SA笔占比=round(len(sa)/len(P)*100,2) if P else None,
        SA买额亿=round(saa/1e8,2),SA净额亿=round(san/1e8,2),SA买额占全榜=round(saa/allamt*100,2) if allamt else None,
        SA单笔最大亿=round(mx/1e8,3),S笔=len(s),S买额亿=round(sum(float(r['买入金额']) for r in s)/1e8,3)))
for r in out: print(r)
json.dump(out,open('_学习/_tmp_series2.json','w',encoding='utf-8'),ensure_ascii=False)
