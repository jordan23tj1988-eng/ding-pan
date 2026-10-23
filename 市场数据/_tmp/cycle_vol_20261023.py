# -*- coding: utf-8 -*-
import json
t=json.load(open('D:/股票数据/市场数据/_学习/_市场温度表.json',encoding='utf-8'))
vals=[(k,v.get('成交额亿')) for k,v in t.items() if str(k).isdigit() and isinstance(v.get('成交额亿'),(int,float))]
vals.sort()
print('n=',len(vals))
cur=19563.0
below=[v for k,v in vals if v<cur]
print('低于当前的日数 %d / %d = 分位%.2f%%'%(len(below),len(vals),100*len(below)/len(vals)))
import statistics as st
print('中位 %.1f'%st.median([v for k,v in vals]))
# 最近20日
print('最近12日序列:',[(k,v.get('成交额亿'),v.get('温度')) for k,v in sorted(t.items()) if str(k).isdigit()][-12:])
# 温度分位
temps=sorted(v['温度'] for k,v in t.items() if str(k).isdigit() and isinstance(v.get('温度'),(int,float)))
print('温度53.2 分位 %.2f%%'%(100*len([x for x in temps if x<53.2])/len(temps)))
# 封板率
print('封板率 82/(82+12)=%.4f'%(82/94))
# 距门槛
print('距2万亿 %d亿; 占3万亿 %.1f%%; 距3万亿 %d亿'%(20000-19563,19563/30000*100,30000-19563))
print('距3.3万亿 %d亿'%(33000-19563))
# 名义高度插值 1.7(9-11) -> 2.0(11+)
frac=(1.9563-1.7)/0.3
print('frac=%.3f 名义下沿 %.2f 上沿 %.2f'%(frac,9+frac*2,11+frac*0.5))
