# -*- coding: utf-8 -*-
"""席位荐票结算.py {昨日d} —— 席位路Top5的T+1结算+按席位归因反思(09号进化闭环)。
执行口径=T+1开盘买入→T+1收。归因主体=席位(谁立功/谁打脸);打脸席位样本进事实表→每晚rank重算自动掉档=自我净化。
反思追加 _学习/_席位荐票反思.jsonl;结算+反思html注入台账{昨日}日块;自动重跑台账组装。"""
import os,sys,re,json,glob,subprocess
from collections import defaultdict
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
def exe_ret(c,dprev):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None,None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None,None
    i=idx[0]; o1=b.loc[i+1,'open']; c1=b.loc[i+1,'close']
    return round((o1/b.loc[i,'close']-1)*100,2),round((c1/o1-1)*100,2)
def main(dprev):
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
    open(os.path.join(L,"_席位荐票反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
        荐票日=dprev,执行胜率=f"{win}/{n}",均收=avg,立功=hero,打脸=flop,反思=refl),ensure_ascii=False)+"\n")
    json.dump(dict(荐票日=dprev,Top5=res,汇总=dict(执行胜率=f"{win}/{n}",均收=avg),反思=refl),
        open(os.path.join(L,f"席位荐票结算_{dprev}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    disp=dprev[4:6]+"-"+dprev[6:8]
    # ★原位重渲同一张荐票卡(合一结构,2026-07-10用户拍板"一种展示方式"):替换日块SEATCARD段
    import importlib.util as _il
    spec=_il.spec_from_file_location("seatrec",os.path.join(BASE,"席位荐票.py"))
    seatrec=_il.module_from_spec(spec); spec.loader.exec_module(seatrec)
    out_full=json.load(open(jp,encoding="utf-8"))
    smap={r["代码"]:dict(T1高开=r["T1高开"],执行收益=r["执行收益"],判定=r["判定"]) for r in res}
    newcard=seatrec.render_card(out_full,settle=smap)
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
