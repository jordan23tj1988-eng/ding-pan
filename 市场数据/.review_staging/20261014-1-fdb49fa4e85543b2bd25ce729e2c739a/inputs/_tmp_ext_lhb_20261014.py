# -*- coding: utf-8 -*-
import os,json,csv,glob
ROOT=r'D:\股票数据\市场数据'
L=os.path.join(ROOT,'_学习')
d='20261014'
cal=sorted(x for x in os.listdir(ROOT) if len(x)==8 and x.isdigit())
days3=[x for x in cal if x<=d][-3:]
print('cal tail:',cal[-8:]);print('days3:',days3)
GENERIC={'机构专用','沪股通专用','深股通专用','机构','自然人','其他自然人','中小投资者','沪股通','深股通','量化基金','其他','北向资金'}
def real_seat(n):
    n=(n or '').strip()
    if not n or n in GENERIC: return False
    return ('营业部' in n) or ('分公司' in n) or ('总部' in n)
def rows_of(t):
    fp=os.path.join(L,'_席位动向','%s.csv'%t); out=[]
    if not os.path.exists(fp): return out
    with open(fp,encoding='utf-8') as f:
        for r in csv.DictReader(f):
            typ=r.get('类型','') or ''
            if ('连续' in typ) or ('累计' in typ) or ('区间' in typ): continue
            if not real_seat(r.get('席位','')): continue
            try: net=float(r.get('净额') or 0)
            except Exception: net=0
            out.append({'seat':r['席位'],'code':str(r.get('代码','')).zfill(6),'net':net,'name':r.get('名称','')})
    return out
# 3日窗口内的边
pair={};pool3={}
for t in days3:
    byc={}
    for r in rows_of(t):
        if r['net']>=3e7: byc.setdefault(r['code'],set()).add(r['seat'])
    for c,ss in byc.items():
        pool3.setdefault(t,set()).add(c)
        ss=sorted(ss)
        for i in range(len(ss)):
            for j in range(i+1,len(ss)):
                pair.setdefault((ss[i],ss[j]),[]).append((t,c))
targets=[('国泰海通证券股份有限公司总部','高盛(中国)证券有限责任公司'),
         ('国新证券股份有限公司北京分公司','开源证券股份有限公司西安西大街证券营业部'),
         ('国信证券股份有限公司浙江互联网分公司','国泰海通证券股份有限公司总部'),
         ('中信证券股份有限公司上海分公司','国泰海通证券股份有限公司总部')]
print('\n== 3日窗口 目标边 ==')
for a,b in targets:
    hits=pair.get((a,b)) or pair.get((b,a)) or []
    print(a,'X',b,'->',len(hits),sorted(hits))
print('\n== 3日窗口 全部边(>=2) ==')
for k,v in sorted(pair.items(),key=lambda x:-len(x[1])):
    if len(v)>=2: print(len(v),k[0][:16],'X',k[1][:16],sorted(v)[:6])
print('\n== 池大小 ==')
for t in days3: print(t,len(pool3.get(t,set())),sorted(pool3.get(t,set()))[:5])
# 零模型期望
import itertools
for a,b in targets:
    exp=0
    for t in days3:
        Na=len({r['code'] for r in rows_of(t) if r['seat']==a and r['net']>=3e7})
        Nb=len({r['code'] for r in rows_of(t) if r['seat']==b and r['net']>=3e7})
        P=len(pool3.get(t,set()))
        if P: exp+=Na*Nb/P
    print('零模型期望',a[:12],'x',b[:12],'=',round(exp,2))
