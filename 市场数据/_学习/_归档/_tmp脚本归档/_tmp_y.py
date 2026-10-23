# -*- coding: utf-8 -*-
import csv,json
D="D:/股票数据/市场数据/"
zt=list(csv.DictReader(open(D+"20261022/zt_pool.csv",encoding='utf-8-sig')))
g=json.load(open(D+"_学习/题材归位_20261022.json",encoding='utf-8'))["映射"]
rob=[r for r in zt if g.get(r["代码"],{}).get("大方向")=="机器人"]
print("n",len(rob))
aft=[r for r in rob if str(r["首次封板时间"]).zfill(6)>="130000"]
print("13:00后封",len(aft),[(r["名称"],r["首次封板时间"]) for r in aft])
thin=[r for r in rob if float(r["封板资金"])/float(r["流通市值"])*100<1]
print("<1%",len(thin))
z=max(rob,key=lambda r:int(float(r["炸板次数"] or 0)))
print("最大炸",z["名称"],z["炸板次数"])
early=[r for r in rob if str(r["首次封板时间"]).zfill(6)<="093600"]
print("<=0936",len(early))
