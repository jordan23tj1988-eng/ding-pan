# -*- coding: utf-8 -*-
"""龙虎榜质量训练.py [--fetch] —— 龙虎榜多因子质量库(照搬涨停质量库v3成功模式,2026-07-10)。
- 原料: akshare stock_lhb_detail_em(20260401→今,一次区间拉全);剔ST/退/转债;去重(代码+上榜日)。
- 12因子全部T日盘后可知(零后视镜):净买占比/多空比/换手率/榜占比/上榜日涨跌/解读性质/上榜原因/
  流通市值/股价/位置60日(K线)/近5日上榜次数(榜单自身滚动)/游资滚动胜率(解读抽名,只用T-1前已完整E1历史)。
- ★执行口径为主: 执1=T+1开买→T+1收, 执2=T+1开买→T+2收(信号T1=T收→T+1收仅参考)。K线=_学习/_bars_cache(与涨停库共用)。
- 有效性自动评估: 区分度(桶间执1胜率极差)<3pp淘汰 × 单调性rank相关;近10个交易日方向翻转降权50%。每晚快照→_龙虎榜质量库快照.jsonl。
- 当日榜单无前向不入库=零后视镜;打标当日(d)供荐票脚本,训练/荐票同一代码路径。
"""
import os,sys,json,glob,datetime
import pandas as pd,numpy as np
BASE=os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(BASE,'_学习')):
    g=glob.glob('/sessions/*/mnt/股票数据/市场数据')
    if g: BASE=g[0]
L=os.path.join(BASE,"_学习"); CDIR=os.path.join(L,"_bars_cache")
START="20260401"; MINB=25; MIN_DISC=3.0; RECENT=10
def _c(v): return pd.to_numeric(v,errors="coerce")
# ── 12因子分桶(row=特征表一行) ──
def b_净占(r):
    v=r['净占']
    if v!=v: return None
    return "≤0净卖" if v<=0 else "0-5%" if v<=5 else "5-10%" if v<=10 else "10-20%" if v<=20 else ">20%"
def b_多空(r):
    v=r['多空比']
    if v!=v: return None
    return "<1空头" if v<1 else "1-2" if v<2 else "2-3" if v<3 else "≥3"
def b_换手(r):
    v=r['换手']
    if v!=v: return None
    return "<3%锁仓" if v<3 else "3-15%" if v<15 else "15-30%" if v<30 else ">30%高换手"
def b_榜占(r):
    v=r['榜占比']
    if v!=v: return None
    return "<10%" if v<10 else "10-20%" if v<20 else ">20%主导"
def b_涨跌(r):
    v=r['涨跌幅']
    if v!=v: return None
    return "涨停" if v>9.5 else "涨5-9.5" if v>=5 else "涨0-5" if v>=0 else "下跌"
def b_性质(r): return r['性质']
def b_原因(r): return r['原因类']
def b_市值(r):
    v=r['市值亿']
    if v!=v: return None
    return "<30亿" if v<30 else "30-100亿" if v<100 else "100-300亿" if v<300 else ">300亿"
def b_股价(r):
    v=r['股价']
    if v!=v: return None
    return "<5元" if v<5 else "5-20元" if v<20 else ">20元"
def b_位置(r):
    v=r['位置']
    if v!=v: return None
    return "低位<30%" if v<30 else "中位30-70%" if v<70 else "高位>70%"
def b_榜龄(r):
    v=r['近5日榜次']
    return "首次" if v<=1 else "2次" if v==2 else "3次+常客"
def b_游资档(r):
    v=r['游资胜率']
    if v!=v: return "无档(散/普通/样本不足)"
    return "强≥55%" if v>=55 else "中45-55%" if v>=45 else "弱<45%"
FACTORS={
 "净买占比":(b_净占,["≤0净卖","0-5%","5-10%","10-20%",">20%"]),
 "多空比":(b_多空,["<1空头","1-2","2-3","≥3"]),
 "换手率":(b_换手,["<3%锁仓","3-15%","15-30%",">30%高换手"]),
 "榜占比":(b_榜占,["<10%","10-20%",">20%主导"]),
 "上榜日涨跌":(b_涨跌,["下跌","涨0-5","涨5-9.5","涨停"]),
 "解读性质":(b_性质,["机构买","游资买","普通买","普通卖","游资卖","机构卖"]),
 "上榜原因":(b_原因,["涨幅偏离","连涨3日","振幅","换手率","量价","其他"]),
 "流通市值":(b_市值,["<30亿","30-100亿","100-300亿",">300亿"]),
 "股价":(b_股价,["<5元","5-20元",">20元"]),
 "位置60日":(b_位置,["低位<30%","中位30-70%","高位>70%"]),
 "近5日榜次":(b_榜龄,["首次","2次","3次+常客"]),
 "游资滚动胜率":(b_游资档,["弱<45%","无档(散/普通/样本不足)","中45-55%","强≥55%"]),
}
def _parse_actor(s):
    """解读→(性质桶, 游资名或None)"""
    s=str(s)
    import re
    if "机构买入" in s: return "机构买","机构"
    if "机构卖出" in s or "机构砸盘" in s: return "机构卖","机构"
    m=re.match(r'^(.{2,12}?)资金(买入|卖出)',s)
    if m:
        nm=m.group(1)
        return ("游资买" if m.group(2)=="买入" else "游资卖"),nm
    if "买入" in s: return "普通买",None
    if "卖出" in s: return "普通卖",None
    return "普通买",None
def _parse_reason(s):
    s=str(s)
    if "涨幅偏离" in s or "涨幅达" in s: return "涨幅偏离"
    if "连续三个交易日" in s: return "连涨3日"
    if "振幅" in s: return "振幅"
    if "换手率" in s: return "换手率"
    if "量" in s: return "量价"
    return "其他"
def _raw():
    import akshare as ak
    e=datetime.date.today().strftime("%Y%m%d")
    df=ak.stock_lhb_detail_em(start_date=START,end_date=e)
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    df=df[df["代码"].str.match(r'^(00|30|60|68|43|83|87|92)')]
    df=df[~df["名称"].astype(str).str.contains("退|ST")]
    df=df.drop_duplicates(subset=["代码","上榜日"]).copy()
    df["日"]=df["上榜日"].astype(str).str.replace("-","")
    return df
def _feat(df):
    P=pd.DataFrame()
    P["代码"]=df["代码"]; P["名称"]=df["名称"]; P["日"]=df["日"]
    P["净占"]=_c(df["净买额占总成交比"])
    buy=_c(df["龙虎榜买入额"]); sell=_c(df["龙虎榜卖出额"])
    P["多空比"]=(buy/sell).replace([np.inf,-np.inf],99)
    P["换手"]=_c(df["换手率"]); P["榜占比"]=_c(df["成交额占总成交比"])
    P["涨跌幅"]=_c(df["涨跌幅"]); P["市值亿"]=_c(df["流通市值"])/1e8; P["股价"]=_c(df["收盘价"])
    pa=df["解读"].apply(_parse_actor)
    P["性质"]=[x[0] for x in pa]; P["游资名"]=[x[1] for x in pa]
    P["原因类"]=df["上榜原因"].apply(_parse_reason)
    P=P.sort_values(["代码","日"]).reset_index(drop=True)
    cnt=[]
    hist={}
    for _,r in P.iterrows():
        k=r["代码"]; lst=hist.setdefault(k,[])
        d=r["日"]
        lst=[x for x in lst if x>= (pd.Timestamp(d)-pd.Timedelta(days=7)).strftime("%Y%m%d")]
        cnt.append(len([x for x in lst if x<d])+1)
        lst.append(d); hist[k]=lst
    P["近5日榜次"]=cnt
    return P
def _bars(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b["date"]=b["date"].astype(str).str.replace("-","")
    return b
def _enrich(P,forward=True):
    pos=[];e1=[];e2=[];t1=[]
    for _,r in P.iterrows():
        c=r["代码"];d=r["日"];b=_bars(c)
        p=e1v=e2v=t1v=np.nan
        if b is not None:
            idx=b.index[b["date"]==d]
            if len(idx):
                i=idx[0]
                w=b.iloc[max(0,i-59):i+1]
                hi,lo=w["high"].max(),w["low"].min()
                if hi>lo: p=(b.loc[i,"close"]-lo)/(hi-lo)*100
                if forward and i+1<len(b):
                    o1=b.loc[i+1,"open"];c1=b.loc[i+1,"close"];Tc=b.loc[i,"close"]
                    if o1>0:
                        e1v=(c1/o1-1); t1v=(c1/Tc-1)
                        if i+2<len(b): e2v=(b.loc[i+2,"close"]/o1-1)
        pos.append(p);e1.append(e1v);e2.append(e2v);t1.append(t1v)
    P=P.copy(); P["位置"]=pos
    if forward: P["E1"]=e1;P["E2"]=e2;P["T1"]=t1
    # 游资滚动胜率(零后视镜:只用 上榜日<=T-2 的已完整E1;买入方向)
    ref=P[(P["性质"].isin(["游资买","机构买"]))&(P.get("E1",pd.Series(dtype=float)).notna())][["游资名","日","E1"]] if forward else None
    return P,ref
def _actor_wr(ref,name,d):
    if ref is None or name is None or name!=name: return np.nan
    h=ref[(ref["游资名"]==name)&(ref["日"]<d)]
    # E1在T+1收才知:严格用 日< d-1个交易日;近似用日<d再去掉最近1条同名当日风险(区间日字符串比较,保守再剔d前1自然日)
    h=h[h["日"]<(pd.Timestamp(d)-pd.Timedelta(days=1)).strftime("%Y%m%d")]
    if len(h)<5: return np.nan
    return (h["E1"]>0).mean()*100
def _agg(g):
    def wr(col):
        v=g[col].dropna()
        return (round((v>0).mean()*100,1),round(v.mean()*100,2)) if len(v) else (None,None)
    e1w,e1r=wr('E1');e2w,e2r=wr('E2');t1w,t1r=wr('T1')
    return dict(n=int(len(g)),执1胜率=e1w,执1均涨=e1r,执2胜率=e2w,执2均涨=e2r,T1胜率=t1w,T1均涨=t1r)
def _bscore(st):
    if st.get('执1胜率') is None: return None
    cl=lambda x:max(0.,min(1.,x))
    return round(100*(0.5*cl((st['执1胜率']-40)/35)+0.3*cl((st['执1均涨'] or 0)/2)+0.2*cl((st.get('执2均涨') or 0)/3)),1)
def _spear(a,b):
    try:
        ra=pd.Series(a,dtype=float).rank();rb=pd.Series(b,dtype=float).rank()
        v=float(np.corrcoef(ra,rb)[0,1])
        return None if v!=v else round(v,3)
    except Exception: return None
def build():
    df=_raw(); P=_feat(df)
    P,ref=_enrich(P,forward=True)
    P["游资胜率"]=[_actor_wr(ref,r["游资名"],r["日"]) for _,r in P.iterrows()]
    S=P[P["E1"].notna()].copy()
    days=sorted(S["日"].unique()); recent=set(days[-RECENT:])
    base=_agg(S); base['score']=_bscore(base)
    facs={}
    for name,(fn,order) in FACTORS.items():
        S['_b']=S.apply(fn,axis=1)
        st={}
        for k,g in S.groupby('_b'):
            a=_agg(g);a['score']=_bscore(a);st[k]=a
        qual=[k for k in order if k in st and st[k]['n']>=MINB]
        ent=dict(桶序=order,桶=st)
        rho=disc=rho_r=None;w=0.;status='淘汰·样本不足'
        if len(qual)>=2:
            wrs=[st[k]['执1胜率'] for k in qual]
            rho=_spear(range(len(qual)),wrs);disc=round(max(wrs)-min(wrs),1)
            Sr=S[S['日'].isin(recent)]
            str_={k:_agg(g) for k,g in Sr.groupby('_b') if len(g)>=8}
            qr=[k for k in qual if k in str_]
            if len(qr)>=2: rho_r=_spear([qual.index(k) for k in qr],[str_[k]['执1胜率'] for k in qr])
            if disc<MIN_DISC: status='淘汰·区分度不足'
            else:
                w=disc*(0.5+0.5*abs(rho or 0));status='有效'
                if rho_r is not None and rho is not None and rho*rho_r<0 and abs(rho_r)>=0.3:
                    status='翻转降权';w*=0.5
        ent.update(区分度=disc,单调rho=rho,近窗rho=rho_r,状态=status,原始权重=round(w,2))
        facs[name]=ent
    tw=sum(e['原始权重'] for e in facs.values())
    for e in facs.values(): e['权重']=round(e['原始权重']/tw,4) if tw>0 else 0
    active=[k for k,e in facs.items() if e['权重']>0]
    lib=dict(更新=datetime.date.today().strftime("%Y%m%d"),窗口=f"{S['日'].min()}~{S['日'].max()}",样本=int(len(S)),
        口径=("龙虎榜质量库v1(照搬涨停v3模式)。12因子T日盘后可知;★执行口径执1/执2=T+1开盘买入→T+1/T+2收(荐票主口径);"
             "T1=T收→T+1收仅参考。不复权,零后视镜(当日榜单无前向不入库;游资滚动胜率只用T-1前已完整历史)。"
             f"质量分=Σ权重×桶分;有效性=区分度×单调性,<{MIN_DISC}pp淘汰,近{RECENT}日翻转降权50%。"),
        基准=base,活跃因子=active,因子=facs)
    json.dump(lib,open(os.path.join(L,"_龙虎榜质量库.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    snap=dict(日=lib['更新'],样本=lib['样本'],基准执1=[base['执1胜率'],base['执1均涨']],
        因子={k:dict(权重=e['权重'],区分度=e['区分度'],rho=e['单调rho'],状态=e['状态']) for k,e in facs.items()})
    open(os.path.join(L,"_龙虎榜质量库快照.jsonl"),"a",encoding="utf-8").write(json.dumps(snap,ensure_ascii=False)+"\n")
    md=[f"# 龙虎榜质量库v1(12因子·执行口径) {lib['窗口']} 样本{lib['样本']} 零后视镜",
        f"基准: 执1 {base['执1胜率']}%/{base['执1均涨']}% | 执2 {base['执2胜率']}%/{base['执2均涨']}% | T1 {base['T1胜率']}%/{base['T1均涨']}%",
        f"活跃因子{len(active)}/{len(FACTORS)}: "+", ".join(f"{k}(w{facs[k]['权重']})" for k in sorted(active,key=lambda x:-facs[x]['权重']))]
    for name in sorted(facs,key=lambda x:-facs[x]['权重']):
        e=facs[name]
        md.append(f"\n## {name} | {e['状态']} 权重{e['权重']} 区分度{e['区分度']}pp rho{e['单调rho']} 近窗rho{e['近窗rho']}")
        for k in e['桶序']:
            if k in e['桶']:
                v=e['桶'][k]
                md.append(f"- {k}: n{v['n']} 执1 {v['执1胜率']}%/{v['执1均涨']}% 执2 {v['执2胜率']}%/{v['执2均涨']}% 分{v['score']}")
    open(os.path.join(L,"_龙虎榜质量库.md"),"w",encoding="utf-8").write("\n".join(md))
    print(f"龙虎榜质量库v1建成: 样本{lib['样本']} 窗口{lib['窗口']} 活跃{len(active)}/{len(FACTORS)}")
    for k in sorted(active,key=lambda x:-facs[x]['权重'])[:6]:
        print(f"  {k}: w{facs[k]['权重']} 区分度{facs[k]['区分度']}pp rho{facs[k]['单调rho']} {facs[k]['状态']}")
    return lib
def _lib():
    p=os.path.join(L,"_龙虎榜质量库.json")
    return json.load(open(p,encoding="utf-8")) if os.path.isfile(p) else None
def 质量打分(row,lib=None):
    lib=lib or _lib()
    if not lib: return None
    base=lib['基准'];tot=0.
    pw={'执1胜率':0.,'执1均涨':0.,'执2胜率':0.,'执2均涨':0.}
    contrib=[]
    for name,(fn,order) in FACTORS.items():
        e=lib['因子'].get(name)
        if not e or e['权重']<=0: continue
        b=fn(row);st=e['桶'].get(b) if b else None
        use=st if (st and st['n']>=MINB and st.get('score') is not None) else base
        tot+=e['权重']*use['score']
        for k in pw: pw[k]+=e['权重']*(use.get(k) or 0)
        contrib.append((name,b,round(e['权重']*(use['score']-base['score']),1)))
    pos=sorted([x for x in contrib if x[2]>0],key=lambda x:-x[2])[:3]
    neg=sorted([x for x in contrib if x[2]<0],key=lambda x:x[2])[:2]
    lead="; ".join(f"{n}:{bk}(+{dv})" for n,bk,dv in pos)+((" | 拖累 "+"; ".join(f"{n}:{bk}({dv})" for n,bk,dv in neg)) if neg else "")
    return dict(质量分=round(tot),
        预测执1胜率=round(pw['执1胜率'],1),预测执1均涨=round(pw['执1均涨'],2),
        预测执2胜率=round(pw['执2胜率'],1),预测执2均涨=round(pw['执2均涨'],2),
        主导因子=lead or "全中性")
def 打标当日(d):
    """d日全部上榜股打分(零后视镜:因子含游资滚动胜率只用历史;当日无前向)。原料=历史区间拉取(含d)。"""
    df=_raw(); P=_feat(df)
    Pf,ref=_enrich(P[P["日"]<d],forward=True)   # 历史部分给游资胜率供参考
    Pd,_=_enrich(P[P["日"]==d],forward=False)
    if not len(Pd): return []
    Pd["游资胜率"]=[_actor_wr(ref,r["游资名"],d) for _,r in Pd.iterrows()]
    lib=_lib();out=[]
    for _,r in Pd.iterrows():
        row=r.to_dict();q=质量打分(row,lib)
        if not q: continue
        out.append(dict(代码=row['代码'],名称=row['名称'],净占=round(row['净占'],2) if row['净占']==row['净占'] else None,
            多空比=round(row['多空比'],2) if row['多空比']==row['多空比'] else None,
            换手=row['换手'],涨跌幅=row['涨跌幅'],市值亿=round(row['市值亿'],1) if row['市值亿']==row['市值亿'] else None,
            性质=row['性质'],游资名=row['游资名'],原因类=row['原因类'],近5日榜次=int(row['近5日榜次']),
            位置60日=round(row['位置'],1) if row['位置']==row['位置'] else None,
            游资胜率=round(row['游资胜率'],1) if row['游资胜率']==row['游资胜率'] else None,**q))
    return out
if __name__=="__main__":
    build()
