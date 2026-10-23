# -*- coding: utf-8 -*-
import json
t=json.load(open('D:/股票数据/市场数据/_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(k for k in t if str(k).isdigit())
w=days[-250:]
def pct(field,val,win=w):
    xs=[t[k][field] for k in win if isinstance(t[k].get(field),(int,float))]
    return 100.0*len([x for x in xs if x<val])/len(xs), len(xs)
for f,v in [('成交额亿',19563.0),('温度',53.2),('跌停数',6),('封板总额亿',62.8),('炸板率',0.128),('涨停数',82)]:
    p,n=pct(f,v); print('%s=%s 250日分位 %.2f%% (n=%d)'%(f,v,p,n))
p,n=pct('跌停数',49); print('昨跌停49 分位 %.2f%% (n=%d)'%(p,n))
# 52日/全窗
days_all=days
def pct_all(field,val):
    xs=[t[k][field] for k in days_all if isinstance(t[k].get(field),(int,float))]
    return 100.0*len([x for x in xs if x<val])/len(xs),len(xs)
for f,v in [('成交额亿',19563.0),('温度',53.2),('封板总额亿',62.8)]:
    p,n=pct_all(f,v); print('全窗 %s 分位 %.2f%% n=%d'%(f,p,n))
# 封板率序列
print('封板率最近8日',[(k, round(t[k]['涨停数']/(t[k]['涨停数']+t[k]['炸板数']),4)) for k in days[-8:]])
