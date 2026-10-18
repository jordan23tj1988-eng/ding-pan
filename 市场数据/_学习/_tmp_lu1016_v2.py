# -*- coding: utf-8 -*-
import json, os, csv
B=r"D:\股票数据\市场数据\_学习"; M=r"D:\股票数据\市场数据"
q=json.load(open(os.path.join(B,"涨停质量荐票_20261016.json"),encoding="utf-8"))
det={r["代码"]:r for r in q["明细"]}
print("打标数",len(det))
for c in ["000530","300045","301586","600802","002917","920006","600825","600668","003029","002815"]:
    r=det.get(c)
    if not r: print(c,"缺");continue
    print(c,r["名称"],{k:v for k,v in r.items() if k in ("首封","连板","开板次数","命中数","封单比","换手","市值亿","封单额亿","质量分","预测执1胜率","预测执1均涨","预测执2均涨","来源档","大方向")})
print("\n命中数>0:",[(r["代码"],r["名称"],r["命中数"]) for r in q["明细"] if r.get("命中数",0)>0])
print("封单比>5%:",[(r["代码"],r["名称"],r["封单比"]) for r in q["明细"] if r["封单比"]>5])
print("封单比>2% n=",sum(1 for r in q["明细"] if r["封单比"]>2),"<1% n=",sum(1 for r in q["明细"] if r["封单比"]<1))
print("封单额>=4亿:",[(r["代码"],r["名称"],r["封单额亿"]) for r in q["明细"] if r["封单额亿"]>=4])
print("封单额>=2亿 n=",sum(1 for r in q["明细"] if r["封单额亿"]>=2))
e1=[r["预测执1均涨"] for r in q["明细"]]; s1=[r["预测执1胜率"] for r in q["明细"]]
import statistics as st
print("执1均涨 mean %.3f max %.2f min %.2f | 胜率 max %.1f min %.1f median %.1f mean %.1f | >50 %d | 均涨>0 %d"%(
 st.mean(e1),max(e1),min(e1),max(s1),min(s1),st.median(s1),st.mean(s1),sum(1 for x in s1 if x>50),sum(1 for x in e1 if x>0)))
z=list(csv.DictReader(open(os.path.join(M,"20261016","zt_pool.csv"),encoding="utf-8-sig")))
print("\nzt_pool行数",len(z))
import collections
def fb(x):
    t=x[:5]
    return "0925" if t=="09:25" else ("<=0930" if t<="09:30" else ("0931-1000" if t<="10:00" else ("1000-1300" if t<="13:00" else ">1300")))
c=collections.Counter(fb(r["首次封板时间"]) for r in z); print("首封分布",dict(c))
print("未开板",sum(1 for r in z if r["炸板次数"]=="0"),"开板>=1",sum(1 for r in z if r["炸板次数"]!="0"))
print("换手中位 %.2f 均 %.2f | 市值中位 %.1f"%(st.median([float(r["换手率"]) for r in z]),st.mean([float(r["换手率"]) for r in z]),st.median([float(r["流通市值"])/1e8 for r in z])))
for c2 in ["000530","300045","301586"]:
    for r in z:
        if r["代码"]==c2: print(c2,r)
print("\n-- 昨日池 000530 行")
for r in csv.DictReader(open(os.path.join(M,"20261015","zt_pool.csv"),encoding="utf-8-sig")):
    if r["代码"]=="000530": print(r)
print("\n-- 昨日明细 000530")
q15=json.load(open(os.path.join(B,"涨停质量荐票_20261015.json"),encoding="utf-8"))
for r in q15["明细"]:
    if r["代码"]=="000530": print(r)
print("\n-- 战绩画像")
p=json.load(open(os.path.join(B,"子agent增强","战绩画像_limitup_20261016.json"),encoding="utf-8"))
print(list(p.keys()))
print(json.dumps(p.get("合计"),ensure_ascii=False)[:600])
print("\n-- 模拟盘")
s=json.load(open(os.path.join(B,"_模拟盘","limitup","状态.json"),encoding="utf-8"))
print(json.dumps(s,ensure_ascii=False)[:800])
