# -*- coding: utf-8 -*-
"""质量荐票结算.py {昨日d} v4 —— Top5荐票T+1结算+归因反思(进化闭环,傍晚跑,零编造)。
★执行口径:荐票=T+1开盘买入,执行收益=T+1收/T+1开-1;信号收益(收对收)仅参考。
v4(2026-07-10,用户拍板"结算要折叠+要有反思"):
①结算html不再占limitup固定段,注入台账【荐票日日块】开头(当日涨停+当日荐票+T+1结算=一天完整档案,随日块折叠),末尾自动重跑台账组装。
②归因反思(自动进化闭环):逐票 预测vs实际 偏差;套/赚票主导因子聚合;Top5均收 vs 当日全场涨停执行均收=选股增益;
  反思写 _学习/_涨停质量反思.jsonl(喂04提炼+每晚重训自适应权重=三层进化);反思段一并注入日块。"""
import os,sys,re,json,glob,subprocess
from collections import Counter
import pandas as pd
try:
    from trading_calendar import next_trading_day
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trading_calendar import next_trading_day
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
sys.path.insert(0, BASE)
from _jsonl_append import append_dedup
CDIR=os.path.join(L,"_bars_cache")
def bars(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b
def exe_ret(c,dprev):
    b=bars(c)
    if b is None: return None,None,None
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None,None,None
    i=idx[0]; Tc=b.loc[i,'close']; o1=b.loc[i+1,'open']; c1=b.loc[i+1,'close']
    return round((o1/Tc-1)*100,2),round((c1/o1-1)*100,2),round((c1/Tc-1)*100,2)
def factors_of(s):
    """主导因子串→加分因子名列表(取'|拖累'之前,'因子名:'模式)"""
    s=(s or "").split("|")[0]
    return re.findall(r'([一-龥A-Za-z0-9]{2,12}):',s)
def main(dprev):
    jp=os.path.join(L,f"涨停质量荐票_{dprev}.json")
    if not os.path.isfile(jp): print("无荐票文件,跳过"); return
    j=json.load(open(jp,encoding="utf-8")); top5=j["top5"][:5]; allrows=j.get("明细",[])
    dnext=next_trading_day(dprev)  # ★A(2026-08-16):交易日历求下一交易日,防跨断档错配
    ztset=set()
    if dnext and os.path.isfile(os.path.join(BASE,dnext,"zt_pool.csv")):
        zp=pd.read_csv(os.path.join(BASE,dnext,"zt_pool.csv"),dtype={"代码":str}); ztset=set(zp["代码"].str.zfill(6))
    res=[]; exes=[]
    for t in top5:
        c=t["代码"]; row=dict(t); ope,exe,sig=exe_ret(c,dprev); feng=c in ztset
        if exe is not None: exes.append(exe)
        verdict=("—" if exe is None else ("✓赚" if exe>0 else "✗套"))
        row.update(T1高开=ope,执行收益=exe,信号收益=sig,次日封板=feng,判定=verdict)
        res.append(row)
        append_dedup(os.path.join(L,"_荐票逐票结算.jsonl"), dict(
            荐票日=dprev,代码=c,名称=t.get("名称"),质量分=t.get("质量分"),预测执1胜率=t.get("预测执1胜率"),
            预测执1均涨=t.get("预测执1均涨"),主导因子=t.get("主导因子") or t.get("匹配桶"),
            T1高开=ope,执行收益=exe,判定=verdict,次日封板=feng), ("荐票日","代码"))
    n=len(exes); win=sum(1 for e in exes if e>0)
    # ── 归因(A档全事实) ──
    mkt=[]
    for r in allrows:
        _,e,_=exe_ret(r["代码"],dprev)
        if e is not None: mkt.append(e)
    mkt_avg=round(sum(mkt)/len(mkt),2) if mkt else None
    top_avg=round(sum(exes)/len(exes),2) if exes else None
    edge=round(top_avg-mkt_avg,2) if (top_avg is not None and mkt_avg is not None) else None
    lose=Counter(); winf=Counter(); miss=[]
    for r in res:
        fs=factors_of(r.get("主导因子"))
        if r["判定"]=="✗套":
            lose.update(fs)
            miss.append(dict(代码=r["代码"],名称=r["名称"],预测执1均涨=r.get("预测执1均涨"),实际=r["执行收益"],
                             偏差=round((r["执行收益"] or 0)-(r.get("预测执1均涨") or 0),2)))
        elif r["判定"]=="✓赚": winf.update(fs)
    refl=(f"{dprev}荐票T+1结算:执行胜率{win}/{n},Top5均收{top_avg}% vs 全场涨停均收{mkt_avg}%"
      +(f"(增益{edge:+.2f}pp{'=选股有效' if edge and edge>0 else '=没跑赢全场,选股无增益'})" if edge is not None else "")
      +(f";套票共同加分因子:{'、'.join(f'{k}×{v}' for k,v in lose.most_common(3))}" if lose else "")
      +(f";赚票因子:{'、'.join(f'{k}×{v}' for k,v in winf.most_common(3))}" if winf else "")
      +"。样本进库→今晚重训权重自适应;连续打脸因子由04提炼降权复核。")
    append_dedup(os.path.join(L,"_涨停质量反思.jsonl"), dict(
        荐票日=dprev,结算日=dnext,执行胜率=f"{win}/{n}",Top5均收=top_avg,全场均收=mkt_avg,选股增益pp=edge,
        套票因子=dict(lose),赚票因子=dict(winf),打脸明细=miss,反思=refl), "荐票日")
    out=dict(荐票日=dprev,结算日=dnext,Top5=res,
             汇总=dict(执行胜率=f"{win}/{n}" if n else "0/0",执行均收=top_avg,全场均收=mkt_avg,选股增益pp=edge,
                     次日封板=f'{sum(1 for r in res if r["次日封板"])}/{len(res)}'),
             口径="★执行口径=T+1开盘买入→T+1收盘;信号收益=收对收仅参考;封死一字开盘可能仍买不进=上界近似")
    json.dump(out,open(os.path.join(L,f"质量荐票结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    append_dedup(os.path.join(L,"_质量荐票结算.jsonl"), dict(荐票日=dprev,**out["汇总"]), "荐票日")
    # ── html:注入荐票日日块开头(随日块折叠) ──
    disp=dprev[4:6]+"-"+dprev[6:8]
    def pred(r):
        pe=r.get("预测执1胜率"); pr=r.get("预测执1均涨")
        if pe is None or pr is None: return '<span class="mut">—(v2旧口径无执行预测)</span>'
        return f'执1 {pe}%/{pr:+.2f}%'
    def g(r):
        if r["执行收益"] is None: return "—"
        return f'开{r["T1高开"]:+.1f}%→收{r["执行收益"]:+.1f}%<br><span class="mut">信号{r["信号收益"]:+.1f}%</span>'
    rows_h=''.join(f'<tr><td style="white-space:nowrap"><b>{r["名称"]}</b><br><span class="mut">{r["代码"]}</span></td>'
        f'<td style="white-space:nowrap"><b>{r["质量分"]}</b></td>'
        f'<td style="white-space:nowrap">{pred(r)}</td>'
        f'<td style="white-space:nowrap">{g(r)}</td>'
        f'<td class="{"dA" if (r["执行收益"] or 0)>0 else "dC"}" style="white-space:nowrap">{r["判定"]}{"·封" if r["次日封板"] else ""}</td></tr>' for r in res)
    blk=(f'<p style="font-weight:700;margin:4px 0 4px;border-left:3px solid var(--accent);padding-left:8px">当日Top5荐票 · T+1结算对账(执行口径)</p>'
     f'<div class="hint">汇总:执行胜率{out["汇总"]["执行胜率"]} · Top5均收{top_avg}% vs 全场{mkt_avg}%'
     +(f'(增益{edge:+.2f}pp)' if edge is not None else '')+f' · 次日封板{out["汇总"]["次日封板"]}。T+1开盘买入→收盘;信号口径仅参考。</div>'
     f'<div class="card"><table style="table-layout:fixed;width:100%"><colgroup><col style="width:112px"><col style="width:42px"><col style="width:150px"><col><col style="width:74px"></colgroup>'
     f'<tr><th>标的</th><th>分</th><th>预测执行</th><th>实际(开盘买→收)</th><th>判定</th></tr>{rows_h}</table></div>'
     f'<div class="card" style="background:#faf7f0"><b>自动归因反思</b> <span class="mut">(A档事实,喂04提炼;权重每晚重训自适应)</span><br>{refl}</div>')
    dp=os.path.join(L,"涨停复盘存档",f"{dprev}.json")
    if os.path.isfile(dp):
        D=json.load(open(dp,encoding="utf-8"))
        h=re.sub(r'<p style="[^"]*">当日Top5荐票 · T\+1结算对账.*?(?=<p style|<div class="strip")','',D["html"],flags=re.S)  # 幂等:先删旧结算块
        D["html"]=blk+h
        json.dump(D,open(dp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        subprocess.run([sys.executable,os.path.join(BASE,"涨停复盘台账.py")],check=True)
        inj="已注入日块"+dprev+"+台账重组装"
    else: inj="⚠无该日日块,结算json已存但未注入页面"
    print(f"{disp} Top5执行结算: 胜率{out['汇总']['执行胜率']} Top5均收{top_avg}% vs 全场{mkt_avg}% 增益{edge}pp | {inj}")
    print("反思:",refl)
if __name__=="__main__": main(sys.argv[1])
