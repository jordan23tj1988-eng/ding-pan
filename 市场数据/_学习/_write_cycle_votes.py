import json, os
root='D:/股票数据/市场数据'; L=os.path.join(root,'_学习'); d='20260908'
main={'date':d,'stage':'退潮','direction':'降','evidence':'温度42.3偏冷、炸板率33.6%、封板率66.4%、最高4板且主线未确认；来源=_学习/fact_20260908.json、_学习/总审_20260908.json'}
votes={
 'auction':('退潮','降','竞价一字强度未转化为可执行承接，采纳防守'),
 'lhb':('退潮','平','B档局部净买但S档0席，保留分歧观察'),
 'theme':('退潮','降','73只归位全B行业兜底，无可确认主线'),
 'logic':('退潮','降','业绩雷达与风险日历缺口，产业逻辑不可升级'),
 'limitup':('退潮','降','炸板37、封板率66.4%、质量执1最高45.9%未过门槛')}
with open(os.path.join(L,'周期主判_'+d+'.json'),'w',encoding='utf-8') as f: json.dump(main,f,ensure_ascii=False,indent=1)
for r,(stage,direction,evidence) in votes.items():
 with open(os.path.join(L,f'周期投票_{r}_{d}.json'),'w',encoding='utf-8') as f: json.dump({'date':d,'route':r,'stage':stage,'direction':direction,'confidence':None,'evidence':evidence},f,ensure_ascii=False,indent=1)
print('cycle votes written')
