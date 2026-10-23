# -*- coding: utf-8 -*-
import csv,os,json,statistics as st
days=sorted(d for d in os.listdir('.') if d.isdigit() and len(d)==8 and os.path.isdir(d) and os.path.isfile(os.path.join(d,'zt_pool.csv')))
pools={}
for d in days:
    rows=list(csv.DictReader(open(f'{d}/zt_pool.csv',encoding='utf-8-sig')))
    m={}
    for r in rows:
        c=str(r['代码']).strip().zfill(6)
        try: fb=float(r['封板资金']); amt=float(r['成交额']); fmc=float(r['流通市值'])
        except: fb=amt=fmc=None
        m[c]=dict(name=r['名称'],lb=int(float(r['连板数'] or 0)),zt=r['涨停统计'],
                  tb=int(float(r['炸板次数'] or 0)),fb=fb,amt=amt,fmc=fmc,
                  first=r['首次封板时间'],last=r['最后封板时间'],
                  hs=float(r['换手率']) if r['换手率'] else None)
    pools[d]=m
print('days',len(days),days[0],days[-1])
def shape_rate(name, pred, minn=8):
    hit=tot=0; nxt_n=0
    for i,d in enumerate(days[:-1]):
        nd=days[i+1]; codes=pools[nd]
        for c,x in pools[d].items():
            if pred(x):
                tot+=1
                if c in codes: hit+=1
    print(f"{name}: n={tot} 次日封板率={hit/tot:.3f} ({hit}/{tot})" if tot else f"{name}: n=0")

shape_rate("连板>=5", lambda x: x['lb']>=5)
shape_rate("连板==6", lambda x: x['lb']==6)
shape_rate("连板>=2", lambda x: x['lb']>=2)
shape_rate("首板", lambda x: x['lb']==1)
shape_rate("首板+封单/成交>=5%+炸<=1+首封<=14:00", lambda x: x['lb']==1 and x['fb'] and x['amt'] and x['fb']/x['amt']>=0.05 and x['tb']<=1 and x['first']<='140000')
shape_rate("首板+炸>=3+封单/流通<1%", lambda x: x['lb']==1 and x['tb']>=3 and x['fb'] and x['fmc'] and x['fb']/x['fmc']<0.01)
shape_rate("2板+封单/流通>=4%+炸1", lambda x: x['lb']==2 and x['fb'] and x['fmc'] and x['fb']/x['fmc']>=0.04 and x['tb']==1)
shape_rate("2板", lambda x: x['lb']==2)
shape_rate("2板+炸>=4+换手10-20", lambda x: x['lb']==2 and x['tb']>=4 and x['hs'] and 10<=x['hs']<=20)
shape_rate("首板+炸>=5+换手10-20+封单/流通<0.5%", lambda x: x['lb']==1 and x['tb']>=5 and x['hs'] and 10<=x['hs']<=20 and x['fb'] and x['fmc'] and x['fb']/x['fmc']<0.005)
shape_rate("首板+晚封(>=13:00)+炸0", lambda x: x['lb']==1 and x['first']>='130000' and x['tb']==0)
shape_rate("首板+封单/流通>=1%+炸0+首封>=14:00", lambda x: x['lb']==1 and x['fb'] and x['fmc'] and x['fb']/x['fmc']>=0.01 and x['tb']==0 and x['first']>='140000')
shape_rate("3板+一字", lambda x: x['lb']==3 and x['first']<='092600' and x['tb']==0 and x['first']==x['last'])
shape_rate("6板+炸>=4", lambda x: x['lb']>=6 and x['tb']>=4)

# 一进二率 next day after high 一进二
S=json.load(open('_学习/_情绪先行指标.json',encoding='utf-8'))
tdays=sorted(d for d in S if S[d].get('晋级',{}).get('一进二率') is not None)
print('\n先行指标可用日',len(tdays),tdays[0],tdays[-1])
seq=[(d,S[d]['晋级']['一进二率']) for d in tdays]
for th in [0.15,0.18,0.20,0.25,0.30]:
    nx=[S[tdays[i+1]]['晋级']['一进二率'] for i in range(len(tdays)-1) if S[tdays[i]]['晋级']['一进二率']>=th]
    if nx:
        print(f"当日一进二>={th}: 次日均={st.mean(nx):.3f} 中位={st.median(nx):.3f} n={len(nx)} 次日>=0.20者={sum(1 for v in nx if v>=0.20)}/{len(nx)} 次日>=0.25者={sum(1 for v in nx if v>=0.25)}/{len(nx)}")
print("近8日一进二:", [(d,round(v,3)) for d,v in seq[-8:]])
# 二进三
seq3=[(d,S[d]['晋级'].get('二进三率')) for d in tdays]
nx3=[S[tdays[i+1]]['晋级'].get('二进三率') for i in range(len(tdays)-1) if (S[tdays[i]]['晋级'].get('一进二率') or 0)>=0.30]
print("一进二>=0.30 时次日二进三:", nx3, sum(1 for v in nx3 if v and v>=0.20),'/',len(nx3))

print("\n--- 补充形态 ---")
shape_rate("连板>=5+换手>=25", lambda x: x['lb']>=5 and x['hs'] and x['hs']>=25)
shape_rate("连板>=5+封单/流通<2%", lambda x: x['lb']>=5 and x['fb'] and x['fmc'] and x['fb']/x['fmc']<0.02)
shape_rate("连板>=6+炸0", lambda x: x['lb']>=6 and x['tb']==0)
shape_rate("连板>=4+首封>=13:00", lambda x: x['lb']>=4 and x['first']>='130000')
shape_rate("3板+一字+封单/流通>=2%", lambda x: x['lb']==3 and x['first']<='092600' and x['first']==x['last'] and x['fb'] and x['fmc'] and x['fb']/x['fmc']>=0.02)
shape_rate("2板+封单/流通>=2%+首封<=10:00", lambda x: x['lb']==2 and x['fb'] and x['fmc'] and x['fb']/x['fmc']>=0.02 and x['first']<='100000')
