# -*- coding: utf-8 -*-
"""低开细拆回测(临时,操盘手审核A4项): 一年竞价池样本,低开档细拆 0~-2 / -2~-5 / ≤-5"""
import importlib.util, os, json
spec=importlib.util.spec_from_file_location("bf","竞价池分桶回填.py")
bf=importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)

ths=json.load(open("_学习/_ths_zt_pool.json",encoding="utf-8"))
days=sorted(ths.keys())
S=[]
for di,d in enumerate(days[:-1]):
    dnext=days[di+1]
    for t in bf.build_pool(ths[d]):
        r=bf.settle(t["代码"],d,dnext)
        if r is None: continue
        gk,ex,sg,mv=r
        S.append(dict(g=gk,ex=ex,lb=t["连板"],sig=t["信号"].split("·")[0]))

def fine(g):
    if g>0: return None
    if g>=-2: return "微低开0~-2"
    if g>=-5: return "中低开-2~-5"
    return "深低开≤-5"
def stat(sub):
    if not sub: return "n=0"
    ex=[s["ex"] for s in sub]
    import numpy as np
    return "n=%-4d 均收%+.2f%% 胜率%.1f%%"%(len(ex),sum(ex)/len(ex),100*sum(1 for e in ex if e>0)/len(ex))

low=[s for s in S if s["g"]<=0]
print("低开全体(≤0):", stat(low))
for tag in ["微低开0~-2","中低开-2~-5","深低开≤-5"]:
    sub=[s for s in low if fine(s["g"])==tag]
    print("%-10s"%tag, stat(sub))
print()
print("深低开≤-5 按信号:")
for sig in ["一字","秒板"]:
    print(" ",sig, stat([s for s in low if fine(s["g"])=="深低开≤-5" and s["sig"]==sig]))
print("深低开≤-5 按连板:")
for lo,hi,tag in [(1,1,"首板"),(2,2,"2板"),(3,99,"3板+")]:
    print(" ",tag, stat([s for s in low if fine(s["g"])=="深低开≤-5" and lo<=s["lb"]<=hi]))
# 顺带: -3以下逐档看单调性
print()
for lo_,hi_,tag in [(-3,-2,"-2~-3"),(-4,-3,"-3~-4"),(-5,-4,"-4~-5"),(-99,-5,"≤-5")]:
    print("%-6s"%tag, stat([s for s in low if lo_<=s["g"]<hi_ if True] if False else [s for s in low if lo_< s["g"]<=hi_]))
