# -*- coding: utf-8 -*-
"""资金结构因子.py [train|score {d}] —— 09号纯资金因子库(2026-07-10用户拍板"按资金角度往下拆")。
★职责边界:09号只研究资金/席位;票的量价/位置/题材是其他agent的事。旧12因子(换手/市值/位置等)退出。
10个纯资金因子(含日度资金温度=当日总额近60日分位,当日视角零后视镜)(全部T日盘后可知,来自买侧席位明细+票级榜单):
  机构席数/机构买占比/北向在场/量化席数/知名游资席数/买1集中度/大单席数(≥5000万)/买侧总额/净买强度。
★目标变量恒为执1/执2(T+1开盘买入→T+1/T+2收盘)。有效性自动评估:区分度(桶间执1胜率极差)<3pp淘汰×单调性。
席位风格识别=米开固定席位表(量化:太华路/西大街/成章路/紫阳东路/知春路/万豪世家;游资:光复路章盟主/溧阳路/上塘路欢乐海岸/永城路等)。
产出: _学习/_资金结构库.json + 快照jsonl;score {d}→逐票资金结构分0-100。"""
import os,sys,json,glob,datetime
import pandas as pd,numpy as np
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
DIR=os.path.join(L,"_席位动向"); CDIR=os.path.join(L,"_bars_cache")
MIN_DISC=3.0
def _temp_map():
    p=os.path.join(L,"_资金温度.json")
    if not os.path.isfile(p): return {}
    try: return {x["日"]:x["温度分位"] for x in json.load(open(p,encoding="utf-8"))}
    except Exception: return {}
TEMP=_temp_map()
QUANT=["太华路","西大街","成章路","紫阳东路","知春路","万豪世家","高新成章"]
HOT=["光复路","溧阳路","上塘路","永城路","宁波桑田路","佛山绿景路","湖里大道","文化东路","金田路","漳州元光"]
def style(seat):
    if "机构专用" in seat: return "机构"
    if "股通" in seat: return "北向"
    if any(k in seat for k in QUANT): return "量化"
    if any(k in seat for k in HOT): return "知名游资"
    return "营业部"
def feats_of_day(d):
    f=os.path.join(DIR,f"{d}.csv")
    if not os.path.isfile(f): return None
    df=pd.read_csv(f,dtype={"代码":str}); df["代码"]=df["代码"].str.zfill(6)
    from 席位动向库 import clean
    df=clean(df)
    df["风格"]=df["席位"].map(style)
    out=[]
    for c,g in df.groupby("代码"):
        buy=g["买入金额"].sum()
        if buy<=0: continue
        jg=g[g["风格"]=="机构"]
        r=dict(日=d,代码=c,名称=g["名称"].iloc[0],
            机构席数=len(jg),机构买占比=round(jg["买入金额"].sum()/buy*100,1),
            北向=int((g["风格"]=="北向").any()),量化席数=int((g["风格"]=="量化").sum()),
            游资席数=int((g["风格"]=="知名游资").sum()),
            买1集中度=round(g["买入金额"].max()/buy*100,1),
            大单席数=int((g["买入金额"]>=5e7).sum()),
            买侧总额亿=round(buy/1e8,2),
            净买强度=round(g["净额"].sum()/buy*100,1),
            资金温度=TEMP.get(d))
        out.append(r)
    return pd.DataFrame(out)
def _bucket(r):
    return dict(
      机构席数=("0" if r["机构席数"]==0 else "1" if r["机构席数"]==1 else "2" if r["机构席数"]==2 else "3+"),
      机构买占比=("无" if r["机构买占比"]<=0 else "<15%" if r["机构买占比"]<15 else "15-30%" if r["机构买占比"]<30 else "≥30%"),
      北向=("在场" if r["北向"] else "无"),
      量化席数=("0" if r["量化席数"]==0 else "1" if r["量化席数"]==1 else "2+"),
      游资席数=("0" if r["游资席数"]==0 else "1" if r["游资席数"]==1 else "2+"),
      买1集中度=("<25%" if r["买1集中度"]<25 else "25-40%" if r["买1集中度"]<40 else "40-60%" if r["买1集中度"]<60 else "≥60%独食"),
      大单席数=("0" if r["大单席数"]==0 else "1" if r["大单席数"]==1 else "2" if r["大单席数"]==2 else "3+"),
      买侧总额亿=("<1亿" if r["买侧总额亿"]<1 else "1-3亿" if r["买侧总额亿"]<3 else "3-6亿" if r["买侧总额亿"]<6 else "≥6亿"),
      净买强度=("≤20%" if r["净买强度"]<=20 else "20-50%" if r["净买强度"]<=50 else "50-80%" if r["净买强度"]<=80 else ">80%"),
      资金温度=(None if r.get("资金温度") is None else "冷<34" if r["资金温度"]<34 else "温34-66" if r["资金温度"]<67 else "热≥67"))
ORDER={"机构席数":["0","1","2","3+"],"机构买占比":["无","<15%","15-30%","≥30%"],"北向":["无","在场"],
 "量化席数":["0","1","2+"],"游资席数":["0","1","2+"],"买1集中度":["<25%","25-40%","40-60%","≥60%独食"],
 "大单席数":["0","1","2","3+"],"买侧总额亿":["<1亿","1-3亿","3-6亿","≥6亿"],"净买强度":["≤20%","20-50%","50-80%",">80%"],
 "资金温度":["冷<34","温34-66","热≥67"]}
def _fwd_map(codes):
    mp={}
    for c in codes:
        f=os.path.join(CDIR,c+".csv")
        if not os.path.isfile(f): mp[c]=None; continue
        b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
        mp[c]=(b,{v:i for i,v in enumerate(b['date'])})
    return mp
def train():
    days=sorted(os.path.basename(x)[:-4] for x in glob.glob(os.path.join(DIR,"20*.csv")))
    tabs=[feats_of_day(d) for d in days]
    ft=pd.concat([t for t in tabs if t is not None and len(t)],ignore_index=True)
    mp=_fwd_map(set(ft["代码"]))
    e1s=[];e2s=[]
    for _,r in ft.iterrows():
        m=mp.get(r["代码"]); e1=e2=None
        if m is not None:
            b,ix=m; i=ix.get(r["日"])
            if i is not None and i+1<len(b):
                o1=b['open'].iat[i+1]; e1=round((b['close'].iat[i+1]/o1-1)*100,2)
                if i+2<len(b): e2=round((b['close'].iat[i+2]/o1-1)*100,2)
        e1s.append(e1);e2s.append(e2)
    ft["执1"]=e1s; ft["执2"]=e2s
    ft=ft[ft["执1"].notna()]           # 零后视镜:无前向不入库
    base_w=round((ft["执1"]>0).mean()*100,1); base_r=round(ft["执1"].mean(),2)
    lib={"窗口":f'{ft["日"].min()}~{ft["日"].max()}',"样本":len(ft),
         "基准":dict(执1胜率=base_w,执1均涨=base_r,执2胜率=round((ft["执2"].dropna()>0).mean()*100,1),执2均涨=round(ft["执2"].dropna().mean(),2)),
         "口径":"纯资金9因子(买侧席位明细聚合);目标恒为执1/执2=T+1开买→T+1/T+2收;区分度<3pp淘汰×单调性加权;每晚重训","因子":{}}
    bs=ft.apply(_bucket,axis=1,result_type="expand")
    weights={}
    for fac in ORDER:
        g=ft[bs[fac].notna()].groupby(bs[fac][bs[fac].notna()])
        bk={}
        for name,gg in g:
            if len(gg)<20: continue
            bk[name]=dict(n=len(gg),执1胜率=round((gg["执1"]>0).mean()*100,1),执1均涨=round(gg["执1"].mean(),2),
                执2胜率=round((gg["执2"].dropna()>0).mean()*100,1),执2均涨=round(gg["执2"].dropna().mean(),2))
        if len(bk)<2: lib["因子"][fac]=dict(桶=bk,状态="样本不足",权重=0); continue
        rates=[bk[o]["执1胜率"] for o in ORDER[fac] if o in bk]
        disc=round(max(rates)-min(rates),1)
        idx=[i for i,o in enumerate(ORDER[fac]) if o in bk]
        rho=abs(np.corrcoef(idx,rates)[0,1]) if len(rates)>2 else 1.0
        ok=disc>=MIN_DISC
        weights[fac]=disc*rho if ok else 0
        lib["因子"][fac]=dict(桶序=[o for o in ORDER[fac] if o in bk],桶=bk,区分度=disc,单调rho=round(float(rho),2),
            状态="有效" if ok else f"淘汰(区分度{disc}<3pp)",权重=0)
    tw=sum(weights.values()) or 1
    for fac,w in weights.items(): lib["因子"][fac]["权重"]=round(w/tw,4)
    lib["活跃因子"]=[f for f,w in weights.items() if w>0]
    json.dump(lib,open(os.path.join(L,"_资金结构库.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    open(os.path.join(L,"_资金结构库快照.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
        日=datetime.date.today().strftime("%Y%m%d"),窗口=lib["窗口"],样本=len(ft),基准=lib["基准"],
        活跃=lib["活跃因子"],权重={f:lib["因子"][f]["权重"] for f in lib["活跃因子"]}),ensure_ascii=False)+"\n")
    print(f'资金结构库: 样本{len(ft)} 基准执1 {base_w}%/{base_r}% 活跃{len(lib["活跃因子"])}/10')
    for f in ORDER:
        v=lib["因子"][f]; print(f'  {f}: {v.get("状态","?")} 区分度{v.get("区分度","—")} 权重{v.get("权重",0)}')
def score(d):
    lib=json.load(open(os.path.join(L,"_资金结构库.json"),encoding="utf-8"))
    ft=feats_of_day(d)
    if ft is None or not len(ft): print("无当日明细"); return
    out={}
    base=lib["基准"]["执1胜率"]
    for _,r in ft.iterrows():
        bs=_bucket(r); pts=0; parts=[]
        for fac in lib["活跃因子"]:
            v=lib["因子"][fac]; b=bs[fac]
            if b is None or b not in v["桶"]: continue
            edge=v["桶"][b]["执1胜率"]-base
            pts+=v["权重"]*edge
            if abs(edge)>=2: parts.append(f'{fac}:{b}({edge:+.0f}pp)')
        sc=int(max(0,min(100,50+pts*6)))
        out[r["代码"]]=dict(资金结构分=sc,风格构成=dict(机构=int(r["机构席数"]),北向=int(r["北向"]),量化=int(r["量化席数"]),游资=int(r["游资席数"])),
            主导=("; ".join(parts[:3]) or "均值附近"),
            特征={k:(int(v) if isinstance(v,(np.integer,)) else float(v) if isinstance(v,(np.floating,)) else v) for k,v in r.drop(["日","代码","名称"]).items()})
    json.dump(dict(日=d,分数=out),open(os.path.join(L,f"资金结构分_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    top=sorted(out.items(),key=lambda x:-x[1]["资金结构分"])[:5]
    print(f'{d} 资金结构打分{len(out)}只 Top:',", ".join(f'{c}({v["资金结构分"]})' for c,v in top))
if __name__=="__main__":
    if sys.argv[1]=="train": train()
    else: score(sys.argv[2] if len(sys.argv)>2 else sys.argv[1])
