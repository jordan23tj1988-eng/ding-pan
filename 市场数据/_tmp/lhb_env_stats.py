# -*- coding: utf-8 -*-
import json,csv,os,collections,statistics
os.chdir(r"D:/股票数据/市场数据")
T=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
rows=[json.loads(l) for l in open('_学习/_席位荐票反思.jsonl',encoding='utf-8') if l.strip()]
buck=collections.defaultdict(lambda:[0,0,[],0])
for r in rows:
    d=r['荐票日']; w=r.get('执行胜率') or '0/0'
    a,b=w.split('/'); a=int(a); b=int(b)
    if b==0: continue
    env=(T.get(d) or {}).get('温度档','?')
    k=buck[env]; k[0]+=a; k[1]+=b; k[2].append(r['均收']); k[3]+=1
print('环境档(按荐票日温度档) 笔胜率 均收 天数')
for env,(a,b,ms,n) in sorted(buck.items(),key=lambda x:-x[1][1]):
    print('%-6s %d/%d=%.1f%%  均收%+.2f%%  日数%d  日均收%+.2f%%'%(env,a,b,100*a/b,statistics.mean(ms),n,statistics.mean(ms)))
# 20261020 档
t=T['20261020']; print('今日',t['温度档'],t['温度'],'涨停',t['涨停数'],'跌停',t['跌停数'],'炸板率',t['炸板率'],'最高板',t['最高板'],'二板加',t['二板加'])
print()
# 昨日观察票结算
for c in ['603286','002343']:
    rs=list(csv.DictReader(open(f'_学习/_bars_cache/{c}.csv',encoding='utf-8-sig')))
    for x in rs[-3:]: print(c,x['date'],'开',x['open'],'收',x['close'],'高',x['high'],'低',x['low'])
    y=[x for x in rs if x['date']=='2026-10-19'][0]; t2=rs[-1]
    print('  执1(20261020开→收)=%+.2f%%'%((float(t2['close'])/float(t2['open'])-1)*100))
print()
# 持仓
for c,buy in [('600802',6.88),('001696',16.00)]:
    rs=list(csv.DictReader(open(f'_学习/_bars_cache/{c}.csv',encoding='utf-8-sig')))
    for x in rs[-2:]: print(c,x['date'],'开',x['open'],'收',x['close'],'高',x['high'],'低',x['low'])
    t2=rs[-1]; print('  相对买入%+.2f%%  今日执1%+.2f%%'%((float(t2['close'])/buy-1)*100,(float(t2['close'])/float(t2['open'])-1)*100))
