# -*- coding: utf-8 -*-
"""席位动向库.py —— 席位为主轴的事实表+分档(09龙虎榜agent v3底座,2026-07-10用户拍板)。
用法: fetch {d} | backfill {d1} {d2} | rank
- fetch: {d}/lhb.csv上榜清单→并发拉个股买入侧席位明细(stock_lhb_stock_detail_em)→_学习/_席位动向/{d}.csv
- rank: 扫全部动向×K线缓存→每席位滚动执行口径胜率(执1=T+1开买→T+1收,执2=→T+2收)→S/A/B/C分档
  _学习/_席位分档.json + 快照jsonl。★零后视镜:分档只用已有T+2前向的笔;当日笔无前向不参与。
  ★自我净化:每晚重算,掉档自动降级;一笔=席位净买>0且买额≥1000万(过滤尾单)。"""
import os,sys,json,glob,time,datetime
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
DIR=os.path.join(L,"_席位动向"); CDIR=os.path.join(L,"_bars_cache")
os.makedirs(DIR,exist_ok=True)
MIN_BUY=1e7
FAKE={"自然人","其他自然人","中小投资者","机构","沪股通","深股通","其他","个人投资者","专业机构","专业机构投资者"}
def clean(df):
    """统一清洗(全链唯一口径,2026-07-10数据污染修复):
    ①剔投资者类别汇总行(自然人/机构/中小投资者等,来自沪市异动榜的类别统计,非真实席位)
    ②剔区间累计榜行(类型含'连续'/'累计'=3日/10日区间合计金额,与当日榜重复且跨日)
    ③(代码,席位)去重(同票多上榜原因重复) ④剔可转债/B股"""
    df=df[~df["席位"].astype(str).str.strip().isin(FAKE)]
    df=df[~df["类型"].astype(str).str.contains("连续|累计",na=False)]
    df=df[~df["代码"].str.startswith(("11","12","90","20"))]
    return df.drop_duplicates(subset=[c for c in ["日","代码","席位"] if c in df.columns])

def fetch(d):
    import akshare as ak
    lp=os.path.join(BASE,d,"lhb.csv")
    if os.path.isfile(lp):
        lh=pd.read_csv(lp,dtype={"代码":str})
    else:  # 历史日无本地榜单→接口回拉当日上榜清单
        ds=f"{d[:4]}-{d[4:6]}-{d[6:]}"
        try: lh=ak.stock_lhb_detail_em(start_date=d,end_date=d)
        except Exception:
            print(d,"榜单接口失败,跳过"); return
        if lh is None or not len(lh): print(d,"无榜单数据"); return
        lh["代码"]=lh["代码"].astype(str)
    lh["代码"]=lh["代码"].astype(str).str.zfill(6)
    codes=sorted(set(lh["代码"])); nm=dict(zip(lh["代码"],lh["名称"]))
    rows=[]
    def one(c):
        for att in range(3):
            try:
                det=ak.stock_lhb_stock_detail_em(symbol=c,date=d,flag="买入")
                out=[]
                for _,r in det.iterrows():
                    out.append(dict(日=d,代码=c,名称=nm.get(c),席位=str(r["交易营业部名称"]).strip(),
                        买入金额=float(r["买入金额"]),买占比=float(r.get("买入金额-占总成交比例") or 0),
                        卖出金额=float(r["卖出金额"]),净额=float(r["净额"]),类型=str(r.get("类型",""))[:40]))
                return out
            except Exception:
                time.sleep(1.2)
        return []
    with ThreadPoolExecutor(16) as ex:
        for out in ex.map(one,codes): rows+=out
    df=pd.DataFrame(rows)
    if len(df): df=df.drop_duplicates(subset=["代码","席位","类型"])
    df.to_csv(os.path.join(DIR,f"{d}.csv"),index=False)
    print(f"{d} 席位动向: 上榜{len(codes)}只 → 席位行{len(df)} (买侧,含重复上榜原因去重)")
def bars(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b
def fwd(c,d):
    b=bars(c)
    if b is None: return None,None
    idx=b.index[b['date']==d]
    if not len(idx) or idx[0]+1>=len(b): return None,None
    i=idx[0]; o1=b.loc[i+1,'open']; c1=b.loc[i+1,'close']
    e1=(c1/o1-1)*100
    e2=(b.loc[i+2,'close']/o1-1)*100 if i+2<len(b) else None
    return round(e1,2),(round(e2,2) if e2 is not None else None)
def _style(seat):
    from 资金结构因子 import style
    return style(seat)
def grade(n,w1,r1):
    if n>=5:
        if w1>=60 and r1>1: return "S"
        if w1>=55 or (w1>=50 and r1>1.5): return "A"
        if w1>=45: return "B"
        return "C"
    return "P"  # 预备:样本3-4
def rank():
    fs=sorted(glob.glob(os.path.join(DIR,"20*.csv")))
    if not fs: print("无动向数据"); return
    df=pd.concat([pd.read_csv(f,dtype={"代码":str}) for f in fs],ignore_index=True)
    df["代码"]=df["代码"].str.zfill(6); df["日"]=df["日"].astype(str)
    df=clean(df)
    df=df[(df["净额"]>0)&(df["买入金额"]>=MIN_BUY)]
    recs=[]
    _bc={}
    def fwd_c(c,d):
        if c not in _bc:
            f=os.path.join(CDIR,c+".csv")
            if os.path.isfile(f):
                b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
                _bc[c]=(b,{v:i for i,v in enumerate(b['date'])})
            else: _bc[c]=None
        if _bc[c] is None: return None,None
        b,ix=_bc[c]; i=ix.get(d)
        if i is None or i+1>=len(b): return None,None
        o1=b['open'].iat[i+1]; e1=(b['close'].iat[i+1]/o1-1)*100
        e2=(b['close'].iat[i+2]/o1-1)*100 if i+2<len(b) else None
        return round(e1,2),(round(e2,2) if e2 is not None else None)
    for _,r in df.iterrows():
        e1,e2=fwd_c(r["代码"],r["日"])
        if e1 is None: continue   # 无前向=不入样本(零后视镜:当日笔明天才结算)
        recs.append(dict(席位=r["席位"],日=r["日"],代码=r["代码"],名称=r["名称"],买入金额=r["买入金额"],净额=r["净额"],执1=e1,执2=e2))
    rd=pd.DataFrame(recs)
    # ★收缩估计(2026-07-11 P0-4):向全体席位基准率收缩,K=10;n=9的66.7%不再按面值定档
    p0=round((rd["执1"]>0).mean()*100,1); r0=round(rd["执1"].mean(),2); K=10
    lib={}
    for s,g in rd.groupby("席位"):
        n=len(g); w1=round((g["执1"]>0).mean()*100,1); r1=round(g["执1"].mean(),2)
        g2v=g["执2"].dropna(); w2=round((g2v>0).mean()*100,1) if len(g2v) else None; r2=round(g2v.mean(),2) if len(g2v) else None
        if n<3: continue
        w1s=round((w1*n+p0*K)/(n+K),1); r1s=round((r1*n+r0*K)/(n+K),2)
        last=g.sort_values("日").tail(5)
        lib[s]=dict(档=grade(n,w1s,r1s),样本=n,执1胜率=w1,执1均涨=r1,
            收缩执1胜率=w1s,收缩执1均涨=r1s,小样本=bool(n<25),
            执2胜率=w2,执2均涨=r2,
            通道=_style(s),
            近5笔=[dict(日=x["日"],名=x["名称"],执1=x["执1"]) for _,x in last.iterrows()])
    cnt=pd.Series([v["档"] for v in lib.values()]).value_counts().to_dict()
    win=f'{rd["日"].min()}~{rd["日"].max()}'
    out=dict(更新=datetime.date.today().strftime("%Y%m%d"),窗口=win,笔数=len(rd),席位数=len(lib),档分布=cnt,
        基准=dict(全体执1胜率=p0,全体执1均涨=r0,收缩K=K),
        口径=f"一笔=席位净买>0且买额≥{int(MIN_BUY/1e4)}万;执1=T+1开买→T+1收,执2=→T+2收(跟随执行口径);零后视镜=只用已有前向的笔;每晚重算=掉档自动净化;★分档用收缩胜率(向全体基准收缩K={K}),n<25标小样本",
        席位=lib)
    json.dump(out,open(os.path.join(L,"_席位分档.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    sa=[(s,v) for s,v in lib.items() if v["档"] in "SA"]
    sa.sort(key=lambda x:(-x[1]["收缩执1胜率"],-x[1]["样本"]))
    open(os.path.join(L,"_席位分档快照.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
        日=out["更新"],窗口=win,笔数=len(rd),档分布=cnt,S榜首=[f'{s[:20]}({v["执1胜率"]}%/{v["样本"]}笔)' for s,v in sa[:3]]),ensure_ascii=False)+"\n")
    print(f"分档完成: 窗口{win} 笔数{len(rd)} 席位{len(lib)} 档分布{cnt}")
    for s,v in sa[:8]: print(f'  [{v["档"]}] {s[:26]} 收缩执1 {v["收缩执1胜率"]}%(原{v["执1胜率"]}%)/{v["收缩执1均涨"]}% n={v["样本"]}{"⚠" if v["小样本"] else ""} {v["通道"]}')

def fetch_bars(codes):
    """补拉缺失K线进 _bars_cache(sina,与涨停质量训练同缓存)"""
    import akshare as ak, time
    from concurrent.futures import ThreadPoolExecutor
    def one(c):
        f=os.path.join(CDIR,c+".csv")
        if os.path.isfile(f): return 0
        pfx="sh" if c.startswith(("6","9")) else ("bj" if c.startswith(("4","8","92")) else "sz")
        for att in range(2):
            try:
                b=ak.stock_zh_a_daily(symbol=pfx+c,start_date="20260320",end_date="20991231")
                b=b[["date","open","high","low","close","volume"]]
                b.to_csv(f,index=False); return 1
            except Exception: time.sleep(1)
        return 0
    with ThreadPoolExecutor(4) as ex: n=sum(ex.map(one,codes))
    print(f"补K线 {n}/{len(codes)}")
if __name__=="__main__":
    a=sys.argv[1:]
    if a[0]=="fetch": fetch(a[1])
    elif a[0]=="backfill":
        # 时间预算模式:交易日历=榜单接口按周扫;跑满预算秒数即停,反复调用直至补齐
        import akshare as ak
        budget=float(a[3]) if len(a)>3 else 38
        t0=time.time()
        try:
            cal=ak.tool_trade_date_hist_sina(); ds=[x.strftime("%Y%m%d") for x in pd.to_datetime(cal["trade_date"]).dt.date]
        except Exception:
            ds=[x.strftime("%Y%m%d") for x in pd.date_range(a[1],a[2])]
        for d in [x for x in ds if a[1]<=x<=a[2]]:
            if os.path.isfile(os.path.join(DIR,f"{d}.csv")): continue
            if time.time()-t0>budget: print("预算用尽,下次继续"); break
            fetch(d)
    elif a[0]=="rank": rank()
    elif a[0]=="bars": fetch_bars([x.strip() for x in open(a[1]).read().split()])
