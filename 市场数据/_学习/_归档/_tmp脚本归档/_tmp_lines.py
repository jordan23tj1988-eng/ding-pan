# -*- coding: utf-8 -*-
import csv, json, statistics
D="D:/股票数据/市场数据/"
def rd(p):
    with open(p, encoding='utf-8-sig') as f: return list(csv.DictReader(f))
zt=rd(D+"20261023/zt_pool.csv"); g=json.load(open(D+"_学习/题材归位_20261023.json",encoding='utf-8'))["映射"]
rows=[]
for r in zt:
    c=r["代码"]; a=g.get(c,{})
    fl=float(r["流通市值"]); fz=float(r["封板资金"])
    rows.append(dict(c=c,n=r["名称"],line=a.get("大方向","未归位"),seg=a.get("环节",""),lb=int(float(r["连板数"] or 0)),
        first=str(r["首次封板时间"]).zfill(6), zha=int(float(r["炸板次数"] or 0)), sealr=fz/fl*100 if fl else 0,
        turn=float(r["换手率"]), px=float(r["最新价"]), amt=float(r["成交额"])/1e8, fl=fl/1e8))
by={}
for x in rows: by.setdefault(x["line"],[]).append(x)
for k,v in sorted(by.items(), key=lambda kv:-len(kv[1])):
    if k=="机器人": continue
    print(f"\n### {k} n={len(v)}")
    for x in sorted(v,key=lambda y:(-y["lb"],-y["sealr"])):
        print(f"  {x['c']} {x['n']:6s} {x['lb']}板 {x['first']} 炸{x['zha']} 封{x['sealr']:.2f}% 换{x['turn']:.1f}% 价{x['px']:.2f} 流通{x['fl']:.0f}亿 成交{x['amt']:.1f}亿 | {x['seg']}")
# 机器人 sub cluster
import re
def sub(x):
    s=x["seg"]
    if any(k in s for k in ["本体","物理AI","具身智能","数字孪生","动捕","数字展示","智慧交通","智慧驾培","工业软件","工业智能","文体旅","机器人乐队","工业缝纫","智能包装","工业自动化","智能交通"]): return "软端(物理AI/具身智能/集成)"
    if any(k in s for k in ["轴承","电机","关节","腱绳","减速","丝杠","触觉","电子皮肤","灵巧手","传感器","IMU","零部件","模组","骨架","丝","精"]): return "硬端(零部件)"
    return "跨界/混合"
print("\n### 机器人 37 子簇")
from collections import Counter
cnt=Counter(sub(x) for x in by["机器人"])
print(cnt)
for x in sorted(by["机器人"],key=lambda y:(sub(y),-y["lb"],-y["sealr"])):
    print(f"  [{sub(x)[:6]}] {x['c']} {x['n']:6s} {x['lb']}板 {x['first']} 炸{x['zha']} 封{x['sealr']:.2f}% 换{x['turn']:.1f}% | {x['seg']}")
# 下午封统计
aft=[x for x in by["机器人"] if x["first"]>="130000"]
print("\n机器人 13:00后封:",len(aft),"/",len(by["机器人"]))
print("机器人 <=0936:",len([x for x in by["机器人"] if x["first"]<="093600"]))
print("机器人 首板:",len([x for x in by["机器人"] if x["lb"]==1]),"2板:",len([x for x in by["机器人"] if x["lb"]==2]))
