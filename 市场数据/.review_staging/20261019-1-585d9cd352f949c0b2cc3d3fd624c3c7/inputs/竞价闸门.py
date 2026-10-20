# -*- coding: utf-8 -*-
"""竞价闸门.py {昨日池日d} —— 早盘9:25-9:31跑(08号优化②):昨日评分池 × 今晨实开 → 今日可吃名单。
★规则(一年分桶库,13个月零翻车): 高开≥5% → ✗闸门放弃(历史-1.74%/胜率21.5%);
  已封板(现价触及涨停) → ⊘追不进只观察; 其余 → ✓可吃候选(按竞价分排序,标该信号×高开档历史预期)。
★零后视镜:池=昨日冻结发出版;分=昨晚竞价评分_{d}.json;今晨开盘价=9:25后执行时点已知,100%因果。
★诚实边界:可吃≠荐票;闸门内半池一年+0.36%/50.4%,是环境统计非个股预言;不给买卖指令。
产出: _学习/竞价闸门_{执行日}.json + 竞价闸门卡_{执行日}.html。2026-08-16起不再注入judgment auction(竞价路改六段,盘中竞价强势归盘中作战页)。
用法: python3 竞价闸门.py {昨日d}            (live,9:25后跑,sina实时)
      python3 竞价闸门.py {昨日d} --backtest  (历史演示,用bars次日开盘,不注入)"""
import os,sys,re,json,glob,datetime,urllib.request
import pandas as pd
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")

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
            out[mm.group(1)]=dict(今开=float(p[1]),昨收=float(p[2]),现价=float(p[3]))
    return out
def lim(c): return 19.9 if c[:2] in("30","68") else 9.9

def load_scored(dprev):
    fp=os.path.join(L,f"竞价评分_{dprev}.json")
    if os.path.isfile(fp):
        j=json.load(open(fp,encoding="utf-8")); return j["明细"],True
    fp2=os.path.join(L,f"竞价池发出_{dprev}.json")
    pool=json.load(open(fp2,encoding="utf-8"))["池"]
    for p in pool: p["竞价分"]=None; p["情景"]={}
    return pool,False

def bt_open(c,dprev):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    idx=b.index[b['date']==dprev]
    if not len(idx) or idx[0]+1>=len(b): return None
    i=idx[0]
    return dict(今开=float(b.loc[i+1,'open']),昨收=float(b.loc[i,'close']),现价=float(b.loc[i+1,'open']),执行日=str(b.loc[i+1,'date']))

def main(dprev,backtest=False):
    pool,scored=load_scored(dprev)
    rows=[]; ed=None
    for t in pool:
        c=str(t["代码"]).zfill(6)
        q=bt_open(c,dprev) if backtest else None
        if not backtest:
            q=sina([c]).get(c) if False else None  # 单票不发,统一批量在下面
        rows.append((t,c,q))
    if not backtest:
        qs=sina([c for _,c,_ in rows])
        rows=[(t,c,qs.get(c)) for t,c,_ in rows]
        ed=datetime.date.today().strftime("%Y%m%d")
    else:
        for _,c,q in rows:
            if q: ed=q["执行日"]; break
    res=[]
    for t,c,q in rows:
        if not q:
            res.append(dict(t,高开=None,判定="—未取到",cls="dB")); continue
        gk=round((q["今开"]/q["昨收"]-1)*100,2)
        sealed=(q["现价"]/q["昨收"]-1)*100>=lim(c)-0.1
        sc3=t.get("情景") or {}
        exp=(sc3.get("低开") if gk<=0 else (sc3.get("高开0~5") if gk<5 else sc3.get("高开≥5"))) or {}
        if gk>=5: v,cl="✗闸门·放弃(高开≥5)","dC"
        elif sealed and not backtest: v,cl="⊘已封板·追不进只观察","dB"
        else: v,cl="✓可吃候选","dA"
        res.append(dict(t,高开=gk,判定=v,cls=cl,档内历史=({"均涨":exp.get("均涨"),"胜率":exp.get("胜率")} if exp else None)))
    res.sort(key=lambda r:(-(r["竞价分"] or 0)))
    eat=[r for r in res if r["判定"].startswith("✓")]
    ban=[r for r in res if r["判定"].startswith("✗")]
    out=dict(池日=dprev,执行日=ed,模式=("backtest演示" if backtest else "live"),评分在场=scored,
        可吃=len(eat),放弃=len(ban),
        口径="闸门=一年分桶库'高开≥5%必弃'(13个月零翻车);可吃≠荐票,是执行过滤;9:25实开已知=100%因果",
        明细=[{k:v for k,v in r.items() if k not in("cls","情景","主导因子","闸门预标")} for r in res])
    ep=os.path.join(L,f"竞价闸门_{ed}.json")
    json.dump(out,open(ep,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # ---- 卡 ----
    dp=dprev[4:6]+"-"+dprev[6:8]; de=(ed or "")[4:6]+"-"+(ed or "")[6:8]
    trs=""
    for r in res:
        h=r.get("档内历史")
        hist=f'{h["均涨"]:+.1f}/{h["胜率"]:.0f}%' if (h and h.get("均涨") is not None) else "—"
        gk="—" if r["高开"] is None else f'{r["高开"]:+.1f}%'
        fdb=f'{r["封单比"]}%' if r.get("封单比") is not None else "—"
        trs+=(f'<tr><td><b>{r["名称"]}</b><br><span class="mut">{r["代码"]}</span></td>'
          f'<td>{r["信号"]}<br><span class="mut">封{fdb}</span></td>'
          f'<td style="white-space:nowrap">{r["竞价分"] if r["竞价分"] is not None else "—"}</td>'
          f'<td style="white-space:nowrap">{gk}</td><td style="white-space:nowrap">{hist}</td>'
          f'<td class="{r["cls"]}">{r["判定"]}</td></tr>')
    tag=f'(backtest演示·执行日{de})' if backtest else f'({de} 9:25实开)'
    card=(f'<div class="card"><b>可吃{len(eat)} · 放弃{len(ban)} · 共{len(res)} {tag}</b> '
      f'<span class="mut">规则:高开≥5%必弃(一年-1.74%/21.5%,13个月零翻车);可吃≠荐票,档内历史=该信号×高开档一年执行均涨%/胜率</span>'
      f'<table style="table-layout:fixed"><colgroup><col style="width:17%"><col style="width:17%"><col style="width:10%">'
      f'<col style="width:12%"><col style="width:14%"><col style="width:30%"></colgroup>'
      f'<tr><th>标的</th><th>昨日信号</th><th>竞价分</th><th>今晨高开</th><th>档内历史</th><th>闸门判定</th></tr>{trs}</table></div>')
    cp=os.path.join(L,f"竞价闸门卡_{ed}.html")
    open(cp,"w",encoding="utf-8").write(card)
    print(f"{dp}池闸门({out['模式']}): 可吃{len(eat)} 放弃{len(ban)} 未取到{sum(1 for r in res if r['高开'] is None)} → {ep}")
    for r in res: print(f'  {r["判定"]:14} {r["名称"]}({r["代码"]}) 分{r["竞价分"]} 高开{r["高开"]}')
    # 2026-08-16 起不再注入 judgment auction: 竞价路改六段, 盘中竞价强势(闸门)移出竞价页→盘中作战页
    #   独立产出(竞价闸门_{ed}.json + 竞价闸门卡_{ed}.html)保留存档, 供盘中作战页/复盘引用。
if __name__=="__main__":
    main(sys.argv[1],backtest="--backtest" in sys.argv)
