# -*- coding: utf-8 -*-
import json, os, csv, statistics
M = r"D:\股票数据\市场数据"
def R(p):
    with open(p,encoding="utf-8-sig") as f: return list(csv.DictReader(f))
zt=R(os.path.join(M,"20261016","zt_pool.csv")); zb=R(os.path.join(M,"20261016","zb_pool.csv")); dt=R(os.path.join(M,"20261016","dt_pool.csv"))
def f(x):
    try: return float(x)
    except: return None
print("== 涨停池 61 ==")
lb=statistics.mean([f(z["连板数"]) for z in zt]); print("平均连板 %.2f"%lb)
print("首封时间<=093000:", sum(1 for z in zt if z["首次封板时间"]<="093000"), " ==092500一字:",sum(1 for z in zt if z["首次封板时间"]=="092500"))
print("9:31-10:00:", sum(1 for z in zt if "093000"<z["首次封板时间"]<="100000"))
print("10:00-13:00:", sum(1 for z in zt if "100000"<z["首次封板时间"]<="130000"))
print("13:00后:", sum(1 for z in zt if z["首次封板时间"]>"130000"))
print("炸板次数0(未开板):", sum(1 for z in zt if z["炸板次数"]=="0"))
print("换手中位 %.2f 均值 %.2f"%(statistics.median([f(z["换手率"]) for z in zt]),statistics.mean([f(z["换手率"]) for z in zt])))
print("流通市值中位 %.1f亿"%(statistics.median([f(z["流通市值"])/1e8 for z in zt])))
# 封单比
zbf=[]
for z in zt:
    c=f(z["封板资金"]); mc=f(z["流通市值"])
    zbf.append((c/mc*100, z["代码"], z["名称"], z["连板数"], z["首次封板时间"], f(z["换手率"])))
zbf.sort(reverse=True)
print("封单比>2%%: %d, >5%%: %d, <1%%: %d"%(sum(1 for x in zbf if x[0]>2),sum(1 for x in zbf if x[0]>5),sum(1 for x in zbf if x[0]<1)))
print("封单比Top8:", [("%s %s %.2f%% 连%s 首封%s"%(x[1],x[2],x[0],x[3],x[4])) for x in zbf[:8]])
# 连板>=2 列表
print("\n连板>=2:")
for z in sorted([z for z in zt if f(z["连板数"])>=2], key=lambda x:-f(x["连板数"])):
    print("  %s %s 连%s 首封%s 开板%s 换手%.2f 封单%.2f亿 市值%.0f亿 行业%s 涨停统计%s 涨跌%.2f"%(z["代码"],z["名称"],z["连板数"],z["首次封板时间"],z["炸板次数"],f(z["换手率"]),f(z["封板资金"])/1e8,f(z["流通市值"])/1e8,z["所属行业"],z["涨停统计"],f(z["涨跌幅"])))
print("\n== 炸板池 49 ==")
print("平均涨跌 %.2f%% 中位 %.2f%%"%(statistics.mean([f(z["涨跌幅"]) for z in zb]),statistics.median([f(z["涨跌幅"]) for z in zb])))
print("炸板后翻绿(<0):", sum(1 for z in zb if f(z["涨跌幅"])<0), " 收在>5%%:", sum(1 for z in zb if f(z["涨跌幅"])>5))
print("平均炸板次数 %.2f"%statistics.mean([f(z["炸板次数"]) for z in zb]))
print("首封<=9:30 的炸板:", sum(1 for z in zb if z["首次封板时间"]<="093000"))
prev=[z for z in zb if "/" in z.get("涨停统计","") and z["涨停统计"].split("/")[0]!="1"]
print("昨日有涨停(涨停统计m/n m>1)的炸板:", len(prev))
for z in sorted(zb,key=lambda x:f(x["涨跌幅"]))[:6]:
    print("  最惨 %s %s %.2f%% 涨停统计%s 炸板%s次 换手%.1f 行业%s"%(z["代码"],z["名称"],f(z["涨跌幅"]),z["涨停统计"],z["炸板次数"],f(z["换手率"]),z["所属行业"]))
