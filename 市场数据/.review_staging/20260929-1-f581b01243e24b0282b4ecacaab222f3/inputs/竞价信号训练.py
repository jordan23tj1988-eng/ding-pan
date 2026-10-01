# -*- coding: utf-8 -*-
"""竞价信号训练.py —— 竞价信号(T日9:25-9:31可知)→T+1/T+2分口径胜率。同龙虎榜规则。
信号桶=首封时间档(一字9:25/秒板≤9:31/早盘≤10:00/盘中)×连板层。样本=本地zt_pool缓存(16交易日)。
收益=本地数据链路日线(不复权,1-2日窗除权噪声忽略并注明)。
口径: T+1观察=T收→T+1收; ★跟随=T+1收→T+2收(一字/秒板T+1开盘常仍强,保守用收盘价口径)。
产出: _学习/_竞价信号胜率.json/.md + 快照jsonl。零后视镜。"""
import os,sys,glob,json,datetime
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR="/tmp/jj_bars"; os.makedirs(CDIR,exist_ok=True)
def bars(code):
    f=os.path.join(CDIR,code+".csv")
    if os.path.isfile(f):
        try:
            b=pd.read_csv(f)
            return b if len(b) else None
        except Exception: return None
    return None
def fetch(codes,limit=400):
    import akshare as ak
    todo=[c for c in codes if not os.path.isfile(os.path.join(CDIR,c+".csv"))][:limit]
    def one(c):
        f=os.path.join(CDIR,c+".csv")
        try:
            pre="sh" if c[0] in "69" else ("bj" if c[0] in "48" else "sz")
            b=ak.stock_zh_a_daily(symbol=pre+c,start_date="20260601",end_date="20260708")
            b=b[["date","close"]]
            b.to_csv(f,index=False)
        except Exception:
            pd.DataFrame().to_csv(f,index=False)
    for c in todo: one(c)
    left=[c for c in codes if not os.path.isfile(os.path.join(CDIR,c+".csv"))]
    return len(left)==0
def seal_bucket(x):
    s=str(x).zfill(6); hm=s[:2]+":"+s[2:4]
    if hm<="09:25": return "竞价一字(9:25)"
    if hm<="09:31": return "秒板(≤9:31)"
    if hm<="10:00": return "早盘封(≤10:00)"
    return "盘中封"
def lb(n):
    try: n=int(n)
    except: return "首板"
    return "首板" if n<=1 else ("2板" if n==2 else "3板+")
def main():
    days=sorted([os.path.basename(p) for p in glob.glob(os.path.join(BASE,"2026*")) if os.path.isfile(os.path.join(p,"zt_pool.csv"))])
    rows=[]
    for i,d in enumerate(days[:-2]):  # 需T+2
        df=pd.read_csv(os.path.join(BASE,d,"zt_pool.csv"),dtype={"代码":str})
        for _,r in df.iterrows():
            code=str(r["代码"]).zfill(6); nm=str(r.get("名称",""))
            if "ST" in nm or "退" in nm: continue
            b=bars(code)
            if b is None or len(b)==0: continue
            b=b.reset_index() if "date" not in b.columns else b
            dcol="date" if "date" in b.columns else b.columns[0]
            b["_d"]=pd.to_datetime(b[dcol]).dt.strftime("%Y%m%d")
            idx=b.index[b["_d"]==d]
            if len(idx)==0 or idx[0]+2>=len(b): continue
            k=idx[0]; c0,c1,c2=float(b.loc[k,"close"]),float(b.loc[k+1,"close"]),float(b.loc[k+2,"close"])
            if not (c0>0 and c1>0): continue
            rows.append(dict(桶=seal_bucket(r.get("首次封板时间","")),层=lb(r.get("连板数",1)),
                r1=(c1/c0-1)*100, rf=(c2/c1-1)*100))
    df=pd.DataFrame(rows)
    def stat(d):
        n=len(d)
        if n<15: return None
        return dict(n=int(n),T1胜率=round(float((d.r1>0).mean()*100),1),T1均涨=round(float(d.r1.mean()),2),
            T2跟随胜率=round(float((d.rf>0).mean()*100),1),T2跟随均涨=round(float(d.rf.mean()),2))
    out={"窗口":f"{days[0]}~{days[-3]}","样本":int(len(df)),"口径":"T1=T收→T+1收(观察);T2跟随=T+1收→T+2收(可执行近似);不复权","基准":stat(df)}
    out["按竞价桶"]={k:stat(g) for k,g in df.groupby("桶") if stat(g)}
    out["竞价桶x连板层"]={f"{k1}|{k2}":stat(g) for (k1,k2),g in df.groupby(["桶","层"]) if stat(g)}
    json.dump(out,open(os.path.join(L,"_竞价信号胜率.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    md=["# 竞价信号胜率库(T+1/T+2口径,A档)\n",f"> {out['窗口']} 共{len(df)}样本。{out['口径']}\n",
        "\n| 桶 | n | T+1胜率 | T+1均涨 | ★T+2跟随胜率 | ★T+2跟随均涨 |\n|---|---|---|---|---|---|"]
    for k,v in list(out["按竞价桶"].items())+list(out["竞价桶x连板层"].items()):
        md.append(f"| {k} | {v['n']} | {v['T1胜率']}% | {v['T1均涨']}% | **{v['T2跟随胜率']}%** | **{v['T2跟随均涨']}%** |")
    b=out["基准"]; md.append(f"\n基准: n={b['n']} T1 {b['T1胜率']}%/{b['T1均涨']}% | T2跟随 {b['T2跟随胜率']}%/{b['T2跟随均涨']}%")
    open(os.path.join(L,"_竞价信号胜率.md"),"w",encoding="utf-8").write("\n".join(md))
    open(os.path.join(L,"竞价信号胜率快照.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(快照日=datetime.date.today().strftime("%Y%m%d"),data=out),ensure_ascii=False)+"\n")
    print("完成 样本",len(df))
def codes_needed():
    days=sorted([os.path.basename(p) for p in glob.glob(os.path.join(BASE,"2026*")) if os.path.isfile(os.path.join(p,"zt_pool.csv"))])
    cs=set()
    for d in days[:-2]:
        df=pd.read_csv(os.path.join(BASE,d,"zt_pool.csv"),dtype={"代码":str})
        for _,r in df.iterrows():
            nm=str(r.get("名称",""))
            if "ST" in nm or "退" in nm: continue
            cs.add(str(r["代码"]).zfill(6))
    return sorted(cs)
if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--fetch":
        done=fetch(codes_needed())
        print("FETCH_DONE" if done else "FETCH_MORE")
    else: main()
