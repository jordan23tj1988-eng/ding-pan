# -*- coding: utf-8 -*-
import json,csv,os,statistics,collections
os.chdir(r"D:/股票数据/市场数据"); D='20261020'
def rd(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.DictReader(f))
rows=rd(f'{D}/lhb.csv'); ds={x['代码']:x for x in json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))['全量']}
zt={r['代码']:r for r in rd(f'{D}/zt_pool.csv')}
# 当日榜 = 校验口径=当日榜
daily=[c for c,x in ds.items() if x.get('源1口径')=='当日榜' and x.get('源1净买亿') is not None]
print('当日榜票数',len(daily),'净买合计%+.2f亿'%sum(ds[c]['源1净买亿'] for c in daily))
pos=[c for c in daily if ds[c]['源1净买亿']>0]; neg=[c for c in daily if ds[c]['源1净买亿']<0]
print('净买>0',len(pos),'净卖',len(neg),'中位%.0f万'%(statistics.median([ds[c]['源1净买亿'] for c in daily])*1e4))
print('单票>1亿',len([c for c in daily if ds[c]['源1净买亿']>1]))
# funnel
f1=[c for c in zt if c in daily]; print('① 涨停∩当日榜',len(f1))
f2=[c for c in f1 if ds[c]['源1净买亿']>0]; print('② 且净买>0',len(f2),sorted(f2))
f3=[c for c in f2 if ds[c]['判定']=='一致']; print('③ 且双源一致',len(f3),sorted(f3))
def bucket(p): return '≤0' if p<=0 else ('0-5' if p<5 else ('5-10' if p<10 else ('10-20' if p<20 else '>20')))
f4=[c for c in f3 if bucket(ds[c]['源1净买亿']/ (ds[c]['源1净买亿']/ ( (ds[c]['源1净买亿']/1) ) ) if False else 0)]
# 占比 from csv row matching 当日榜口径
lhb={}
for r in rows:
    c=r['代码']
    impr=r['上榜原因']
    cum=('连续' in impr) or ('累计' in impr) or ('严重异常' in impr)
    if not cum: lhb[c]=r
b={c:bucket(float(lhb[c]['净买额占总成交比'])) for c in f3 if c in lhb}
print('④ 占比桶分布',collections.Counter(b.values()), [(c,round(float(lhb[c]['净买额占总成交比']),2)) for c in f3 if c in lhb])
f5=[c for c in f3 if c in lhb and float(lhb[c]['净买额占总成交比'])<=20]; print('⑤ 且占比≤20%',len(f5),f5)
fen=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
sd=rd(f'_学习/_席位动向/{D}.csv')
sa=collections.defaultdict(list)
for r in sd:
    f=fen.get(r['席位'])
    if f and f['档'] in ('S','A'): sa[r['代码']].append((r['席位'],f['档'],f['样本'],f['小样本'],float(r['净额'])/1e4))
f6=[c for c in f5 if any((not x[3]) and x[4]>=1000 for x in sa.get(c,[]))]; print('⑥ 且非小样本S/A席位净买≥1000万',len(f6),f6)
print()
print('候选(所有一致∧当日榜净买>0∧涨停)的S/A足迹:')
for c in f5:
    print(' ',c,lhb[c]['名称'],'S/A:',[(x[0][:18],x[1],x[2],x[3],round(x[4])) for x in sa.get(c,[])])
# 全市场 S/A 足迹 (股票端)
allsa=sorted([(c,n) for c,v in sa.items() for n in v if not c.startswith(('11','12'))],key=lambda t:-t[1][4])
print()
print('全市场股票端S/A足迹条数',len(allsa))
for c,n in allsa: print('  %-7s %-8s %s %s n=%-3d ⚠%s 净%+.0f万 判定%s'%(c,ds.get(c,{}).get('名称','') or lhb.get(c,{}).get('名称',''),n[1],n[0][:22],n[2],n[3],n[4],ds.get(c,{}).get('判定')))
