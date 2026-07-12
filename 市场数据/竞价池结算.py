# -*- coding: utf-8 -*-
"""竞价池结算.py {池日d} —— 竞价路(第一路)选股池T+1终结算(2026-07-11建,照质量/席位/题材/逻辑路骨架)。
★池=零后视镜确定性重建({d}/zt_pool.csv 首封≤09:31,一字=首封≤09:25),首次结算时冻结 _学习/竞价池发出_{d}.json,之后只读冻结版(发出版不可覆盖)。
★执行口径:T+1开盘买入→T+1收盘。产出:竞价池结算_{d}.json + 追加 _竞价池结算.jsonl + _竞价池反思.jsonl(按信号/连板/高开档/评分半区归因,验证"低开有肉高开套") + 竞价池结算卡_{d}.html(嵌auction页终结算段)。
基准:当日全场涨停执行均收(读 质量荐票结算_{d}.json 同源可比)。bars缺票sina兜底;拿不到标null不编。
2026-07-12评分体系联动:join昨晚竞价评分_{d}.json(分数唯一源)→结算表加竞价分列+高分半/低分半战绩+闸门对账。"""
import os,sys,json,glob
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
def _sina_sym(c): return ('bj' if c.startswith(('4','8','92')) else 'sh' if c.startswith(('6','5','9')) else 'sz')+c
def bars(c):
    f=os.path.join(CDIR,c+".csv")
    if os.path.isfile(f):
        b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b
    try:
        import akshare as ak
        b=ak.stock_zh_a_daily(symbol=_sina_sym(c))
        b['date']=b['date'].astype(str).str.replace('-','')
        b=b[['date','open','close']].reset_index(drop=True)
        b.to_csv(f,index=False); return b
    except Exception as e:
        print('bars兜底失败',c,e); return None
def exe_ret(c,dprev):
    b=bars(c)
    if b is None: return None,None,None
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None,None,None
    i=idx[0]; Tc=float(b.loc[i,'close']); o1=float(b.loc[i+1,'open']); c1=float(b.loc[i+1,'close'])
    return round((o1/Tc-1)*100,2),round((c1/o1-1)*100,2),round((c1/Tc-1)*100,2)
def _junk(name):
    """ST/退/N/C统计层剔除(2026-07-11 P0-2);已冻结的历史发出版不回改。"""
    s=str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")
def build_pool(d):
    df=pd.read_csv(os.path.join(BASE,d,"zt_pool.csv"),dtype={"代码":str})
    df=df[~df["名称"].astype(str).map(_junk)]
    df["代码"]=df["代码"].astype(str).str.zfill(6)
    def hm(x): s=str(x).split(".")[0].zfill(6); return s[:2]+":"+s[2:4]
    pool=[]
    for _,r in df.iterrows():
        fb=hm(r["首次封板时间"])
        if fb>"09:31": continue
        lb=int(pd.to_numeric(r.get("连板数",1),errors="coerce") or 1)
        mv=pd.to_numeric(r.get("流通市值"),errors="coerce"); fj=pd.to_numeric(r.get("封板资金"),errors="coerce")
        fdb=round(float(fj)/float(mv)*100,2) if (mv and mv>0 and fj==fj) else None
        zha=int(pd.to_numeric(r.get("炸板次数",0),errors="coerce") or 0)
        sig=("一字" if fb<="09:25" else "秒板")+(f"·{lb}板" if lb>1 else "·首板")
        pool.append(dict(代码=r["代码"],名称=str(r["名称"]),首封=fb,连板=lb,信号=sig,封单比=fdb,炸板=zha))
    return sorted(pool,key=lambda x:x["首封"])
def freeze_pool(d):
    fp=os.path.join(L,f"竞价池发出_{d}.json")
    if os.path.isfile(fp): return json.load(open(fp,encoding="utf-8"))["池"],True
    pool=build_pool(d)
    json.dump(dict(池日=d,口径="零后视镜确定性池:zt_pool首封≤09:31;一字=首封≤09:25;发出版不可覆盖",池=pool),
              open(fp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    return pool,False
def _avg(v): return round(sum(v)/len(v),2) if v else None
def load_scores(dprev):
    """2026-07-12评分体系联动:昨晚竞价评分_{d}.json → {代码:竞价分};缺文件返回{}"""
    fp=os.path.join(L,f"竞价评分_{dprev}.json")
    if not os.path.isfile(fp): return {}
    try: return {str(r["代码"]).zfill(6):r.get("竞价分") for r in json.load(open(fp,encoding="utf-8"))["明细"]}
    except Exception: return {}
def main(dprev):
    pool,frozen=freeze_pool(dprev)
    scores=load_scores(dprev)
    days=sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE,"2026*")) if os.path.isdir(x)])
    dnext=next((x for x in days if x>dprev),None)
    ztset=set()
    if dnext and os.path.isfile(os.path.join(BASE,dnext,"zt_pool.csv")):
        zp=pd.read_csv(os.path.join(BASE,dnext,"zt_pool.csv"),dtype={"代码":str}); ztset=set(zp["代码"].str.zfill(6))
    res=[]; exes=[]
    for t in pool:
        c=str(t["代码"]).zfill(6); row=dict(t); ope,exe,sig=exe_ret(c,dprev)
        if exe is not None: exes.append(exe)
        feng=c in ztset
        verdict=("—" if exe is None else ("✓封" if feng else ("✓可吃" if exe>0 else "✗套")))
        row.update(T1高开=ope,执行收益=exe,信号收益=sig,次日封板=feng,判定=verdict,竞价分=scores.get(c))
        res.append(row)
    n=len(exes); win=sum(1 for e in exes if e>0); seal=sum(1 for r in res if r["次日封板"])
    top_avg=_avg(exes)
    mkt_avg=None
    qp=os.path.join(L,f"质量荐票结算_{dprev}.json")
    if os.path.isfile(qp): mkt_avg=json.load(open(qp,encoding="utf-8")).get("汇总",{}).get("全场均收")
    edge=round(top_avg-mkt_avg,2) if (top_avg is not None and mkt_avg is not None) else None
    ok=[r for r in res if r["执行收益"] is not None]
    bysig={"一字":_avg([r["执行收益"] for r in ok if r["信号"].startswith("一字")]),
           "秒板":_avg([r["执行收益"] for r in ok if r["信号"].startswith("秒板")])}
    bylb={"首板":_avg([r["执行收益"] for r in ok if r["连板"]==1]),
          "2板+":_avg([r["执行收益"] for r in ok if r["连板"]>=2])}
    gk=[r for r in ok if r["T1高开"] is not None]
    bygk={"低开≤0":_avg([r["执行收益"] for r in gk if r["T1高开"]<=0]),
          "高开0~5":_avg([r["执行收益"] for r in gk if 0<r["T1高开"]<5]),
          "高开≥5":_avg([r["执行收益"] for r in gk if r["T1高开"]>=5])}
    sc_ok=[r for r in ok if r.get("竞价分") is not None]
    byscore=None
    if len(sc_ok)>=4:
        med=sorted(r["竞价分"] for r in sc_ok)[len(sc_ok)//2]
        hi=[r["执行收益"] for r in sc_ok if r["竞价分"]>=med]; lo=[r["执行收益"] for r in sc_ok if r["竞价分"]<med]
        byscore={"高分半":_avg(hi),"低分半":_avg(lo),"分界":med}
    gate_in=[r["执行收益"] for r in gk if r["T1高开"]<5]
    bygate={"闸门内均收":_avg(gate_in),"闸门内只数":len(gate_in),"全池均收":top_avg}
    refl=(f"{dprev}竞价池终结算:池{len(pool)}只,次日封板{seal}/{len(pool)},执行胜率{win}/{n},均收{top_avg}%"
      +(f" vs 全场涨停{mkt_avg}%(增益{edge:+.2f}pp)" if edge is not None else "")
      +f";按信号:{bysig};按连板:{bylb};按高开档:{bygk}(验证'低开有肉高开套')"
      +(f";按评分半区:{byscore}" if byscore else "")+f";闸门对账:{bygate}。")
    out=dict(池日=dprev,结算日=dnext,明细=res,
        汇总=dict(池家数=len(pool),次日封板=f"{seal}/{len(pool)}",执行胜率=f"{win}/{n}" if n else "0/0",
                执行均收=top_avg,全场涨停均收=mkt_avg,增益pp=edge,按信号=bysig,按连板=bylb,按高开档=bygk,
                按评分半区=byscore,闸门对账=bygate),
        口径="★执行口径=T+1开盘买入→T+1收盘;池=发出版冻结名单,不可事后增删;竞价分=昨晚竞价评分json(分数唯一源)")
    json.dump(out,open(os.path.join(L,f"竞价池结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    open(os.path.join(L,"_竞价池结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(池日=dprev,**{k:v for k,v in out["汇总"].items() if k not in("按信号","按连板","按高开档","按评分半区","闸门对账")}),ensure_ascii=False)+"\n")
    open(os.path.join(L,"_竞价池反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(池日=dprev,结算日=dnext,反思=refl,按信号=bysig,按连板=bylb,按高开档=bygk,按评分半区=byscore,闸门对账=bygate),ensure_ascii=False)+"\n")
    disp=dprev[4:6]+"-"+dprev[6:8]
    has_sc=any(r.get("竞价分") is not None for r in res)
    rows="".join(f'<tr><td style="white-space:nowrap"><b>{r["名称"]}</b> <span class="mut">{r["代码"]}</span></td><td>{r["信号"]}{("·炸"+str(r["炸板"])) if r.get("炸板") else ""}</td>'
        +(f'<td>{"—" if r.get("竞价分") is None else r["竞价分"]}</td>' if has_sc else '')
        +f'<td>{"" if r["T1高开"] is None else format(r["T1高开"],"+.1f")+"%"}</td>'
        f'<td>{"null" if r["执行收益"] is None else format(r["执行收益"],"+.2f")+"%"}</td>'
        f'<td>{r["判定"]}</td></tr>' for r in res)
    card=(f'<div class="card"><b>{disp}竞价池终结算(T+1执行口径):次日封板{seal}/{len(pool)},胜率{out["汇总"]["执行胜率"]},均收{top_avg}%'
      +(f' vs 全场涨停{mkt_avg}%(增益{edge:+.2f}pp)' if edge is not None else '')+'</b>'
      +'<table><tr><th>票</th><th>信号</th>'+('<th>竞价分</th>' if has_sc else '')+'<th>T+1高开</th><th>执行收益</th><th>判定</th></tr>'+rows+'</table>'
      +f'<p><b>归因(A档):</b>按信号 一字{bysig["一字"]}% / 秒板{bysig["秒板"]}%;按连板 首板{bylb["首板"]}% / 2板+{bylb["2板+"]}%;按高开档 低开≤0:{bygk["低开≤0"]}% / 0~5:{bygk["高开0~5"]}% / ≥5:{bygk["高开≥5"]}%'
      +(f';评分半区 高分半{byscore["高分半"]}% / 低分半{byscore["低分半"]}%' if byscore else '')
      +f';闸门内(高开&lt;5){bygate["闸门内均收"]}%×{bygate["闸门内只数"]}只 vs 全池{top_avg}%。</p></div>')
    open(os.path.join(L,f"竞价池结算卡_{dprev}.html"),"w",encoding="utf-8").write(card)
    print(refl)
if __name__=="__main__":
    main(sys.argv[1])
