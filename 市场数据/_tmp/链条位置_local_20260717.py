# -*- coding: utf-8 -*-
"""一次性: 链条位置本地版(bars_cache口径,沙箱无网,#007 premium_bars同思路)
与 链条位置.py 输出schema完全一致;bars不含当日或历史<80根的代码照实跳过(零编造)。"""
import os,sys,json,datetime
import pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BC=os.path.join(BASE,'_学习','_bars_cache')
def one(cn,d):
    c,n=cn
    p=os.path.join(BC,f'{c}.csv')
    if not os.path.exists(p): return c,None
    try:
        b=pd.read_csv(p)
        dc=[x for x in b.columns if 'date' in x.lower() or '日' in x][0]
        cc=[x for x in b.columns if x.lower() in ('close','收盘','收盘价')][0]
        b[dc]=pd.to_datetime(b[dc]); b=b.sort_values(dc)
        ds=d[:4]+'-'+d[4:6]+'-'+d[6:]
        b=b[b[dc]<=ds]
        if len(b)<80: return c,None
        if b[dc].iloc[-1].strftime('%Y-%m-%d')!=ds: return c,None  # 无当日bar=不新鲜,跳过
        cl=b[cc].astype(float).values; last=cl[-1]
        idx=(b[dc]>=pd.Timestamp('2026-01-01')).idxmax()
        return c,dict(名=n,r20=round((last/cl[-21]-1)*100,1),
            r60=round((last/cl[-61]-1)*100,1) if len(cl)>61 else None,
            ytd=round((last/float(b.loc[idx,cc])-1)*100,1),
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
    if sector not in tpl: print("no board"); return 1
    cfg=tpl[sector]
    res={}
    for seg,ss in cfg["环节"].items():
        for c,n in ss:
            r=one((c,n),d)
            if r[1]: res[c]=r[1]
    out={"板块":sector,"日期":d,"来源":"bars_cache本地(沙箱无网)","环节":{}}
    for seg,ss in cfg["环节"].items():
        rows=[res[c] for c,_ in ss if c in res]
        if not rows:
            out["环节"][seg]={"注":"bars_cache无当日覆盖(照实跳过)"}
            continue
        r60s=[r["r60"] for r in rows if r["r60"] is not None]
        dists=[r["距250日高"] for r in rows]
        m60=round(sum(r60s)/len(r60s),1) if r60s else None
        md=round(sum(dists)/len(dists),1)
        out["环节"][seg]={"个股":rows,"均60日":m60,"均距高":md,"位置":judge(m60,md)}
    json.dump(out,open(os.path.join(BASE,"_学习",f"链条位置_{sector.replace(chr(47),chr(95))}_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    for seg,v in out["环节"].items():
        if "个股" not in v: print(seg,v["注"]); continue
        print(f'{seg:12s} 均60日{v["均60日"]:+6.1f}% 均距高{v["均距高"]:+6.1f}% [{v["位置"]}] '+", ".join(f'{r["名"]}{r["r60"]:+.0f}' for r in v["个股"]))
    return 0
if __name__=='__main__':
    for sec in sys.argv[1:]:
        print('==='+sec); main(sec,'20260717')
