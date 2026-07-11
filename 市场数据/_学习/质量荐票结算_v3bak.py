# -*- coding: utf-8 -*-
"""质量荐票结算.py {昨日d} v3 —— 涨停复盘Top5荐票的T+1结算(傍晚跑,零编造)。
★执行口径为主:荐票=T+1开盘买入,执行收益=T+1收/T+1开-1;信号收益(收对收)仅参考。
v3新增:逐票结算追加 _学习/_荐票逐票结算.jsonl(带质量分/主导因子/执行收益)=因子校准审计线;
HTML卡"匹配桶"改"主导因子"(v3无单一桶,质量分=多因子加权)。"""
import os,sys,re,json,glob
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
def bars(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b
def main(dprev):
    jp=os.path.join(L,f"涨停质量荐票_{dprev}.json")
    if not os.path.isfile(jp): print("无荐票文件,跳过"); return
    top5=json.load(open(jp,encoding="utf-8"))["top5"][:5]
    days=sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE,"2026*")) if os.path.isdir(x)])
    dnext=next((x for x in days if x>dprev),None)
    ztset=set()
    if dnext and os.path.isfile(os.path.join(BASE,dnext,"zt_pool.csv")):
        zp=pd.read_csv(os.path.join(BASE,dnext,"zt_pool.csv"),dtype={"代码":str}); ztset=set(zp["代码"].str.zfill(6))
    res=[]; exes=[]
    for t in top5:
        c=t["代码"]; b=bars(c); row=dict(t); ope=exe=sig=None; feng=c in ztset
        if b is not None:
            idx=b.index[b['date']==dprev]
            if len(idx) and idx[0]+1<len(b):
                i=idx[0]; Tc=b.loc[i,'close']; o1=b.loc[i+1,'open']; c1=b.loc[i+1,'close']
                ope=round((o1/Tc-1)*100,2); exe=round((c1/o1-1)*100,2); sig=round((c1/Tc-1)*100,2)
        if exe is not None: exes.append(exe)
        verdict=("—" if exe is None else ("✓赚" if exe>0 else "✗套"))
        row.update(T1高开=ope,执行收益=exe,信号收益=sig,次日封板=feng,判定=verdict)
        res.append(row)
        open(os.path.join(L,"_荐票逐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
            荐票日=dprev,代码=c,名称=t.get("名称"),质量分=t.get("质量分"),预测执1胜率=t.get("预测执1胜率"),
            预测执1均涨=t.get("预测执1均涨"),主导因子=t.get("主导因子") or t.get("匹配桶"),
            T1高开=ope,执行收益=exe,判定=verdict,次日封板=feng),ensure_ascii=False)+"\n")
    n=len([r for r in res if r["执行收益"] is not None])
    win=sum(1 for r in res if (r["执行收益"] or 0)>0)
    out=dict(荐票日=dprev,结算日=dnext,Top5=res,
             汇总=dict(执行胜率=f"{win}/{n}" if n else "0/0",
                     执行均收=round(sum(exes)/len(exes),2) if exes else None,
                     次日封板=f'{sum(1 for r in res if r["次日封板"])}/{len(res)}'),
             口径="★执行口径为主=T+1开盘买入→T+1收盘;信号收益=收对收仅参考;封死一字开盘可能仍买不进=上界近似")
    json.dump(out,open(os.path.join(L,f"质量荐票结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    open(os.path.join(L,"_质量荐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,**out["汇总"]),ensure_ascii=False)+"\n")
    disp=dprev[4:6]+"-"+dprev[6:8]
    def g(r):
        if r["执行收益"] is None: return "—"
        return f'开{r["T1高开"]:+.1f}%→收{r["执行收益"]:+.1f}%<br><span class="mut">信号{r["信号收益"]:+.1f}%</span>'
    def lead(r):
        s=r.get("主导因子") or r.get("匹配桶") or ""
        return s if len(s)<=52 else s[:50]+"…"
    rows=''.join(f'<tr><td><b>{r["名称"]}</b><br><span class="mut">{r["代码"]}</span></td>'
        f'<td>{r["质量分"]}<br><span class="mut">{lead(r)}</span></td>'
        f'<td>执{r.get("预测执1胜率","—")}%/{r.get("预测执1均涨","—")}%</td>'
        f'<td>{g(r)}</td>'
        f'<td class="{"dA" if (r["执行收益"] or 0)>0 else "dC"}">{r["判定"]}{"·封" if r["次日封板"] else ""}</td></tr>' for r in res)
    blk=(f'<h2>昨日Top5结算 · {disp}荐票(执行口径T+1)</h2>'
     f'<div class="hint">★执行口径=T+1开盘买入→当日收盘(封死票T日买不进,只能次日开盘介入,这才是荐票能不能吃到肉)。汇总:执行胜率{out["汇总"]["执行胜率"]} · 执行均收{out["汇总"]["执行均收"]}% · 次日封板{out["汇总"]["次日封板"]}。信号口径(收对收)仅作参考、不作战绩。</div>'
     f'<div class="card"><table><tr><th>标的</th><th>质量分·主导因子</th><th>预测执行</th><th>实际(开盘买→收)</th><th>判定</th></tr>{rows}</table></div>')
    js=sorted(glob.glob(os.path.join(L,"judgment_*.json"))); jpath=js[-1]
    J=json.load(open(jpath,encoding="utf-8")); b2=J["bodies"].get("limitup","")
    b2=re.sub(r'<h2>昨日Top5结算.*?(?=<h2)','',b2,flags=re.S)
    anchor=b2.find('<h2>每日涨停归位台账');  anchor=anchor if anchor>=0 else b2.find('<!--LEDGER-->')
    b2=b2[:anchor]+blk+b2[anchor:]; J["bodies"]["limitup"]=b2
    json.dump(J,open(jpath,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"{disp} Top5执行结算: 胜率{out['汇总']['执行胜率']} 均收{out['汇总']['执行均收']}% | 已注入limitup+逐票jsonl")
    for r in res: print(f'  {r["名称"]} 开{r["T1高开"]}→执行{r["执行收益"]} {r["判定"]}')
if __name__=="__main__": main(sys.argv[1])
