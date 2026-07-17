# -*- coding: utf-8 -*-
"""龙虎榜台账.py {d} [--from-data] —— lhb页唯一每日管道(2026-07-10链路统一,防脚本打架)。
★日块=一天完整档案:速览+席位路Top5荐票卡+今日S/A动向全表+全量上榜表(辅助分排序)+次日注入的结算反思。
★分工铁律:每日内容只进日块(本脚本);固定段(分档库/训练库/认知迭代)不归本脚本管;结算由席位荐票结算.py注入昨日日块。
日块=速览+当日席位质量Top5荐票卡+强档真金表(全量上榜按质量分排)+T+1结算对账(次日由结算脚本注入),
存 _学习/龙虎榜复盘存档/{d}.json;组装(最新在上、当天展开)注入最新judgment的lhb页<!--LHBLEDGER-->段。
分数唯一源=龙虎榜质量荐票_{d}.json(缺则自动补跑),与荐票同源杜绝一页两口径。"""
import os,sys,json,glob,subprocess,html
BASE=os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(BASE,'_学习')):
    g=glob.glob('/sessions/*/mnt/股票数据/市场数据')
    if g: BASE=g[0]
L=os.path.join(BASE,"_学习"); STORE=os.path.join(L,"龙虎榜复盘存档")
esc=html.escape
def _qmap(d):
    p=os.path.join(L,f"龙虎榜质量荐票_{d}.json")
    if not os.path.isfile(p):
        try: subprocess.run([sys.executable,os.path.join(BASE,"龙虎榜质量荐票.py"),d],check=True)
        except Exception: pass
    if not os.path.isfile(p): return {},None
    j=json.load(open(p,encoding="utf-8"))
    return {x["代码"]:x for x in j.get("明细",[])},j

def _seat_table(d):
    """今日S/A席位动向全表(S优先),进日块"""
    try:
        import pandas as pd
        lib=json.load(open(os.path.join(L,'_席位分档.json'),encoding='utf-8'))
        sa={s:v for s,v in lib['席位'].items() if v['档'] in 'SA'}
        mv=pd.read_csv(os.path.join(L,'_席位动向',f'{d}.csv'),dtype={'代码':str}); mv['代码']=mv['代码'].str.zfill(6)
        mv=mv[(mv['净额']>0)&(mv['买入金额']>=1e7)].drop_duplicates(subset=['代码','席位'])
        hits=mv[mv['席位'].isin(sa)].copy()
        if not len(hits): return '<div class="hint">今日无S/A席位出手(净买≥1000万)</div>'
        hits['档']=hits['席位'].map(lambda s:sa[s]['档']); hits['序']=hits['档'].map({'S':0,'A':1})
        hits=hits.sort_values(['序','净额'],ascending=[True,False])
        rows=[]
        for _,r in hits.iterrows():
            v=sa[r['席位']]
            rows.append(f'<tr><td style="white-space:nowrap"><b class="{"s-ok" if r["档"]=="S" else "s-mid"}">[{r["档"]}]</b> {esc(r["席位"][:22])}…<br>'
              f'<span class="mut">滚动执1 {v["执1胜率"]}%/{v["执1均涨"]}% · n={v["样本"]} · {v["通道"]}</span></td>'
              f'<td style="white-space:nowrap"><b>{esc(str(r["名称"]))}</b><br><span class="mut">{r["代码"]}</span></td>'
              f'<td style="white-space:nowrap">净买<b>{r["净额"]/1e8:.2f}亿</b><br><span class="mut">买{r["买入金额"]/1e8:.2f}亿</span></td></tr>')
        return (f'<p style="font-weight:700;margin:14px 0 4px;border-left:3px solid var(--accent);padding-left:8px">今日S/A席位动向全表(出手{len(hits)}笔)</p>'
          '<div class="card"><table style="table-layout:fixed;width:100%"><colgroup><col><col style="width:110px"><col style="width:96px"></colgroup>'
          '<tr><th>S/A席位(滚动战绩)</th><th>买入标的</th><th>金额</th></tr>'+''.join(rows)+'</table></div>')
    except Exception as e:
        return f'<div class="hint">动向表生成失败:{esc(str(e)[:60])}(标null不编)</div>'
def build_from_data(d):
    import pandas as pd
    mp=os.path.join(L,'_席位动向',f'{d}.csv')
    if not os.path.isfile(mp):
        try: subprocess.run([sys.executable,os.path.join(BASE,'席位动向库.py'),'fetch',d],check=True)
        except Exception: pass
    n=jg=sa_n=0
    if os.path.isfile(mp):
        mv=pd.read_csv(mp,dtype={'代码':str})
        n=mv['代码'].nunique()
        jg=mv[mv['席位'].astype(str).str.contains('机构专用')]['代码'].nunique()
        try:
            lib=json.load(open(os.path.join(L,'_席位分档.json'),encoding='utf-8'))['席位']
            sa=[s for s,v in lib.items() if v['档'] in 'SA']
            sa_n=len(mv[(mv['席位'].isin(sa))&(mv['净额']>0)&(mv['买入金额']>=1e7)].drop_duplicates(subset=['代码','席位']))
        except Exception: pass
    summary=f'上榜{n} · 机构在场{jg}只 · S/A出手{sa_n}笔'
    speed=(f'<div class="strip"><div class="kv"><div class="l">上榜(买侧明细)</div><div class="v">{n}</div></div>'
      f'<div class="kv"><div class="l">机构在场</div><div class="v">{jg}</div></div>'
      f'<div class="kv"><div class="l">S/A出手</div><div class="v">{sa_n}笔</div></div></div>')
    cardp=os.path.join(L,f"席位荐票卡_{d}.html")
    if not os.path.isfile(cardp):
        try: subprocess.run([sys.executable,os.path.join(BASE,"席位荐票.py"),d],check=True)
        except Exception: pass
    card=('<p style="font-weight:700;margin:8px 0 4px;border-left:3px solid var(--accent);padding-left:8px">当日席位路Top5荐票(S/A席位动向v3·第2路)</p>'+open(cardp,encoding="utf-8").read()) if os.path.isfile(cardp) else ""
    seat_tbl=_seat_table(d)
    inner=speed+card+seat_tbl
    return summary,inner
def save(d,summary,inner):
    os.makedirs(STORE,exist_ok=True)
    json.dump({"date":d,"summary":summary,"html":inner},open(os.path.join(STORE,f"{d}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
def assemble():
    fs=sorted(glob.glob(os.path.join(STORE,"20*.json")),reverse=True)
    parts=[]
    for i,f in enumerate(fs):
        j=json.load(open(f,encoding="utf-8")); d=j["date"]; disp=d[4:6]+"-"+d[6:8]
        op=" open" if i==0 else ""
        chip='<span class="chip cold">最新</span>' if i==0 else '<span class="chip">存档</span>'
        parts.append(f'<details class="chain"{op}><summary><b>{disp}</b> {chip} {esc(j["summary"])}</summary><div class="inner">{j["html"]}</div></details>')
    return "".join(parts) or '<div class="hint">暂无存档日</div>'
def inject(section):
    js=sorted(glob.glob(os.path.join(L,"judgment_*.json"))); jp=js[-1]
    J=json.load(open(jp,encoding="utf-8")); b=J["bodies"].get("lhb","")
    if '<!--LHBLEDGER-->' not in b:
        print("⚠ lhb页无LHBLEDGER锚,未注入(先重构lhb页)"); return None
    b=b[:b.find('<!--LHBLEDGER-->')+len('<!--LHBLEDGER-->')]+section+b[b.find('<!--/LHBLEDGER-->'):]
    J["bodies"]["lhb"]=b; json.dump(J,open(jp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    return os.path.basename(jp)
def main():
    a=sys.argv[1:]; d=next((x for x in a if x.isdigit()),None)
    if "--from-data" in a and not d:
        print("!!! 龙虎榜台账.py --from-data 缺日期参数(YYYYMMDD),拒绝静默跳过当日日块(2026-07-16事故)。用法: python3 龙虎榜台账.py 20260716 --from-data"); sys.exit(2)
    if d and "--from-data" in a:
        s,inner=build_from_data(d); save(d,s,inner); print(f"{d} lhb日块已存: {s}")
    jp=inject(assemble())
    if jp: print(f"lhb台账注入 {jp} | 存档日数 {len(glob.glob(os.path.join(STORE,'20*.json')))}")
if __name__=="__main__": main()
