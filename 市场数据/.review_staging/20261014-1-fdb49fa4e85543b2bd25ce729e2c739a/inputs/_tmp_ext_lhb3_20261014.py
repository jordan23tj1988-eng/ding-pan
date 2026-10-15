# -*- coding: utf-8 -*-
import os,json,csv,glob
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
# 全窗收集每边的 (t,code) 与当日各席净买
EDGES={3:('国泰海通证券股份有限公司总部','高盛(中国)证券有限责任公司上海浦东新区世纪大道证券营业部'),
       4:('国新证券股份有限公司北京分公司','开源证券股份有限公司西安西大街证券营业部'),
       5:('国信证券股份有限公司浙江互联网分公司','国泰海通证券股份有限公司总部'),
       6:('中信证券股份有限公司上海分公司','国泰海通证券股份有限公司总部')}
hits={k:[] for k in EDGES}
for fp in sorted(glob.glob(os.path.join(L,'_席位动向','*.csv'))):
    t=os.path.basename(fp)[:8]
    if t>d: continue
    seats={}
    for r in csv.DictReader(open(fp,encoding='utf-8')):
        typ=r.get('类型','') or ''
        if ('连续' in typ) or ('累计' in typ) or ('区间' in typ): continue
        if not real_seat(r.get('席位','')): continue
        net=float(r.get('净额') or 0)
        if net>=3e7: seats.setdefault(str(r['代码']).zfill(6),{})[r['席位']]=(net,r.get('名称',''))
    for c,sm in seats.items():
        for k,(a,b) in EDGES.items():
            if a in sm and b in sm: hits[k].append((t,c,sm[a][0],sm[b][0],sm[a][1]))
for k in (4,5,3,6):
    hs=hits[k]
    n=0;win=0;s=0.0;seen={}
    for t,c,na,nb,nm in hs:
        r=z1(c,t)
        if r is None: continue
        n+=1;s+=r;win+=(1 if r>0 else 0)
        seen.setdefault(c,[]).append(round(r,2))
    print('EDGE%d %s X %s'%(k,EDGES[k][0][:8],EDGES[k][1][:8]),'n=%d 胜率%.1f%% 均%.2f'%(n,100.0*win/max(n,1),s/max(n,1)))
    # 去重票口径（每票取首次）
    fw=[v[0] for v in seen.values()]; wn=sum(1 for x in fw if x>0)
    print('   去重票 n=%d 胜率%.1f%% 均%.2f  票数明细(前12)=%s'%(len(fw),100.0*wn/len(fw),sum(fw)/len(fw),[(c,seen[c]) for c in list(seen)[:12]]))
    print('   窗口内明细(近12):',[(t,c,round(na/1e4),round(nb/1e4),nm) for t,c,na,nb,nm in hs[-12:]])
