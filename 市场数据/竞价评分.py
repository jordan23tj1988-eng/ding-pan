# -*- coding: utf-8 -*-
"""竞价评分.py {d} —— 竞价路评分体系(2026-07-12建,08号优化③+评分卡)。
★傍晚18:00跑:冻结当日竞价池(与竞价池结算.py同口径)→查 _竞价池分桶库.json 打【竞价分0-100】
  =各维度桶值(0.6×执1胜率+0.4×执1均涨映射)按区分度加权;维度=信号/连板/炸板/封单比/温度/信号x连板。
★同时给每票"明晨三情景预测"(信号x高开档桶查表)+闸门预标(高开≥5%→放弃)。
★产出三件:竞价评分_{d}.json(分数唯一源) + 竞价评分卡_{d}.html(嵌auction段一)
  + 竞价评分库卡_{d}.html(训练库折叠:权重/分桶表/WF战绩,嵌auction段四,照limitup训练库做法)。
★诚实边界:竞价分=历史桶加权,非个股预言;池原样追开盘非alpha(-0.31pp),分数用途=池内排序+配合9:25闸门,
  不是买入指令。
用法: python3 竞价评分.py {d}"""
import os,sys,json
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")

# ---------- 池构建(逐条复刻 竞价池结算.py) ----------
def _junk(name):
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
        _zha=pd.to_numeric(r.get("炸板次数",0),errors="coerce")
        zha=int(_zha) if _zha==_zha else 0
        sig=("一字" if fb<="09:25" else "秒板")+(f"·{lb}板" if lb>1 else "·首板")
        pool.append(dict(代码=r["代码"],名称=str(r["名称"]),首封=fb,连板=lb,信号=sig,封单比=fdb,炸板=zha,
                         行业=str(r.get("所属行业",""))))
    return sorted(pool,key=lambda x:x["首封"])
def freeze_pool(d):
    fp=os.path.join(L,f"竞价池发出_{d}.json")
    if os.path.isfile(fp): return json.load(open(fp,encoding="utf-8"))["池"]
    pool=build_pool(d)
    json.dump(dict(池日=d,口径="零后视镜确定性池:zt_pool首封≤09:31;一字=首封≤09:25;发出版不可覆盖",池=pool),
              open(fp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    return pool

# ---------- 桶定义(与 竞价池分桶回填.py 一致) ----------
def lb_bucket(l): return "首板" if l==1 else ("2板" if l==2 else "3板+")
def fd_bucket(f): return None if f is None else ("<0.5%" if f<0.5 else ("0.5~1.5%" if f<1.5 else ("1.5~4%" if f<4 else "≥4%")))
def wd_bucket(w): return None if w is None else ("冷<40" if w<40 else ("中40~65" if w<65 else "热≥65"))
def zh_bucket(z): return "未炸" if z==0 else "炸1+"

# ---------- 评分卡 ----------
def _v(b):
    """桶值0-100:0.6×执行胜率 + 0.4×执行均涨映射([-3,+3]%→[0,100])"""
    if not b: return None
    r=max(-3.0,min(3.0,b["执行均涨"]))
    return 0.6*b["执行胜率"]+0.4*(r/3.0*50+50)
def build_scorecard(lib):
    """从分桶库构建评分卡:每维度{桶:值}+权重(∝执行均涨区分度)。返回(sc,v0,基准)"""
    base=lib["基准"]["池整体"]; v0=_v(base)
    dims={"信号":lib["一维"]["按信号"],"连板":lib["一维"]["按连板"],"炸板":lib["一维"]["按炸板"],
          "封单比":lib["一维"]["按封单比"],"温度":lib["一维"]["按温度"],"信号x连板":lib["交叉"]["信号x连板"]}
    sc={}
    for name,bk in dims.items():
        vals={k:_v(v) for k,v in bk.items() if v and v.get("n",0)>=10}
        rets=[v["执行均涨"] for v in bk.values() if v and v.get("n",0)>=10]
        spread=(max(rets)-min(rets)) if len(rets)>=2 else 0.0
        sc[name]=dict(桶值=vals,区分度=round(spread,2),
                      桶均涨={k:v["执行均涨"] for k,v in bk.items() if v},桶n={k:v.get("n") for k,v in bk.items() if v})
    tot=sum(s["区分度"] for s in sc.values()) or 1.0
    for s in sc.values(): s["权重"]=round(s["区分度"]/tot,3)
    return sc,v0,base
def stock_keys(t,wd):
    return {"信号":t["信号"].split("·")[0],"连板":lb_bucket(t["连板"]),"炸板":zh_bucket(t.get("炸板",0)),
            "封单比":fd_bucket(t.get("封单比")),"温度":wd_bucket(wd),
            "信号x连板":f'{t["信号"].split("·")[0]}|{lb_bucket(t["连板"])}'}
def score_stock(t,wd,sc,v0):
    """返回(竞价分,主导因子列表[(维,桶,贡献,桶均涨,n)])"""
    total=0.0; contrib=[]
    for dim,s in sc.items():
        k=stock_keys(t,wd)[dim]; v=s["桶值"].get(k)
        vv=v if v is not None else v0
        total+=s["权重"]*vv
        if v is not None:
            c=s["权重"]*(v-v0)
            contrib.append((dim,k,round(c,2),s["桶均涨"].get(k),s["桶n"].get(k)))
    contrib.sort(key=lambda x:-abs(x[2]))
    return round(total,1),contrib
def scenarios(t,lib):
    """明晨三情景(信号x高开档查表)+闸门预标"""
    sig=t["信号"].split("·")[0]; x=lib["交叉"]["信号x高开档"]; out={}
    for g,tag in (("低开≤0","低开"),("高开0~5","高开0~5"),("高开≥5","高开≥5")):
        b=x.get(f"{sig}|{g}")
        out[tag]=dict(均涨=b["执行均涨"],胜率=b["执行胜率"],n=b["n"]) if b else None
    return out

def lib_card(d,lib,sc,v0):
    """竞价评分训练库卡(照limitup训练库做法,details折叠):维度权重/区分度 + 各维度分桶胜率表 + 闸门依据 + WF战绩。
    产出 _学习/竞价评分库卡_{d}.html,嵌auction页段四。"""
    wt="".join(f'<tr><td>{k}</td><td>{s["权重"]}</td><td>{s["区分度"]}pp</td></tr>'
               for k,s in sorted(sc.items(),key=lambda x:-x[1]["权重"]))
    dim_src={"信号":lib["一维"]["按信号"],"连板":lib["一维"]["按连板"],"炸板":lib["一维"]["按炸板"],
             "封单比":lib["一维"]["按封单比"],"温度":lib["一维"]["按温度"],"信号x连板":lib["交叉"]["信号x连板"]}
    dims=""
    for name,bk in dim_src.items():
        rs="".join(f'<tr><td>{k}</td><td>{v["n"]}{"⚠" if v.get("注") else ""}</td><td>{v["执行胜率"]}%</td>'
                   f'<td class="{"dA" if v["执行均涨"]>0 else "dC"}">{v["执行均涨"]:+.2f}%</td><td>{v["次日封板率"]}%</td></tr>'
                   for k,v in sorted(bk.items(),key=lambda x:-x[1]["执行均涨"]))
        dims+=(f'<p style="margin:10px 0 0"><b>{name}</b> <span class="mut">权重{sc[name]["权重"]} · 区分度{sc[name]["区分度"]}pp</span></p>'
          f'<table><tr><th>桶</th><th>n</th><th>执1胜率</th><th>执1均涨</th><th>次日封板率</th></tr>{rs}</table>')
    gkb=lib["一维"]["按高开档"]
    gkr="".join(f'<tr><td>{k}</td><td>{v["n"]}</td><td>{v["执行胜率"]}%</td>'
                f'<td class="{"dA" if v["执行均涨"]>0 else "dC"}">{v["执行均涨"]:+.2f}%</td><td>{v["次日封板率"]}%</td></tr>'
                for k,v in gkb.items())
    wf_html=""
    wp=os.path.join(L,"_竞价评分WF.json")
    if os.path.isfile(wp):
        wf=json.load(open(wp,encoding="utf-8"))
        mrows="".join(f'<tr><td>{r["月"]}</td><td>{r["n"]}</td><td class="{"dA" if (r["RankIC"] or 0)>0 else "dC"}">{r["RankIC"]}</td>'
                      f'<td class="{"dA" if r["价差pp"]>0 else "dC"}">{r["价差pp"]:+.2f}</td></tr>' for r in wf["月度"])
        ter="".join(f'<tr><td>{t["组"]}</td><td>{t["n"]}</td><td>{t["胜率"]}%</td>'
                    f'<td class="{"dA" if t["执行均涨"]>0 else "dC"}">{t["执行均涨"]:+.2f}%</td></tr>' for t in wf["全期三分位"])
        wf_html=(f'<p style="margin:12px 0 0"><b>WF走查战绩(零后视镜:每月只用之前样本建库打分)</b> '
          f'<span class="mut">IC均值{wf["IC均值"]}(为正月{wf["IC为正月占比"]}%) · 三分位价差均值{wf["价差均值pp"]:+.2f}pp/月</span></p>'
          f'<table><tr><th>月</th><th>n</th><th>RankIC</th><th>三分位价差pp</th></tr>{mrows}</table>'
          f'<p style="margin:10px 0 0"><b>全期三分位(拼所有WF月)</b></p>'
          f'<table><tr><th>组</th><th>n</th><th>执1胜率</th><th>执1均涨</th></tr>{ter}</table>')
    body=(f'<details class="chain"><summary><b>竞价评分训练库</b> <span class="chip">一年分桶库 n={lib["样本"]}</span> '
      f'<span class="mut">{lib["窗口"]} · bars覆盖{lib["bars覆盖率pct"]}% · 每晚滚动重建</span></summary><div class="inner">'
      f'<div class="hint">竞价分=Σ维度权重×桶值;桶值=0.6×执1胜率+0.4×执1均涨映射;权重∝区分度(每晚自适应);n&lt;10桶取池基准中性(基准值{round(v0,1)})。'
      f'★桶均值非个股预言;池原样追开盘非alpha(-0.31pp);评分=池内排序器+环境仪表,非荐票器。执行口径=T+1开→T+1收,未含滑点费用,含幸存者偏差。</div>'
      f'<p><b>维度权重榜</b></p><table><tr><th>维度</th><th>权重</th><th>区分度(桶间执1均涨极差)</th></tr>{wt}</table>'
      f'{dims}'
      f'<p style="margin:10px 0 0"><b>高开档(闸门依据,执行时点过滤,不进评分)</b> <span class="mut">高开≥5%必弃,13个月零翻车</span></p>'
      f'<table><tr><th>档</th><th>n</th><th>执1胜率</th><th>执1均涨</th><th>次日封板率</th></tr>{gkr}</table>'
      f'{wf_html}</div></details>')
    open(os.path.join(L,f"竞价评分库卡_{d}.html"),"w",encoding="utf-8").write(body)

def main(d):
    lib=json.load(open(os.path.join(L,"_竞价池分桶库.json"),encoding="utf-8"))
    wdt=json.load(open(os.path.join(L,"_市场温度表.json"),encoding="utf-8"))
    wd=(wdt.get(d) or {}).get("温度")
    pool=freeze_pool(d)
    sc,v0,base=build_scorecard(lib)
    rows=[]
    for t in pool:
        score,contrib=score_stock(t,wd,sc,v0)
        rows.append(dict(t,竞价分=score,
            主导因子=[f'{dim}={k}({c:+.1f},桶均涨{r}%,n={n})' for dim,k,c,r,n in contrib[:3]],
            情景=scenarios(t,lib),闸门预标="若明晨高开≥5%→放弃(一年桶-1.74%/21.5%)"))
    rows.sort(key=lambda x:-x["竞价分"])
    out=dict(日=d,温度=wd,温度档=wd_bucket(wd),权重={k:v["权重"] for k,v in sc.items()},池基准值=round(v0,1),
        口径=("竞价分=分桶库桶值(0.6×执1胜率+0.4×执1均涨映射)按区分度加权,0-100;维度=信号/连板/炸板/封单比/温度/信号x连板;"
             "n<10桶取池基准中性;★桶均值非个股预言;池原样追开盘非alpha(-0.31pp),分数用途=池内排序+9:25闸门,不是买入指令;"
             f"库窗口={lib['窗口']},n={lib['样本']}"),
        明细=rows)
    fp=os.path.join(L,f"竞价评分_{d}.json")
    json.dump(out,open(fp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # ---- 卡html(排版铁律:fixed+两行标的) ----
    disp=d[4:6]+"-"+d[6:8]
    trs=""
    for r in rows:
        sc3=r["情景"]
        def cell(k):
            s=sc3.get(k)
            return f'{s["均涨"]:+.1f}/{s["胜率"]:.0f}%' if s else "—"
        fdb=f'{r["封单比"]}%' if r["封单比"] is not None else "—"
        lead=r["主导因子"][0].split("(")[0] if r["主导因子"] else "—"
        trs+=(f'<tr><td><b>{r["名称"]}</b><br><span class="mut">{r["代码"]}</span></td>'
          f'<td>{r["信号"]}{("·炸"+str(r["炸板"])) if r.get("炸板") else ""}<br><span class="mut">封{fdb}</span></td>'
          f'<td style="white-space:nowrap"><b>{r["竞价分"]}</b></td><td>{lead}</td>'
          f'<td style="white-space:nowrap">{cell("低开")}</td><td style="white-space:nowrap">{cell("高开0~5")}</td>'
          f'<td style="white-space:nowrap" class="dC">{cell("高开≥5")}弃</td></tr>')
    card=(f'<div class="card"><b>{disp}竞价池评分({len(rows)}只,温度{wd}·{wd_bucket(wd) or "null"})</b> '
      f'<span class="mut">分=一年分桶库加权(桶均值非个股预言);明晨按9:25实开走闸门:高开≥5%整体-1.74%历史必弃;情景=均涨%/胜率</span>'
      f'<table style="table-layout:fixed"><colgroup><col style="width:15%"><col style="width:17%"><col style="width:9%">'
      f'<col style="width:20%"><col style="width:13%"><col style="width:13%"><col style="width:13%"></colgroup>'
      f'<tr><th>标的</th><th>信号</th><th>竞价分</th><th>主导因子</th><th>若低开</th><th>若高开0~5</th><th>若高开≥5</th></tr>{trs}</table>'
      f'<p class="mut" style="margin-top:8px">情景列=该信号×高开档一年执行均涨/胜率(T+1开→收);池原样非alpha,闸门内(高开&lt;5%)半池一年+0.36%/50.4%。</p></div>')
    open(os.path.join(L,f"竞价评分卡_{d}.html"),"w",encoding="utf-8").write(card)
    lib_card(d,lib,sc,v0)
    print(f"{d} 竞价评分: {len(rows)}只 → {fp}")
    print("权重:",out["权重"])
    for r in rows[:12]:
        print(f'  {r["竞价分"]:5.1f} {r["名称"]}({r["代码"]}) {r["信号"]} 封{r["封单比"]} | {r["主导因子"][0] if r["主导因子"] else ""}')
if __name__=="__main__":
    main(sys.argv[1])
