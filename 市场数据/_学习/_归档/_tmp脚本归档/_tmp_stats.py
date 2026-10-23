# -*- coding: utf-8 -*-
import csv, json, statistics
D="D:/股票数据/市场数据/"
def rd(p):
    with open(p, encoding='utf-8-sig') as f: return list(csv.DictReader(f))
zt=rd(D+"20261023/zt_pool.csv"); g=json.load(open(D+"_学习/题材归位_20261023.json",encoding='utf-8'))["映射"]
rows=[]
for r in zt:
    c=r["代码"];a=g.get(c,{});fl=float(r["流通市值"]);fz=float(r["封板资金"])
    rows.append(dict(c=c,n=r["名称"],line=a.get("大方向"),seg=a.get("环节",""),lb=int(float(r["连板数"] or 0)),
      first=str(r["首次封板时间"]).zfill(6),zha=int(float(r["炸板次数"] or 0)),sealr=fz/fl*100,sealf=fz/1e8,
      turn=float(r["换手率"]),px=float(r["最新价"]),amt=float(r["成交额"])/1e8,fl=fl/1e8))
rob=[x for x in rows if x["line"]=="机器人"]
print("涨停总数",len(rows),"机器人",len(rob),"占比",f"{len(rob)/len(rows):.1%}")
print("机器人封单额",f"{sum(x['sealf'] for x in rob):.2f}亿 / 全场 {sum(x['sealf'] for x in rows):.2f}亿 = {sum(x['sealf'] for x in rob)/sum(x['sealf'] for x in rows):.1%}")
print("机器人成交",f"{sum(x['amt'] for x in rob):.1f}亿 / 全场 {sum(x['amt'] for x in rows):.1f}亿 = {sum(x['amt'] for x in rob)/sum(x['amt'] for x in rows):.1%}")
print("机器人封单率中位",f"{statistics.median([x['sealr'] for x in rob]):.2f}%","均值",f"{statistics.mean([x['sealr'] for x in rob]):.2f}%")
print("<1%只数",len([x for x in rob if x['sealr']<1]),"/",len(rob))
print("13:00后封",len([x for x in rob if x['first']>='130000']),f"({len([x for x in rob if x['first']>='130000'])/len(rob):.1%})")
print("<=0936",len([x for x in rob if x['first']<='093600']))
print("炸>0只数",len([x for x in rob if x['zha']>0]),"炸合计",sum(x['zha'] for x in rob),"单只最大",max(x['zha'] for x in rob))
print("炸0且封单率>=1.5%且首封>0925:",[(x['c'],x['n'],round(x['sealr'],2),x['first']) for x in rob if x['zha']==0 and x['sealr']>=1.5 and x['first']>'092500'])
print("换手>=20%:",len([x for x in rob if x['turn']>=20]))
print("二板全市场",len([x for x in rows if x['lb']==2]),"其中机器人",len([x for x in rob if x['lb']==2]))
print("首板",len([x for x in rob if x['lb']==1]))
print("机器人流通中位",f"{statistics.median([x['fl'] for x in rob]):.0f}亿","价中位",f"{statistics.median([x['px'] for x in rob]):.2f}")
# 硬端纯度
core=[x for x in rob if any(k in x["seg"] for k in ["关节","无框电机","腱绳","减速","丝杠","灵巧手","触觉","电子皮肤","六维力","IMU","轴承","骨架"])]
print("硬端真卡位(关节/电机/腱绳/灵巧手/触觉/传感器/轴承/骨架):",len(core),[(x['c'],x['n']) for x in core])
# 昨日首板晋级
g22=json.load(open(D+"_学习/题材归位_20261022.json",encoding='utf-8'))["映射"]
zt22=rd(D+"20261022/zt_pool.csv")
y=[r["代码"] for r in zt22 if g22.get(r["代码"],{}).get("大方向")=="机器人" and int(float(r["连板数"] or 0))==1]
print("昨日机器人首板",len(y),y)
adv=[c for c in y if c in {x['c'] for x in rows}]
print("其中今日再涨停",len(adv),adv, f"{len(adv)/len(y):.1%}")
# 全市场昨涨停今晋级
ally=[r["代码"] for r in zt22]
print("全市场昨涨停",len(ally),"今日再封",len([c for c in ally if c in {x['c'] for x in rows}]))
