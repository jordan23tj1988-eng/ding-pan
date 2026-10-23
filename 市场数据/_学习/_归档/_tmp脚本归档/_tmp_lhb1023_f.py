import csv,json,os
from statistics import mean,median
D='20261023'; Y='20261022'
def bars(c):
    p=f'_学习/_bars_cache/{c}.csv'
    if not os.path.exists(p): return None
    rows=[]
    for line in open(p,encoding='utf-8'):
        parts=line.strip().split(',')
        if len(parts)<6 or parts[0]=='date': continue
        try: rows.append((parts[0],float(parts[1]),float(parts[2]),float(parts[3]),float(parts[4])))
        except: pass
    return rows
def day(c,d):
    b=bars(c)
    if not b: return None
    for i,r in enumerate(b):
        if r[0].replace('-','')==d:
            prev=b[i-1][4] if i>0 else None
            return {'open':r[1],'high':r[2],'low':r[3],'close':r[4],'prev':prev}
    return None
# 昨日涨停票今日执1
ztY=[r['代码'] for r in csv.DictReader(open(f'{Y}/zt_pool.csv',encoding='utf-8-sig'))]
res=[];miss=[]
for c in ztY:
    t=day(c,D)
    if not t or t['prev'] is None: miss.append(c); continue
    if t['open']==t['high']==t['low']: continue  # 不可成交剔除
    res.append((c,(t['close']-t['open'])/t['open']*100,(t['close']-t['prev'])/t['prev']*100,(t['open']-t['prev'])/t['prev']*100))
print(f'昨涨停 {len(ztY)} 只，可成交 {len(res)}，缺价 {len(miss)}')
ex=[x[1] for x in res]
print(f'执1(开→收) 均收 {mean(ex):.2f}% 中位 {median(ex):.2f}% 胜率 {sum(1 for x in ex if x>0)}/{len(ex)}={sum(1 for x in ex if x>0)/len(ex)*100:.1f}%')
print(f'昨收→今收 均 {mean([x[2] for x in res]):.2f}%')
print(f'隔夜gap 均 {mean([x[3] for x in res]):.2f}%  gap>=9.5%只数 {sum(1 for x in res if x[3]>=9.5)}')
# 连板晋级：昨日连板>=2今日是否涨停
ztT={r['代码'] for r in csv.DictReader(open(f'{D}/zt_pool.csv',encoding='utf-8-sig'))}
y2=[r for r in csv.DictReader(open(f'{Y}/zt_pool.csv',encoding='utf-8-sig')) if int(r['连板数'])>=2]
print('昨连板>=2',len(y2),'今日仍涨停',sum(1 for r in y2 if r['代码'] in ztT))
y1=[r for r in csv.DictReader(open(f'{Y}/zt_pool.csv',encoding='utf-8-sig')) if int(r['连板数'])==1]
print('昨首板',len(y1),'今日涨停(晋级)',sum(1 for r in y1 if r['代码'] in ztT),f'{sum(1 for r in y1 if r["代码"] in ztT)/len(y1)*100:.1f}%')
# 002639 / 观察池
for c,nm in [('002639','雪人集团'),('300839','博汇股份'),('000678','襄阳轴承'),('600192','长城电工'),('300296','利亚德'),('603721','中广天择'),('002354','天娱数科'),('301660','粤芯半导'),('600215','派斯林'),('600303','曙光股份')]:
    t=day(c,D); y=day(c,Y)
    if not t: print(c,nm,'无今日K'); continue
    print(f"{c} {nm} 昨收{y['close'] if y else 'NA'} 今开{t['open']} 今高{t['high']} 今低{t['low']} 今收{t['close']} 执1={((t['close']-t['open'])/t['open']*100):.2f}% gap={((t['open']-t['prev'])/t['prev']*100):.2f}% vs昨收={((t['close']-t['prev'])/t['prev']*100):.2f}%")
