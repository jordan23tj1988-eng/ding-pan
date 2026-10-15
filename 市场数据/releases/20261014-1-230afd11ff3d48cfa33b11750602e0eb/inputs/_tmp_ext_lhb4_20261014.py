# -*- coding: utf-8 -*-
import os,json,csv,glob
from collections import Counter,defaultdict
ROOT=r'D:\股票数据\市场数据';L=os.path.join(ROOT,'_学习');d='20261014'
GENERIC={'机构专用','沪股通专用','深股通专用','机构','自然人','其他自然人','中小投资者','沪股通','深股通','量化基金','其他','北向资金'}
def real_seat(n):
    n=(n or '').strip()
    if not n or n in GENERIC: return False
    return ('营业部' in n) or ('分公司' in n) or ('总部' in n)
BM={}
def load_bars(code):
    if code in BM: return BM[code]
    fp=os.path.join(L,'_bars_cache','%s.csv'%code);m={}
    if os.path.exists(fp):
        for r in csv.DictReader(open(fp,encoding='utf-8')):
            m[r['date'].replace('-','')]=(float(r['open']),float(r['close']))
    BM[code]=m;return m
def z1(code,t):
    m=load_bars(code);ks=sorted(m)
    if t not in m: return None
    i=ks.index(t)
    if i+1>=len(ks): return None
    nt=ks[i+1];o,c=m[nt]
    return (c-o)/o*100.0
EDGES={3:('国泰海通证券股份有限公司总部','高盛(中国)证券有限责任公司上海浦东新区世纪大道证券营业部'),
       4:('国新证券股份有限公司北京分公司','开源证券股份有限公司西安西大街证券营业部'),
       5:('国信证券股份有限公司浙江互联网分公司','国泰海通证券股份有限公司总部'),
       6:('中信证券股份有限公司上海分公司','国泰海通证券股份有限公司总部')}
hits=defaultdict(list); nullhit=set()
for fp in sorted(glob.glob(os.path.join(L,'_席位动向','*.csv'))):
    t=os.path.basename(fp)[:8]
    if t>d: continue
    seats={}
    for r in csv.DictReader(open(fp,encoding='utf-8')):
        typ=r.get('类型','') or ''
        if ('连续' in typ) or ('累计' in typ) or ('区间' in typ): continue
        if not real_seat(r.get('席位','')): continue
        if float(r.get('净额') or 0)>=3e7: seats.setdefault(str(r['代码']).zfill(6),set()).add(r['席位'])
    for c,sm in seats.items():
        nullhit.add((t,c))
        for k,(a,b) in EDGES.items():
            if a in sm and b in sm: hits[k].append((t,c))
cal=sorted({t for t,c in nullhit}); last60=cal[-60:][0]
def agg(rows):
    vals=[];win=0
    for t,c in rows:
        r=z1(c,t)
        if r is None: continue
        vals.append(r); win+=(1 if r>0 else 0)
    if not vals: return (0,None,None)
    return (len(vals),round(100.0*win/len(vals),1),round(sum(vals)/len(vals),2))
def dedup(rows,mode='first'):
    per=defaultdict(list)
    for t,c in rows:
        r=z1(c,t)
        if r is not None: per[c].append(r)
    if not per: return (0,None,None)
    if mode=='first': v=[x[0] for x in per.values()]
    else: v=[sum(x)/len(x) for x in per.values()]
    win=sum(1 for x in v if x>0)
    return (len(v),round(100.0*win/len(v),1),round(sum(v)/len(v),2))
print('近60日起=',last60)
nb=agg(sorted(nullhit)); print('null 全窗',nb,' 近60日',agg([x for x in nullhit if x[0]>=last60]))
for k in (3,4,5,6):
    hs=hits[k]; cnt=Counter(c for t,c in hs)
    print('== EDGE%d 全窗 hits=%d 独立票=%d 集中度top3=%s'%(k,len(hs),len(cnt),cnt.most_common(3)))
    print('   全窗 逐笔',agg(hs),' 去重票(首次)',dedup(hs,'first'),' 去重票(均值)',dedup(hs,'avg'))
    hs6=[x for x in hs if x[0]>=last60]
    cnt6=Counter(c for t,c in hs6)
    print('   近60日 hits=%d 独立票=%d top3=%s'%(len(hs6),len(cnt6),cnt6.most_common(3)))
    print('   近60日 逐笔',agg(hs6),' 去重(首次)',dedup(hs6,'first'),' 去重(均值)',dedup(hs6,'avg'))
