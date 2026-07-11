# -*- coding: utf-8 -*-
"""链条位置.py {板块名} [d] —— 读产业链模板.json,对该板块每环节代表股拉sina日线,
算60日/20日/YTD涨幅+距250日高,输出环节位置地图。A档,位置标尺口径。
产出: _学习/链条位置_{板块}_{d}.json"""
import os,sys,json,datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import akshare as ak
BASE=os.path.dirname(os.path.abspath(__file__))
def one(cn):
    c,n=cn
    pre="sh" if c[0] in "69" else ("bj" if c[0] in "48" else "sz")
    try:
        b=ak.stock_zh_a_daily(symbol=pre+c,start_date="20250701",end_date=datetime.date.today().strftime("%Y%m%d"))
        cl=b["close"].astype(float).values
        if len(cl)<80: return c,None
        last=cl[-1]
        d=pd.to_datetime(b["date"]); idx=(d>=pd.Timestamp("2026-01-01")).idxmax()
        return c,dict(名=n,r20=round((last/cl[-21]-1)*100,1),
            r60=round((last/cl[-61]-1)*100,1) if len(cl)>61 else None,
            ytd=round((last/float(b["close"].iloc[idx])-1)*100,1),
            距250日高=round((last/max(cl[-250:] if len(cl)>=250 else cl)-1)*100,1))
    except Exception: return c,None
def judge(r60,dist):
    if r60 is None: return "数据不足"
    if dist>-10 and r60>50: return "基本涨到位"
    if r60>=90: return "严重透支"
    if r60>=40: return "高位/分化"
    if r60>=10: return "中位"
    if r60<0 and dist<-30: return "洼地"
    return "中低位"
def main(sector,d):
    tpl=json.load(open(os.path.join(BASE,"产业链模板.json"),encoding="utf-8"))
    if sector not in tpl: print("模板无此板块,现有:",[k for k in tpl if k!="说明"]); return 1
    cfg=tpl[sector]
    codes=[(c,n) for seg in cfg["环节"].values() for c,n in seg]
    res={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for c,v in ex.map(one,codes):
            if v: res[c]=v
    out={"板块":sector,"日期":d,"环节":{}}
    for seg,ss in cfg["环节"].items():
        rows=[res[c] for c,_ in ss if c in res]
        if not rows:
            out["环节"][seg]={"注":cfg.get("环节注",{}).get(seg,"无数据/无标的")}
            continue
        r60s=[r["r60"] for r in rows if r["r60"] is not None]
        dists=[r["距250日高"] for r in rows]
        m60=round(sum(r60s)/len(r60s),1) if r60s else None
        md=round(sum(dists)/len(dists),1)
        out["环节"][seg]={"个股":rows,"均60日":m60,"均距高":md,"位置":judge(m60,md)}
    json.dump(out,open(os.path.join(BASE,"_学习",f"链条位置_{sector}_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    for seg,v in out["环节"].items():
        if "个股" not in v: print(f"{seg}: {v['注']}"); continue
        print(f'{seg:14s} 均60日{v["均60日"]:+7.1f}% 均距高{v["均距高"]:+6.1f}% [{v["位置"]}] | '+", ".join(f'{r["名"]}{r["r60"]:+.0f}/{r["距250日高"]:+.0f}' for r in v["个股"]))
    return 0
if __name__=="__main__":
    a=sys.argv[1:]
    sys.exit(main(a[0] if a else "AI算力", a[1] if len(a)>1 else datetime.date.today().strftime("%Y%m%d")))
