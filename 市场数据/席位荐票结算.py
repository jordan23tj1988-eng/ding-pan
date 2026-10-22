# -*- coding: utf-8 -*-
"""席位荐票结算.py {昨日d} —— 席位路Top5的T+1结算+按席位归因反思(09号进化闭环)。
执行口径=T+1开盘买入→T+1收。归因主体=席位(谁立功/谁打脸);打脸席位样本进事实表→每晚rank重算自动掉档=自我净化。
反思追加 _学习/_席位荐票反思.jsonl;结算+反思html注入台账{昨日}日块;自动重跑台账组装。"""
import os,sys,re,json,glob,subprocess
from collections import defaultdict
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
sys.path.insert(0, BASE)
from _jsonl_append import append_dedup
CDIR=os.path.join(L,"_bars_cache")
def exe_ret(c,dprev):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None,None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None,None
    i=idx[0]; o1=b.loc[i+1,'open']; c1=b.loc[i+1,'close']
    return round((o1/b.loc[i,'close']-1)*100,2),round((c1/o1-1)*100,2)
def exe_px(c,dprev):
    """执行日(次日)开盘价/收盘价；无数据返 (None,None)"""
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None,None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None,None
    i=idx[0]; return round(float(b.loc[i+1,'open']),3),round(float(b.loc[i+1,'close']),3)
def feng_ratio(c,d):
    """封单比双口径(%): 返回 (封单/当日成交额, 封单/流通市值)。缺源/不在涨停池→(None,None)。
    MA-20261021-03③: 门槛一律用『成交』口径, 『流通』口径只作结构参考。"""
    f=os.path.join(BASE,d,"zt_pool.csv")
    if not os.path.isfile(f): return None,None
    try:
        z=pd.read_csv(f,dtype={"代码":str})
        z["代码"]=z["代码"].astype(str).str.strip().str.zfill(6)
        r=z[z["代码"]==str(c).strip().zfill(6)]
        if not len(r): return None,None
        r=r.iloc[0]
        fg=float(r["封板资金"]); amt=float(r["成交额"]); cmv=float(r["流通市值"])
        return (round(fg/amt*100,2) if amt else None, round(fg/cmv*100,3) if cmv else None)
    except Exception:
        return None,None
def settle_formal(dprev):
    """正式荐票段: 条数==交易计划_lhb_{dprev}#buys; buy_px==执行日open; 落带外/无价→闸门未落,收益None不进分母"""
    tp=os.path.join(L,f"交易计划_lhb_{dprev}.json")
    if not os.path.isfile(tp): return None
    buys=json.load(open(tp,encoding="utf-8")).get("buys",[])
    out=[]
    for b in buys:
        ope,cls=exe_px(b["代码"],dprev)
        gate=b.get("buy_gate") or b.get("可选buy_gate") or {}
        ret=None if (ope is None or cls is None) else round((cls/ope-1)*100,2)
        rb,tb=feng_ratio(b["代码"],dprev)
        out.append(dict(代码=b["代码"],名称=b.get("名称",""),权重=b.get("权重%"),
                        buy_px=ope,close_px=cls,执行收益=ret,
                        判定=("闸门未落" if ope is None else ("✓赚" if (ret or 0)>0 else "✗套")),
                        封单比=dict(成交=rb,流通=tb),
                        封单比门槛口径="封板质量三项门槛一律用『成交』口径(封单/当日成交额);『流通』口径仅作结构参考,不参与取舍",
                        gate=gate))
    return out
def main(dprev,dry=False):
    """dry=True 只算不写(不落盘/不改jsonl/不重渲/不跑台账), 用于自检。"""
    jp=os.path.join(L,f"席位荐票_{dprev}.json")
    if not os.path.isfile(jp): print("无席位荐票,跳过"); return
    top=json.load(open(jp,encoding="utf-8"))["top5"]
    res=[]; exes=[]; seat_acc=defaultdict(list)
    for t in top:
        ope,exe=exe_ret(t["代码"],dprev)
        if exe is not None: exes.append(exe)
        v=("—待结算" if exe is None else ("✓赚" if exe>0 else "✗套"))
        res.append(dict(t,T1高开=ope,执行收益=exe,判定=v))
        for s in t["席位"]: seat_acc[f'[{s["档"]}]{s["名"]}'].append(exe)
    n=len(exes); win=sum(1 for e in exes if e>0)
    avg=round(sum(exes)/n,2) if n else None
    hero=[k for k,v in seat_acc.items() if v and all(x is not None and x>0 for x in v)]
    flop=[k for k,v in seat_acc.items() if v and all(x is not None and x<=0 for x in v)]
    refl=(f"{dprev}席位路Top5结算:执行胜率{win}/{n},均收{avg}%"
      +(f";立功席位:{'、'.join(x[:24] for x in hero[:3])}" if hero else "")
      +(f";打脸席位:{'、'.join(x[:24] for x in flop[:3])}" if flop else "")
      +"。打脸笔已在事实表,今晚rank重算自动压档=净化;连续打脸席位由08提炼在五路裁决降权。") if n else f"{dprev}席位路Top5待T+1收盘结算(首期)。"
    formal=settle_formal(dprev)
    fb=len(formal) if formal is not None else None
    fwin=sum(1 for x in (formal or []) if (x["执行收益"] or 0)>0)
    fnum=sum(1 for x in (formal or []) if x["执行收益"] is not None)
    fdrop=sum(1 for x in (formal or []) if x["执行收益"] is None)
    payload=dict(荐票日=dprev,Top5=res,
        正式荐票=(formal if formal is not None else []),
        正式荐票汇总=dict(条数=fb,已结算=fnum,无执行价剔除数=fdrop,执行胜率=f"{fwin}/{fnum}",均收=(round(sum(x["执行收益"] for x in formal if x["执行收益"] is not None)/fnum,2) if fnum else None)),
        正式荐票口径="来自 交易计划_lhb_{d}#buys;buy_px=执行日open(±0.001容差),执行收益=open→close;无价/落带外=闸门未落,收益null不进分母;空段(0==0)合法;封单比双值见每票『封单比』,门槛只用『成交』口径",
        汇总=dict(执行胜率=f"{win}/{n}",均收=avg,样本数=len(top),已结算=n,无执行价剔除数=len(top)-n),反思=refl)
    if dry:
        print(json.dumps(dict(汇总=payload["汇总"],正式荐票汇总=payload["正式荐票汇总"],
             正式荐票=[dict(代码=x["代码"],权重=x["权重"],执行收益=x["执行收益"],封单比=x["封单比"]) for x in (formal or [])]),
             ensure_ascii=False,indent=1))
        return payload
    # ① 双段主键 MA-20261021-03①: (荐票日,段)=  d|发版 / d|正式  同日两段互不覆盖; 旧记录无『段』→键(d,None)不受影响
    append_dedup(os.path.join(L,"_席位荐票反思.jsonl"), dict(
        荐票日=dprev,段="发版",执行胜率=f"{win}/{n}",均收=avg,立功=hero,打脸=flop,反思=refl),
        ("荐票日","段"))
    if formal is not None:
        append_dedup(os.path.join(L,"_席位荐票反思.jsonl"), dict(
            荐票日=dprev,段="正式",执行胜率=f"{fwin}/{fnum}",
            均收=(round(sum(x["执行收益"] for x in formal if x["执行收益"] is not None)/fnum,2) if fnum else None),
            无执行价剔除数=fdrop,
            标的=[dict(代码=x["代码"],权重=x["权重"],执行收益=x["执行收益"],封单比=x["封单比"]) for x in formal],
            反思=f"{dprev}正式荐票{fb}条/已结算{fnum}/无执行价剔除{fdrop}"),
            ("荐票日","段"))
    json.dump(payload,
        open(os.path.join(L,f"席位荐票结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    disp=dprev[4:6]+"-"+dprev[6:8]
    # ★原位重渲同一张荐票卡(合一结构,2026-07-10用户拍板"一种展示方式"):替换日块SEATCARD段
    import importlib.util as _il
    spec=_il.spec_from_file_location("seatrec",os.path.join(BASE,"席位荐票.py"))
    seatrec=_il.module_from_spec(spec); spec.loader.exec_module(seatrec)
    out_full=json.load(open(jp,encoding="utf-8"))
    smap={r["代码"]:dict(T1高开=r["T1高开"],执行收益=r["执行收益"],判定=r["判定"]) for r in res}
    newcard=seatrec.render_card(out_full,settle=smap)
    # Keep the standalone source card in lockstep with the archived body card.
    # lhb数据核对.py treats this file as the auditable Top5 source after T+1 settlement.
    with open(os.path.join(L, f"席位荐票卡_{dprev}.html"), "w", encoding="utf-8") as _card_fp:
        _card_fp.write(newcard)
    refl_blk=(f'<!--REFL--><div class="card" style="background:#faf7f0"><b>按席位归因反思</b> '
      f'<span class="mut">(执行胜率{win}/{n} · 均收{avg}% · 自动;事实表重算=净化)</span><br>{refl}</div><!--/REFL-->'
      if n else '')
    dp=os.path.join(L,"龙虎榜复盘存档",f"{dprev}.json")
    if os.path.isfile(dp):
        D=json.load(open(dp,encoding="utf-8")); h=D["html"]
        if '<!--SEATCARD-->' in h and '<!--/SEATCARD-->' in h:
            h=h[:h.find('<!--SEATCARD-->')]+newcard+h[h.find('<!--/SEATCARD-->')+len('<!--/SEATCARD-->'):]
        if '<!--REFL-->' in h:
            h=re.sub(r'<!--REFL-->.*?<!--/REFL-->',refl_blk,h,flags=re.S)
        else:
            h=h[:h.find('<!--/SEATCARD-->')+len('<!--/SEATCARD-->')]+refl_blk+h[h.find('<!--/SEATCARD-->')+len('<!--/SEATCARD-->'):] if '<!--/SEATCARD-->' in h else h+refl_blk
        D["html"]=h
        json.dump(D,open(dp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        subprocess.run([sys.executable,os.path.join(BASE,"龙虎榜台账.py")],check=True)
    print(f"{disp} 席位路结算: 胜率{win}/{n} 均收{avg}% | 卡已原位回填")
    print("反思:",refl)
if __name__=="__main__": main(sys.argv[1])
