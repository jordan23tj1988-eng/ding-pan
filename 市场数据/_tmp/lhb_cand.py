# -*- coding: utf-8 -*-
import json,csv,os
os.chdir(r"D:/股票数据/市场数据"); D='20261020'
def rd(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.DictReader(f))
lhb={}
for r in rd(f'{D}/lhb.csv'): lhb.setdefault(r['代码'],r)
zt={r['代码']:r for r in rd(f'{D}/zt_pool.csv')}
ds={x['代码']:x for x in json.load(open(f'_学习/龙虎榜双源校验_{D}.json',encoding='utf-8'))['全量']}
q=json.load(open('_学习/_龙虎榜质量库.json',encoding='utf-8'))['因子']['净买占比']['桶']
def bucket(p):
    if p<=0: return '≤0净卖'
    if p<5: return '0-5%'
    if p<10: return '5-10%'
    if p<20: return '10-20%'
    return '>20%'
codes=['300115','688608','688787','300244','002164','600267','002242','301313','002696','300466','600178','603696','920096','605488','603626','003029','603119']
print('%-7s%-9s%7s%8s%7s%-7s%-5s%-5s%8s%-6s%6s%7s%7s%7s'%('代码','名称','涨幅','净买亿','占比%','桶','判定','板','封单/成','首末封','炸','换手','流通亿','60分位'))
for c in codes:
    r=lhb[c]; p=float(r['净买额占总成交比']); amt=float(r['市场总成交额'])/1e8
    z=zt.get(c,{})
    seal=(float(z['封板资金'])/1e8/amt*100) if z and amt else None
    rows=list(csv.DictReader(open(f'_学习/_bars_cache/{c}.csv',encoding='utf-8-sig')))
    cl=[float(x['close']) for x in rows[-60:]]; cur=cl[-1]
    pos=(cur-min(cl))/(max(cl)-min(cl))*100 if max(cl)>min(cl) else 100
    print('%-7s%-9s%7.2f%8.4f%7.2f%-7s%-5s%-5s%8s%-6s%6s%7.2f%7.1f%7.1f'%(c,r['名称'],float(r['涨跌幅']),float(r['龙虎榜净买额'])/1e8,p,bucket(p),ds[c]['判定'],z.get('连板数',''),'%.1f%%'%seal if seal else '-',(z.get('首次封板时间','')+'/'+z.get('最后封板时间','')) if z else '-',z.get('炸板次数',''),float(r['换手率']),float(r['流通市值'])/1e8,pos))
    print('        桶历史 n=%d 执1胜率%.1f%% 均涨%+.2f%%'%(q[bucket(p)]['n'],q[bucket(p)]['执1胜率'],q[bucket(p)]['执1均涨']))
