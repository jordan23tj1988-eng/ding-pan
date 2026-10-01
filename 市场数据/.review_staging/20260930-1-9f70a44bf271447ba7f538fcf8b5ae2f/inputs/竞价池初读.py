# -*- coding: utf-8 -*-
"""竞价池初读.py {昨日d} —— 早盘固化步骤:对昨日竞价选股池(zt_pool首封≤9:31)做今晨T+1竞价初读。
零编造:昨日池由 {昨日d}/zt_pool.csv 首封≤09:31 确定性重建;今晨行情走sina实时(hq.sinajs.cn)。
规则初读判定(A档):盘中封板=✓兑现/高开≥4未封=◐/平开=未兑现/低开≤-2=✗打脸/现涨≤-8=✗✗近跌停。
产出 _学习/竞价池初读_{昨日d}.json(含初读判定/解读)。2026-08-16起不再注入judgment auction(竞价路改六段,盘中竞价强势归盘中作战页)。完整封板收益终结算由18:00傍晚场做。"""
import os,sys,re,json,glob,datetime,urllib.request
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
def sina(codes):
    out={}
    if not codes: return out
    lst=",".join(("sh" if c[0] in "69" else "sz")+c for c in codes)
    req=urllib.request.Request("https://hq.sinajs.cn/list="+lst,headers={"Referer":"https://finance.sina.com.cn"})
    for l in urllib.request.urlopen(req,timeout=10).read().decode("gbk").strip().split("\n"):
        mm=re.search(r'str_(?:sh|sz)(\d{6})="([^"]*)"',l)
        if not mm: continue
        p=mm.group(2).split(",")
        if len(p)>10 and float(p[2])>0:
            out[mm.group(1)]=dict(今开=float(p[1]),昨收=float(p[2]),现价=float(p[3]),高=float(p[4]))
    return out
def lim(c): return 19.9 if c[:2] in("30","68") else 9.9
def build_pool(dprev):
    df=pd.read_csv(os.path.join(BASE,dprev,"zt_pool.csv"),dtype={"代码":str})
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    def hm(x): s=str(x).split(".")[0].zfill(6); return s[:2]+":"+s[2:4]
    pool=[]
    for _,r in df.iterrows():
        fb=hm(r["首次封板时间"])
        if fb>"09:31": continue
        lb=int(pd.to_numeric(r.get("连板数",1),errors="coerce") or 1)
        mv=pd.to_numeric(r.get("流通市值"),errors="coerce"); fj=pd.to_numeric(r.get("封板资金"),errors="coerce")
        fdb=round(float(fj)/float(mv)*100,2) if (mv and mv>0 and fj==fj) else None
        sig=("一字" if fb<="09:25" else "秒板")+(f"·{lb}板" if lb>1 else "·首板")
        pool.append(dict(代码=r["代码"],名称=str(r["名称"]),首封=fb,连板=lb,信号=sig,封单比=fdb,行业=str(r.get("所属行业",""))))
    return sorted(pool,key=lambda x:x["首封"])
def verdict(c,d):
    if not d: return ("dB","—未取到","")
    gk,cur=d["高开"],d["现涨"]
    if d["封板"]: return ("dA","✓封板(T+1兑现)","盘中封板,竞价信号兑现")
    if cur<=-8: return ("dC","✗✗近跌停","高位崩,最差")
    if gk<=-2: return ("dC","✗低开走弱","低开打脸,竞价信号证伪")
    if gk>=4: return ("dB","◐高开未封","竞价冲高但未封,盯回落")
    return ("dB","平开未兑现","无方向,竞价信号未兑现")
def main(dprev):
    pool=build_pool(dprev)
    q=sina([p["代码"] for p in pool])
    seal=0
    for p in pool:
        s=q.get(p["代码"]); d=None
        if s:
            d=dict(高开=round((s["今开"]/s["昨收"]-1)*100,2),现涨=round((s["现价"]/s["昨收"]-1)*100,2),
                   盘中高=round((s["高"]/s["昨收"]-1)*100,2),封板=(s["现价"]/s["昨收"]-1)*100>=lim(p["代码"])-0.1)
            if d["封板"]: seal+=1
        p["今晨"]=d
        if d:
            _, tag, why = verdict(p["代码"], d)
            p["初读判定"]=tag; p["初读解读"]=why
        else:
            p["初读判定"]="—未取到"; p["初读解读"]=""
    n=len(pool); rate=round(seal/n*100) if n else 0
    out=dict(池日=dprev,初读日=datetime.date.today().strftime("%Y%m%d"),初读时间=datetime.datetime.now().strftime("%H:%M"),
             池家数=n,盘中封板=seal,封板率=rate,明细=pool)
    json.dump(out,open(os.path.join(L,f"竞价池初读_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # 2026-08-16 起不再注入 judgment auction: 竞价路改六段, 盘中竞价强势(初读)移出竞价页→盘中作战页
    print(f"{dprev[4:6]}-{dprev[6:8]}池初读: {n}只 盘中封板{seal}/{n}={rate}% → _学习/竞价池初读_{dprev}.json (盘中判定归盘中作战页)")
    for p in pool:
        d=p["今晨"]; print(f'  {p["名称"]}({p["代码"]}) {p["信号"]:8} '+(f'高开{d["高开"]:+.1f}% 现{d["现涨"]:+.1f}% {"封" if d["封板"] else "未"}' if d else "未取到"))
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else (sorted(glob.glob(os.path.join(BASE,"2026*")))[-1].split(os.sep)[-1]))
