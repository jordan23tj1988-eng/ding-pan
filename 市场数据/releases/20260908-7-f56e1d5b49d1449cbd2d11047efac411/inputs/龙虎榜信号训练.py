# -*- coding: utf-8 -*-
"""龙虎榜信号训练.py [start] [end] —— 量化"什么样的龙虎榜资金结构产生高胜率"。
数据: akshare stock_lhb_detail_em(含上榜后1/2/5/10日真实表现,东财口径)。零后视镜:
信号全部为T日盘后可知;口径两套——观察=上榜后1日(T收→T+1收,不可交易仅观察),
跟随=上榜后2日相对1日的增量((1+r2)/(1+r1)-1,近似T+1买入者的可吃区间,同席位库口径)。
产出: _学习/_龙虎榜信号胜率.json + .md
"""
import os,sys,json,datetime
import pandas as pd,numpy as np
try: import akshare as ak
except ImportError: os.system(sys.executable+" -m pip install akshare --break-system-packages -q"); import akshare as ak
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
def stat(d):
    n=len(d)
    if n<20: return None  # 样本太小不出数
    return dict(n=int(n),
        观察胜率=round(float((d["r1"]>0).mean()*100),1),观察均涨=round(float(d["r1"].mean()),2),
        跟随胜率=round(float((d["rf"]>0).mean()*100),1),跟随均涨=round(float(d["rf"].mean()),2))
def main(s,e):
    df=ak.stock_lhb_detail_em(start_date=s,end_date=e)
    df=df[~df["名称"].astype(str).str.contains("退|ST")]
    df=df.drop_duplicates(subset=["代码","上榜日"])
    df=df.dropna(subset=["上榜后1日","上榜后2日"])
    df["r1"]=df["上榜后1日"]; df["rf"]=((1+df["上榜后2日"]/100)/(1+df["上榜后1日"]/100)-1)*100
    df["净占"]=pd.to_numeric(df["净买额占总成交比"],errors="coerce")
    df["dk"]=pd.to_numeric(df["龙虎榜买入额"],errors="coerce")/pd.to_numeric(df["龙虎榜卖出额"],errors="coerce")
    df["hs"]=pd.to_numeric(df["换手率"],errors="coerce"); df["zdf"]=pd.to_numeric(df["涨跌幅"],errors="coerce")
    out={"样本区间":f"{s}-{e}","总样本":int(len(df)),"口径":"观察=T收→T+1收(不可交易);跟随=(1+2日)/(1+1日)-1≈T+1买入者可吃区间","基准":stat(df)}
    def bucket(name,col,edges,labels):
        r={}
        for (lo,hi),lab in zip(edges,labels):
            d=df[(df[col]>lo)&(df[col]<=hi)]
            v=stat(d)
            if v: r[lab]=v
        out[name]=r
    bucket("净买占比",'净占',[(-999,0),(0,5),(5,10),(10,20),(20,999)],["≤0净卖","0-5%","5-10%","10-20%",">20%"])
    bucket("多空比",'dk',[(0,1),(1,2),(2,3),(3,999)],["<1","1-2","2-3","≥3"])
    bucket("换手率",'hs',[(0,3),(3,15),(15,30),(30,999)],["<3%(一字锁仓型)","3-15%","15-30%",">30%(高换手)"])
    bucket("上榜日涨跌",'zdf',[(9.5,999),(0,9.5),(-999,0)],["涨停","涨未停","下跌"])
    # 组合信号
    combos={
     "强档(净占≥10&多空≥2)":df[(df["净占"]>=10)&(df["dk"]>=2)],
     "强档+一字锁仓(换手<3%)":df[(df["净占"]>=10)&(df["dk"]>=2)&(df["hs"]<3)],
     "强档+高换手(>30%)":df[(df["净占"]>=10)&(df["dk"]>=2)&(df["hs"]>30)],
     "出货型涨停(涨停&净占≤0)":df[(df["zdf"]>9.5)&(df["净占"]<=0)],
     "真金涨停(涨停&净占≥10)":df[(df["zdf"]>9.5)&(df["净占"]>=10)],
     "机构买入解读":df[df["解读"].astype(str).str.contains("机构买入")],
     "机构卖出解读":df[df["解读"].astype(str).str.contains("机构卖出|机构砸盘")],
    }
    out["组合信号"]={k:stat(v) for k,v in combos.items() if stat(v)}
    json.dump(out,open(os.path.join(L,"_龙虎榜信号胜率.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    md=["# 龙虎榜信号胜率库(A档·东财上榜后表现口径)\n",f"> 样本{s}-{e}共{len(df)}股次(剔ST/退市/重复)。观察口径不可交易;跟随口径≈T+1买入者可吃。\n"]
    for sec in ["净买占比","多空比","换手率","上榜日涨跌","组合信号"]:
        md.append(f"\n## {sec}\n| 桶 | n | 观察胜率 | 观察均涨 | ★跟随胜率 | ★跟随均涨 |\n|---|---|---|---|---|---|")
        for k,v in out[sec].items():
            md.append(f"| {k} | {v['n']} | {v['观察胜率']}% | {v['观察均涨']}% | **{v['跟随胜率']}%** | **{v['跟随均涨']}%** |")
    b=out["基准"]
    md.append(f"\n基准(全样本): n={b['n']} 观察{b['观察胜率']}%/{b['观察均涨']}% 跟随{b['跟随胜率']}%/{b['跟随均涨']}%")
    open(os.path.join(L,"_龙虎榜信号胜率.md"),"w",encoding="utf-8").write("\n".join(md))

    # 追加每日快照(供盯盘台追踪胜率变化,只加不删)
    try:
        import datetime as _dt
        _snap=dict(快照日=_dt.date.today().strftime("%Y%m%d"))
        _snap["data"]=out
        open(os.path.join(BASE,"_学习","信号胜率快照.jsonl"),"a",encoding="utf-8").write(json.dumps(_snap,ensure_ascii=False,default=str)+"\n")
    except Exception as _e: print("快照失败",_e)
    print("完成,样本",len(df))
if __name__=="__main__":
    a=sys.argv[1:]
    main(a[0] if a else "20260401", a[1] if len(a)>1 else "20260703")
