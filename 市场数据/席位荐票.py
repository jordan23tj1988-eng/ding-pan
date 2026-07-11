# -*- coding: utf-8 -*-
"""席位荐票.py {d} —— 09龙虎榜agent第2路荐票v3:席位为主轴(2026-07-10用户拍板)。
候选池=当日S/A档席位(滚动执行口径胜率,_席位分档.json)净买≥1000万的标的;
打分=席位主分(档位S3/A2×净买强度,多S/A共买=共振自然加分)+涨停质量分辅助(权重小);
Top5→总agent。★席位胜率是席位历史滚动值,非个股预言;荐票=跟随S/A席位的T+1开盘执行口径。"""
import os,sys,json,glob,subprocess
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
MIN_BUY=1e7

def render_card(out,settle=None):
    """席位路Top5卡=荐票+T+1结算合一表(2026-07-10用户拍板:一种展示方式,不来回换)。
    settle=None→结算列显"待结算";结算脚本传入{代码:{T1高开,执行收益,判定}}原位重渲同一张卡。"""
    import html as H
    top=out["top5"]
    rows=[]
    for i,x in enumerate(top,1):
        seats="<br>".join(f'<b>[{s["档"]}]</b>{H.escape(s["名"][:14])}… <span class="mut">执1 {s["滚动执1"]}(n={s["样本"]}) 净买{s["净额万"]}万</span>' for s in x["席位"][:3])
        pc=f'{x["涨跌幅"]:+.1f}%' if x.get("涨跌幅") is not None else "—"
        st=(settle or {}).get(x["代码"])
        if st and st.get("执行收益") is not None:
            cls="dA" if st["执行收益"]>0 else "dC"
            stl=f'<span style="white-space:nowrap">开{st["T1高开"]:+.1f}%→收{st["执行收益"]:+.1f}%</span><br><b class="{cls}">{st["判定"]}</b>'
        else:
            stl='<span class="mut">—待结算</span>'
        rows.append(f'<tr><td>{i}</td>'
            f'<td style="white-space:nowrap"><b>{H.escape(str(x["名称"]))}</b><br><span class="mut">{x["代码"]} {pc}</span></td>'
            f'<td style="white-space:nowrap"><b>{x["综合分"]}</b><br><span class="mut">共振{x["共振"]}</span></td>'
            f'<td style="word-break:break-word">{seats}</td>'
            f'<td style="white-space:nowrap">结构<b>{x["资金结构分"] if x.get("资金结构分") is not None else "—"}</b><br><span class="mut">{("机构%d·量化%d·游资%d"%(x["风格构成"]["机构"],x["风格构成"]["量化"],x["风格构成"]["游资"])) if x.get("风格构成") else "—"}</span></td>'
            f'<td style="white-space:nowrap">{stl}</td></tr>')
    card=(f'<!--SEATCARD--><div class="card"><table style="table-layout:fixed;width:100%">'
     f'<colgroup><col style="width:24px"><col style="width:100px"><col style="width:60px"><col><col style="width:104px"><col style="width:118px"></colgroup>'
     f'<tr><th>#</th><th>标的</th><th>综合分·共振</th><th>S/A席位(档·滚动执1胜率·净买)</th><th>资金结构</th><th>T+1结算(开买→收)</th></tr>'
     +"".join(rows)+'</table></div>'
     f'<div class="hint">候选=当日S/A席位净买≥1000万({out["SA数"]}个S/A,候选{out["候选数"]}只);席位胜率=滚动执行口径历史值(窗口{out["分档窗口"]}),非个股预言;结构分仅辅助。结算列次日由结算脚本原位回填,同一张表不换结构。</div><!--/SEATCARD-->')
    return card
def main(d):
    gp=os.path.join(L,"_席位分档.json")
    lib=json.load(open(gp,encoding="utf-8"))["席位"]
    sa={s:v for s,v in lib.items() if v["档"] in ("S","A")}
    mp=os.path.join(L,"_席位动向",f"{d}.csv")
    if not os.path.isfile(mp): subprocess.run([sys.executable,os.path.join(BASE,"席位动向库.py"),"fetch",d],check=True)
    df=pd.read_csv(mp,dtype={"代码":str}); df["代码"]=df["代码"].str.zfill(6)
    df=df[~df["代码"].str.startswith(("11","12","90","20"))]  # 剔转债/B股(v3.1铁律;2026-07-10修:N豪26转曾混入Top5)
    df=df[(df["净额"]>0)&(df["买入金额"]>=MIN_BUY)].drop_duplicates(subset=["代码","席位"])
    hits=df[df["席位"].isin(sa)]
    # 涨跌幅(lhb.csv) + 题材/质量分辅助(涨停系产出,对齐唯一真源)
    pchg={}; lp=os.path.join(BASE,d,"lhb.csv")
    if os.path.isfile(lp):
        lh=pd.read_csv(lp,dtype={"代码":str}); lh["代码"]=lh["代码"].str.zfill(6)
        pchg=dict(zip(lh["代码"],lh["涨跌幅"]))
    theme={}
    qp=os.path.join(L,f"涨停质量荐票_{d}.json")
    if os.path.isfile(qp):
        for x in json.load(open(qp,encoding="utf-8"))["明细"]: theme[x["代码"]]=x.get("大方向")
    # 第三维=资金结构分(纯资金9因子库;旧12因子质量分已退出09号=职责边界,2026-07-10用户拍板)
    zp=os.path.join(L,f"资金结构分_{d}.json")
    if not os.path.isfile(zp):
        try: subprocess.run([sys.executable,os.path.join(BASE,"资金结构因子.py"),"score",d],check=True)
        except Exception: pass
    zj=json.load(open(zp,encoding="utf-8"))["分数"] if os.path.isfile(zp) else {}
    cand={}
    for _,r in hits.iterrows():
        c=r["代码"]; v=sa[r["席位"]]
        w=3 if v["档"]=="S" else 2
        strength=min(r["净额"]/5e7,2)
        e=cand.setdefault(c,dict(代码=c,名称=r["名称"],席位分=0,席位=[],共振=0))
        e["席位分"]+=w*strength
        _w=v.get("收缩执1胜率",v["执1胜率"]); _r=v.get("收缩执1均涨",v["执1均涨"])
        _flag="⚠小样本" if (v.get("小样本") or v["样本"]<25) else ""
        e["席位"].append(dict(名=r["席位"],档=v["档"],滚动执1=f'{_w}%/{_r}%{_flag}',样本=v["样本"],净额万=round(r["净额"]/1e4)))
        e["共振"]+=1
    for c,e in cand.items():
        e["席位分"]=round(e["席位分"],2)
        z=zj.get(c) or {}
        e["资金结构分"]=z.get("资金结构分"); e["风格构成"]=z.get("风格构成"); e["资金主导"]=z.get("主导")
        e["题材"]=theme.get(c)
        e["涨跌幅"]=round(float(pchg.get(c)),2) if c in pchg else None
        # 三维共打:①席位档(人)②强度共振(钱)已并入席位分 ③资金结构(构成),0-100→0-4分
        e["综合分"]=round(e["席位分"]+(e["资金结构分"] or 50)/100*4,2)
    top=sorted(cand.values(),key=lambda x:(-x["综合分"],-x["共振"]))[:5]
    out=dict(日=d,荐票源="09_龙虎榜(席位路v3:S/A席位动向)",分档窗口=json.load(open(gp,encoding="utf-8"))["窗口"],
        SA数=len(sa),候选数=len(cand),
        口径="候选=S/A席位当日净买≥1000万;席位胜率=收缩估计值(向全体基准收缩K=10,n<25标⚠小样本),滚动执行口径(T+1开买)历史值非个股预言;三维=席位档(人)×强度共振(钱)+资金结构分(构成,0-4分);旧12因子已出09号",
        top5=top)
    json.dump(out,open(os.path.join(L,f"席位荐票_{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    open(os.path.join(L,f"席位荐票卡_{d}.html"),"w",encoding="utf-8").write(render_card(out,settle=None))
    print(f"{d} 席位路Top5(S/A={out['SA数']},候选{out['候选数']}):")
    for i,x in enumerate(top,1):
        print(f'  {i} {x["名称"]} {x["代码"]} 综合{x["综合分"]} 共振{x["共振"]} 主席位[{x["席位"][0]["档"]}]{x["席位"][0]["名"][:16]} {x["席位"][0]["滚动执1"]}')
if __name__=="__main__":
    import datetime
    main(sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime("%Y%m%d"))
