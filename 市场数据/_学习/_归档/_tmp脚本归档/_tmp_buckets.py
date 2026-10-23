import csv,json
from collections import Counter,defaultdict
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
rows=[r for r in csv.DictReader(open('20261023/lhb.csv',encoding='utf-8-sig')) if not is_int(r['上榜原因'])]
st=[r for r in rows if r['代码'][:2] not in ('11','12')]
def pct(r): return float(r['净买额占总成交比'])*100 if float(r['净买额占总成交比'])<1 else float(r['净买额占总成交比'])
b=defaultdict(list)
for r in st:
    p=pct(r)
    k='≤0' if p<=0 else ('0-5%' if p<=5 else ('5-10%' if p<=10 else ('10-20%' if p<=20 else '>20%')))
    b[k].append((r['代码'],r['名称'],round(p,2)))
for k in ['≤0','0-5%','5-10%','10-20%','>20%']:
    print(k,len(b[k]),b[k][:6])
print('股票码',len(st))
# S/A 明细
zt={r['代码']:r for r in csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig'))}
seats=list(csv.DictReader(open('_学习/_席位动向/20261023.csv',encoding='utf-8')))
dd=[r for r in seats if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
seen=set();Q=[]
for r in dd:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k);Q.append(r)
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
ds={r['代码']:r['判定'] for r in json.load(open('_学习/龙虎榜双源校验_20261023.json',encoding='utf-8'))['全量']}
src1={r['代码']:float(r['净买额占总成交比'])*100 for r in st}
print('--- S/A 笔(净买>0 ∧ 买额>=1000万) ---')
for r in sorted(Q,key=lambda x:-float(x['买入金额'])):
    v=pj.get(r['席位'])
    if not v or v['档'] not in ('S','A'): continue
    if float(r['净额'])<=0 or float(r['买入金额'])<1e7: continue
    z=zt.get(r['代码'])
    fb=(float(z['封板资金'])/float(z['成交额'])*100) if z else None
    print(f"{r['代码']} {r['名称'][:5]} | {v['档']}/{v['样本']} 收缩{v['收缩执1胜率']}/{v['收缩执1均涨']} | {r['席位'][:22]} 买{float(r['买入金额'])/1e8:.3f} 净{float(r['净额'])/1e8:.3f} | 源1占比{src1.get(r['代码'],0):.2f}% 双源{ds.get(r['代码'],'NA')} | 涨停={'Y' if z else 'N'} 封单{fb if fb is None else round(fb,2)} 炸{z['炸板次数'] if z else '-'}")
