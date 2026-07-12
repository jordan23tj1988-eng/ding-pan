# -*- coding: utf-8 -*-
"""竞价全市场快照.py —— 早盘9:26全A竞价快照留档(2026-07-12建,08号优化④:C档转A档铺路)。
★动机:925成交额排名/竞价换手是米开第一式核心,但历史不可复现=C档只能实盘。从今天起每天9:26把
  全市场竞价快照落盘存档,一年后这些C档信号就有了可回测的A档历史(竞价额排名/竞价换手/高开分布)。
★存档: _学习/竞价快照存档/{d}.csv.gz(全A:代码/名称/今开/昨收/高开幅度/竞价成交额/竞价额排名/竞价换手代理)
       + {d}_meta.json(采集时间/来源/条数/可信度)。幂等:当日已存则跳过(--force覆盖)。
★可信度:采集时间≤09:30时成交额≈集合竞价额(A档);>09:30则为盘中累计,meta标"污染"仅留档不训练。
★零编造:接口全失败→meta标"失败",不造数。
用法: python3 竞价全市场快照.py [--wait] [--force]   (--wait=等到09:26再抓,给9:20启动的定时任务用)"""
import os,sys,json,time,datetime,glob
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
ARC=os.path.join(L,"竞价快照存档"); os.makedirs(ARC,exist_ok=True)

def wait_926():
    while True:
        now=datetime.datetime.now()
        if now.hour>9 or (now.hour==9 and now.minute>=26): return
        time.sleep(10)

def fetch():
    """全A实时spot:东财em优先,sina兜底。返回(df,来源) df列=代码,名称,今开,昨收,最新价,成交额"""
    import pandas as pd
    try:
        import akshare as ak
    except ImportError:
        os.system(sys.executable+" -m pip install akshare --break-system-packages -q"); import akshare as ak
    try:
        df=ak.stock_zh_a_spot_em()
        df=df.rename(columns={"最新价":"最新价","今开":"今开","昨收":"昨收","成交额":"成交额"})
        df=df[["代码","名称","今开","昨收","最新价","成交额","流通市值"]].copy()
        return df,"eastmoney_em"
    except Exception as e:
        print("em失败:",e)
    try:
        import akshare as ak
        df=ak.stock_zh_a_spot()  # sina,较慢
        df=df.rename(columns={"symbol":"代码","name":"名称","open":"今开","settlement":"昨收","trade":"最新价","amount":"成交额"})
        df["代码"]=df["代码"].astype(str).str[-6:]
        df["流通市值"]=None
        return df[["代码","名称","今开","昨收","最新价","成交额","流通市值"]],"sina_spot"
    except Exception as e:
        print("sina也失败:",e)
    return None,None

def main(wait=False,force=False):
    import pandas as pd
    if wait: wait_926()
    d=datetime.date.today().strftime("%Y%m%d")
    fp=os.path.join(ARC,d+".csv.gz"); mp=os.path.join(ARC,d+"_meta.json")
    if os.path.isfile(fp) and not force:
        print("今日已存档,跳过(--force覆盖)"); return
    t0=datetime.datetime.now().strftime("%H:%M:%S")
    df,src=fetch()
    if df is None:
        json.dump(dict(日=d,状态="失败",采集时间=t0,备注="em/sina均不可达,不造数"),
                  open(mp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print("接口全失败,已记meta,不造数"); return
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    for c in ("今开","昨收","最新价","成交额"): df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df[(df["昨收"]>0)&df["今开"].notna()].copy()
    df["高开幅度"]=((df["今开"]/df["昨收"]-1)*100).round(2)
    df["竞价额排名"]=df["成交额"].rank(ascending=False,method="min").astype("Int64")
    mv=pd.to_numeric(df["流通市值"],errors="coerce")
    df["竞价换手代理"]=(df["成交额"]/mv*100).round(4)  # %(9:26口径≈竞价换手)
    df=df.sort_values("成交额",ascending=False)
    df.to_csv(fp,index=False,compression="gzip",encoding="utf-8")
    hhmm=t0[:5]
    clean=hhmm<="09:30"
    json.dump(dict(日=d,状态="成功",来源=src,采集时间=t0,条数=int(len(df)),
        可信度=("A档:≤09:30,成交额≈集合竞价额" if clean else "污染:>09:30盘中累计,只留档不训练"),
        交易日核验="待傍晚以{d}/zt_pool.csv存在为准;节假日误跑的存档训练时须剔除"),
        open(mp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"{d} 全市场竞价快照 {len(df)}条 来源{src} 采集{t0} {'A档' if clean else '⚠污染口径'} → {fp}")
    print("竞价额Top10:")
    print(df.head(10)[["代码","名称","高开幅度","成交额","竞价额排名"]].to_string(index=False))
if __name__=="__main__":
    main(wait="--wait" in sys.argv,force="--force" in sys.argv)
