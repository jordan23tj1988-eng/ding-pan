# -*- coding: utf-8 -*-
import os,json,csv,glob
ROOT=r'D:\股票数据\市场数据';L=os.path.join(ROOT,'_学习');d='20261014'
GENERIC={'机构专用','沪股通专用','深股通专用','机构','自然人','其他自然人','中小投资者','沪股通','深股通','量化基金','其他','北向资金'}
def real_seat(n):
    n=(n or '').strip()
    if not n or n in GENERIC: return False
    return ('营业部' in n) or ('分公司' in n) or ('总部' in n)
def load_bars(code):
    fp=os.path.join(L,'_bars_cache','%s.csv'%code)
    if not os.path.exists(fp): return None
    m={}
    with open(fp,encoding='utf-8') as f:
        for r in csv.DictReader(f):
            m[r['date'].replace('-','')]=(float(r['open']),float(r['close']))
    return m
BAR={}
def z1(code,t):
    if code not in BAR: BAR[code]=load_bars(code)
    m=BAR[code]
    if not m: return None
    ks=sorted(m)
    if t not in m: return None
    i=ks.index(t)
    if i+1>=len(ks): return None
    nt=ks[i+1]
    o,c=m[nt]
    if o<=0: return None
    return (c-o)/o*100.0
# 全窗 edges
files=sorted(glob.glob(os.path.join(L,'_席位动向','*.csv')))
pair={};nullset=set()
for fp in files:
    t=os.path.basename(fp)[:8]
    if t>d: continue
    byc={}
    for r in csv.DictReader(open(fp,encoding='utf-8')):
        typ=r.get('类型','') or ''
        if ('连续' in typ) or ('累计' in typ) or ('区间' in typ): continue
        if not real_seat(r.get('席位','')): continue
        try: net=float(r.get('净额') or 0)
        except Exception: net=0
        if net>=3e7: byc.setdefault(str(r['代码']).zfill(6),set()).add(r['席位'])
    for c,ss in byc.items():
        nullset.add((t,c))
        ss=sorted(ss)
        for i in range(len(ss)):
            for j in range(i+1,len(ss)):
                pair.setdefault((ss[i],ss[j]),set()).add((t,c))
def stat(hits):
    n=0;win=0;s=0.0
    for (t,c) in hits:
        r=z1(c,t)
        if r is None: continue
        n+=1;s+=r;win+= (1 if r>0 else 0)
    if n==0: return None
    return n,round(100.0*win/n,1),round(s/n,2)
# 基线
allbars=[(t,c) for (t,c) in nullset]
NALL=stat(allbars)
cal=sorted({t for t,c in nullset}); last60=cal[-60:]
rec=[x for x in allbars if x[0]>=last60[0]]
NREC=stat(rec)
print('null 全窗',NALL,' 近60日(起%s)'%last60[0],NREC)
# 找边：名字含目标关键词
def find(sub1,sub2):
    out=[]
    for (a,b),h in pair.items():
        if (sub1 in a and sub2 in b) or (sub1 in b and sub2 in a):
            out.append(((a,b),h))
    return out
tests=[('国泰海通证券股份有限公司总部','高盛(中国)'),('国新证券股份有限公司北京','开源证券股份有限公司西安西大街'),
       ('国信证券股份有限公司浙江互联网','国泰海通证券股份有限公司总部'),('中信证券股份有限公司上海分公司','国泰海通证券股份有限公司总部'),
       ('瑞银证券','高盛(中国)')]
for s1,s2 in tests:
    for (a,b),h in find(s1,s2):
        allst=stat(h); rst=stat([x for x in h if x[0]>=last60[0]])
        print('EDGE',a,'||',b)
        print('   全窗',allst,' 近60日',rst,' 边样本数(hits)',len(h))
# 单席分档
rk=json.load(open(os.path.join(L,'_席位分档.json'),encoding='utf-8'))
print('基准',rk['基准'],'窗口',rk['窗口'],'笔数',rk['笔数'])
for k,v in rk['席位'].items():
    if any(s in k for s in ['国泰海通证券股份有限公司总部','高盛(中国)','国新证券股份有限公司北京','开源证券股份有限公司西安西大街','国信证券股份有限公司浙江互联网','中信证券股份有限公司上海分公司']):
        print('SEAT',k,'|',v.get('档'),'n=',v.get('样本'),v.get('执1胜率'),v.get('执1均涨'),'通道=',v.get('通道'),'小样本=',v.get('小样本'))
