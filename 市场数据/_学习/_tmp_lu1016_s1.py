# -*- coding: utf-8 -*-
"""昨日(20261015)打脸结算 + 002815否决对照 + 追不进门 机械结算（零网络）"""
import os, json, csv, pandas as pd, numpy as np
B=r"D:\股票数据\市场数据\_学习"; M=r"D:\股票数据\市场数据"
CD=os.path.join(B,"_bars_cache")
def bars(c):
    f=os.path.join(CD,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    return b
def e1(c,d):
    b=bars(c)
    if b is None: return None
    idx=b.index[b['date']==d]
    if not len(idx): return None
    i=idx[0]
    if i+1>=len(b): return None
    o=b.loc[i+1,'open']; cl=b.loc[i+1,'close']; tc=b.loc[i,'close']
    return dict(T1开=round(float(o),3),T1收=round(float(cl),3),T0收=round(float(tc),3),
                T1高开=round((o/tc-1)*100,2), 执1=round((cl/o-1)*100,2))
# ---- 昨日 全池 36 ----
q=json.load(open(os.path.join(B,"涨停质量荐票_20261015.json"),encoding="utf-8"))
det=q["明细"]
res=[]; miss=[]
for r in det:
    x=e1(r["代码"],"20261015")
    if x is None: miss.append(r["代码"]); continue
    res.append(dict(代码=r["代码"],名称=r["名称"],连板=r["连板"],换手=round(r["换手"],2),封单比=r["封单比"],
                    首封=r["首封"],开板=r["开板次数"],预测执1=r["预测执1均涨"],实执1=x["执1"],T1高开=x["T1高开"]))
e1s=[x["实执1"] for x in res]
print("=== 昨日池 %d 只（缺bar %d）==="%(len(res),len(miss)))
print("池均执1 %.2f%%  胜率 %d/%d=%.1f%%  预测池均 %.2f%%"%(np.mean(e1s),sum(1 for v in e1s if v>0),len(e1s),sum(1 for v in e1s if v>0)/len(e1s)*100,
      np.mean([x["预测执1"] for x in res])))
print("池均T1高开 %.2f%%  为正数 %d"%(np.mean([x["T1高开"] for x in res]),sum(1 for x in res if x["T1高开"]>0)))
# 昨池换手<3% 子集 vs 3-10%
for lo,hi,lab in [(0,3,"<3%"),(3,10,"3-10%"),(10,20,"10-20%"),(20,999,"≥20%")]:
    g=[x for x in res if lo<=x["换手"]<hi]
    if g: print("  昨池换手%s n=%d 执1均 %.2f%% 胜率 %.1f%%"%(lab,len(g),np.mean([x["实执1"] for x in g]),
          sum(1 for x in g if x["实执1"]>0)/len(g)*100))
# ---- 昨日 3 观察位 ----
print("\n=== 昨日观察位 ===")
for c,n in [("605058","澳弘电子"),("600812","华北制药"),("002945","华林证券")]:
    x=e1(c,"20261015"); print(" ",c,n,x)
# ---- 002815 否决对照 ----
x=e1("002815","20261015")
print("\n=== 002815 崇达技术(昨日被本路否决 / logic荐票) ===", x)
# ---- 追不进门: 昨日 9 只 首封<=09:31 ----
print("\n=== 昨日 首封<=09:31 的 9 只 T+1 追不进检验 ===")
nine=["002815","001225","000530","002343","001318","002696","605189","603999","000626"]
lim={c:0.2 for c in ["300001"]}
for c in nine:
    x=e1(c,"20261015")
    if not x: print("  ",c,"缺bar"); continue
    cap=0.30 if c[0]=="8" or c.startswith("92") else (0.20 if c[0] in "3" or c.startswith("688") else 0.10)
    zj = x["T1高开"] >= cap*100-0.2
    print("  %s 高开%+.2f%% 执1%+.2f%% 板幅%.0f%% %s"%(c,x["T1高开"],x["执1"],cap*100,"→追不进" if zj else "可成交"))
json.dump(dict(昨日池=res,池均执1=round(float(np.mean(e1s)),3),被否决票_002815=x),open(os.path.join(B,"_limitup_结算_20261016.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\nwritten _limitup_结算_20261016.json")
