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

def fetch_ifind_spot():
    """iFinD兜底(2026-08-14修正): 代码表改用量价因子库全A清单(原iwencai\"全部A股\"只返回84只ST,已弃)；
    RealtimeQuotes分批500取open/preClose/latest/amount。约25s,IPC零风控。"""
    import pandas as pd
    import iFinDPy, json as _j
    try:
        a = _j.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
        iFinDPy.THS_iFinDLogin(a["account"], a["password"])
        codes, names = None, {}
        lst = os.path.join(r"D:\股票数据\量价因子库\data\meta", "stock_list.csv")
        if os.path.isfile(lst):
            codes = [str(c).strip() for c in pd.read_csv(lst)["code"].tolist()]
        else:
            r = iFinDPy.THS_iwencai("全部A股", "stock")
            tbl = (r.get("tables") or [{}])[0].get("table")
            if not isinstance(tbl, dict) or not tbl.get("股票代码"):
                print("iFinD代码表失败"); return None, None
            codes = [str(c) for c in tbl["股票代码"]]
            names = dict(zip([str(c) for c in tbl["股票代码"]],
                             [str(n) for n in tbl.get("股票简称", [])]))
        rows = []
        for i in range(0, len(codes), 500):
            batch = codes[i:i+500]
            rt = iFinDPy.THS_RealtimeQuotes(",".join(batch), "open;preClose;latest;amount")
            if not isinstance(rt, dict) or rt.get("errorcode") != 0:
                print("iFinD分批失败 i=%d" % i); continue
            for t in rt.get("tables") or []:
                code = t.get("thscode")
                nt = t.get("table")
                if not code or not isinstance(nt, dict):
                    continue
                def _last(k):
                    v = nt.get(k)
                    return v[-1] if isinstance(v, list) and v else None
                rows.append({"代码": code.split(".")[0], "名称": names.get(code, ""),
                             "今开": _last("open"), "昨收": _last("preClose"),
                             "最新价": _last("latest"), "成交额": _last("amount"),
                             "流通市值": None})
        if not rows:
            print("iFinD无数据"); return None, None
        return pd.DataFrame(rows), "ifind_rt"
    except Exception as e:
        print("iFinD兜底失败:", e)
        return None, None

def fetch():
    """全A实时spot:东财em优先,iFinD次之,sina末位。返回(df,来源) df列=代码,名称,今开,昨收,最新价,成交额"""
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
    df,src=fetch_ifind_spot()
    if df is not None: return df,src
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
    # 名称补齐(2026-08-14加): iFinD RealtimeQuotes不返回name字段→用akshare代码名称表(缓存兜底)
    if "名称" in df.columns and df["名称"].fillna("").astype(str).str.strip().eq("").mean()>0.3:
        try:
            nmf=os.path.join(ARC,"代码名称映射.csv")
            if os.path.isfile(nmf):
                nm=pd.read_csv(nmf,dtype={"code":str}); nm["code"]=nm["code"].str.zfill(6)
            else:
                import akshare as ak
                nm=ak.stock_info_a_code_name(); nm["code"]=nm["code"].astype(str).str.zfill(6)
                nm.to_csv(nmf,index=False,encoding="utf-8-sig")
            nm=nm.drop_duplicates("code").rename(columns={"code":"代码","name":"_名称"})
            df=df.merge(nm,on="代码",how="left")
            df["名称"]=df["_名称"].fillna(df["名称"]).fillna("")
            df=df.drop(columns="_名称")
        except Exception as e:
            print("名称补齐失败(不影响存档):",e)
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
