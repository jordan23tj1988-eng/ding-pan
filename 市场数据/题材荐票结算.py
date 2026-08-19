# -*- coding: utf-8 -*-
"""题材荐票结算.py {荐票日d} —— 第三路(题材命门)荐票T+1结算(2026-07-11建,照质量/逻辑路骨架)。
★执行口径:荐票=T+1开盘买入,执行收益=T+1收/T+1开-1;发出版 _学习/题材荐票_{d}.json 不可覆盖。
产出:题材荐票结算_{d}.json + 追加 _题材荐票结算.jsonl(汇总) + _题材荐票反思.jsonl(按身位归因) + 题材荐票结算卡_{d}.html(嵌theme页对账区)。
基准:当日全场涨停执行均收(读 质量荐票结算_{d}.json 的全场均收,同源可比)。
bars: _bars_cache 优先,缺票akshare stock_zh_a_daily(sina)兜底;拿不到标null不编。"""
import os,sys,json,glob
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
sys.path.insert(0, BASE)
from _jsonl_append import append_dedup
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
def main(dprev):
    jp=os.path.join(L,f"题材荐票_{dprev}.json")
    if not os.path.isfile(jp): print("无题材荐票发出版,跳过"); return
    j=json.load(open(jp,encoding="utf-8")); picks=j.get("荐票",[])
    days=sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE,"2026*")) if os.path.isdir(x)])
    dnext=next((x for x in days if x>dprev),None)
    ztset=set()
    if dnext and os.path.isfile(os.path.join(BASE,dnext,"zt_pool.csv")):
        zp=pd.read_csv(os.path.join(BASE,dnext,"zt_pool.csv"),dtype={"代码":str}); ztset=set(zp["代码"].str.zfill(6))
    res=[]; exes=[]
    for t in picks:
        c=str(t["代码"]).zfill(6); row=dict(t); ope,exe,sig=exe_ret(c,dprev)
        if exe is not None: exes.append(exe)
        verdict=("—" if exe is None else ("✓赚" if exe>0 else "✗套"))
        row.update(T1高开=ope,执行收益=exe,信号收益=sig,次日封板=c in ztset,判定=verdict)
        res.append(row)
    n=len(exes); win=sum(1 for e in exes if e>0)
    top_avg=round(sum(exes)/n,2) if n else None
    mkt_avg=None
    qp=os.path.join(L,f"质量荐票结算_{dprev}.json")
    if os.path.isfile(qp): mkt_avg=json.load(open(qp,encoding="utf-8")).get("汇总",{}).get("全场均收")
    edge=round(top_avg-mkt_avg,2) if (top_avg is not None and mkt_avg is not None) else None
    bypos={}
    for r in res:
        if r["执行收益"] is None: continue
        bypos.setdefault(r.get("身位","?"),[]).append(r["执行收益"])
    bypos={k:round(sum(v)/len(v),2) for k,v in bypos.items()}
    refl=(f"{dprev}题材路结算:执行胜率{win}/{n},均收{top_avg}%"
      +(f" vs 全场涨停{mkt_avg}%(增益{edge:+.2f}pp)" if edge is not None else "")
      +(f";按身位均收:{bypos}" if bypos else "")+"。")
    out=dict(荐票日=dprev,结算日=dnext,明细=res,
        汇总=dict(执行胜率=f"{win}/{n}" if n else "0/0",执行均收=top_avg,全场涨停均收=mkt_avg,增益pp=edge,按身位=bypos),
        口径="★执行口径=T+1开盘买入→T+1收盘;发出版名单结算,不可事后增删")
    json.dump(out,open(os.path.join(L,f"题材荐票结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    append_dedup(os.path.join(L,"_题材荐票结算.jsonl"), dict(荐票日=dprev,**out["汇总"]), "荐票日")
    append_dedup(os.path.join(L,"_题材荐票反思.jsonl"), dict(荐票日=dprev,结算日=dnext,反思=refl,明细=[dict(代码=r["代码"],名称=r["名称"],身位=r.get("身位"),执行收益=r["执行收益"],判定=r["判定"]) for r in res]), "荐票日")
    disp=dprev[4:6]+"-"+dprev[6:8]
    rows="".join(f'<tr><td><b>{r["名称"]}</b> <span class="mut">{r["代码"]}</span></td><td>{r.get("身位","")}</td>'
        f'<td>{"" if r["T1高开"] is None else format(r["T1高开"],"+.2f")+"%"}</td>'
        f'<td>{"null" if r["执行收益"] is None else format(r["执行收益"],"+.2f")+"%"}</td>'
        f'<td>{"封板" if r["次日封板"] else ""} {r["判定"]}</td></tr>' for r in res)
    card=(f'<div class="card"><b>{disp}发出版结算(T+1执行口径):胜率{out["汇总"]["执行胜率"]},均收{top_avg}%'
      +(f' vs 全场涨停{mkt_avg}%(增益{edge:+.2f}pp)' if edge is not None else '')+'</b>'
      +'<table><tr><th>票</th><th>身位</th><th>T+1高开</th><th>执行收益</th><th>判定</th></tr>'+rows+'</table></div>')
    open(os.path.join(L,f"题材荐票结算卡_{dprev}.html"),"w",encoding="utf-8").write(card)
    print(refl)
if __name__=="__main__":
    main(sys.argv[1])
