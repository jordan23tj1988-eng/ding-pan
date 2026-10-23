import csv,json
from collections import defaultdict,Counter
D='20261023'
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
ded=[r for r in rows if not is_int(r['类型'])]
seen=set(); dd=[]
for r in ded:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k); dd.append(r)
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dg(r):
    v=pj.get(r['席位']); return v['档'] if v else '未入档'
def is_cb(c): return c[:2] in ('11','12')
stock=[r for r in dd if not is_cb(r['代码'])]
cb=[r for r in dd if is_cb(r['代码'])]
print(f'股票笔 {len(stock)} 转债笔 {len(cb)}')
for label,S in [('含转债',dd),('仅股票',stock)]:
    tot=len(S); ta=sum(float(r['买入金额']) for r in S); tn=sum(float(r['净额']) for r in S)
    sa=[r for r in S if dg(r) in ('S','A') and float(r['买入金额'])>=1e7]
    saa=sum(float(r['买入金额']) for r in sa); san=sum(float(r['净额']) for r in sa)
    s=[r for r in S if dg(r)=='S']
    print(f'{label}: 笔{tot} 买额{ta/1e8:.2f}亿 净额{tn/1e8:.2f}亿 | S/A {len(sa)}笔 {len(sa)/tot*100:.2f}% 买额{saa/1e8:.2f}亿 占{saa/ta*100:.1f}% 净额{san/1e8:.2f}亿 | S {len(s)}笔 买额{sum(float(r["买入金额"]) for r in s)/1e8:.2f}亿 净额{sum(float(r["净额"]) for r in s)/1e8:.2f}亿 max{max([float(r["买入金额"]) for r in s] or [0])/1e8:.2f}亿')
# 按日序列 S/A 买额占比（最近12个交易日）
import os,glob
print('--- S/A 买额占全榜买额 逐日序列 ---')
days=sorted([os.path.basename(p)[:-4] for p in glob.glob(f'_学习/_席位动向/2026*.csv')])[-12:]
for day in days:
    R=list(csv.DictReader(open(f'_学习/_席位动向/{day}.csv',encoding='utf-8')))
    R2=[r for r in R if not is_int(r['类型'])]
    se=set(); Q=[]
    for r in R2:
        k=(r['代码'],r['席位'])
        if k in se: continue
        se.add(k); Q.append(r)
    Qs=[r for r in Q if not is_cb(r['代码'])]
    ta=sum(float(r['买入金额']) for r in Qs)
    sa=[r for r in Qs if dg(r) in ('S','A') and float(r['买入金额'])>=1e7]
    saa=sum(float(r['买入金额']) for r in sa)
    print(f'{day} 笔{len(Qs)} S/A {len(sa)}笔 {len(sa)/len(Qs)*100:.2f}% 买额{saa/1e8:.2f}亿 占{saa/ta*100 if ta else 0:.1f}%')
