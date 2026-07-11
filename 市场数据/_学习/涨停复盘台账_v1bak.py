# -*- coding: utf-8 -*-
"""涨停复盘台账.py {d} [--from-data] —— 每日涨停复盘按日累积台账(格式统一)。
每天日块=速览+三层归位表(含质量分·T1/T2预测)+待归位兜底;存 _学习/涨停复盘存档/{d}.json,
组装成台账(最新在上、当天展开、旧日折叠)注入最新judgment的limitup页<!--LEDGER-->段。
--from-data: 从 涨停对链条_{d}.json+主流题材6有_{d}.json+zt_pool现算日块(缺则自动跑脚本)。"""
import os,sys,re,json,glob,subprocess,html,importlib.util
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习"); STORE=os.path.join(L,"涨停复盘存档")
esc=html.escape
def ensure(d):
    for scr,out in [("涨停对链条.py",f"涨停对链条_{d}.json"),("主流题材6有.py",f"主流题材6有_{d}.json")]:
        if not os.path.isfile(os.path.join(L,out)):
            subprocess.run([sys.executable,os.path.join(BASE,scr),d],check=True)
def _qual():
    spec=importlib.util.spec_from_file_location("zlq",os.path.join(BASE,"涨停质量训练.py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    try: return m,m._lib()
    except Exception: return m,None
def load_mv(d):
    import pandas as pd
    df=pd.read_csv(os.path.join(BASE,d,"zt_pool.csv"),dtype={"代码":str}); df["代码"]=df["代码"].astype(str).str.zfill(6)
    mv={}
    for _,r in df.iterrows():
        v=pd.to_numeric(r.get("流通市值"),errors="coerce"); ind=str(r.get("所属行业",""))
        mv[r["代码"]]=(v/1e8 if v==v else None,ind)
    return mv
def vcls(v): return {'主线承载核心':'s-ok','分歧/末端':'s-weak','末端扩散':'s-mid'}.get(v.split(':')[0],'mut')
def qcell(g,mv,zl,lib):
    fdb=g.get("封单比"); c=g["代码"]
    if lib is None or fdb is None or c not in mv or mv[c][0] is None: return '<span class="mut">—</span>'
    q=zl.质量查表(fdb,g["首封"],g["连板"],mv[c][0],lib)
    if not q: return '<span class="mut">—</span>'
    e1=q.get("预测执1胜率"); e1r=q.get("预测执1均涨")
    disp=(f'执{e1}%/{e1r}%' if e1 is not None else f'信T1 {q["预测T1胜率"]}%')
    return f'<b>{q["质量分"]}</b> <span class="mut">{disp}</span>'
def srcbadge(s):
    return {'A':'<span class="badge bA">A</span>','C':'<span class="badge bC">C</span>'}.get(s,'<span class="mut" style="font-size:11px">B</span>') if s not in('模板','模板匹配') else '<span class="tag2 t-watch">模板</span>'
def row(g,mv,zl,lib,catalyst=None):
    fdb=f'{g["封单比"]}%' if g.get("封单比") is not None else '—'
    kb='<span class="tag2 t-avoid">开</span>' if g.get("开板次数",0)>0 else ''
    lb=f'<span class="tag2 t-attack">{g["连板"]}板</span>' if g["连板"]>1 else ''
    cat=catalyst if catalyst is not None else (esc(g.get("催化") or "(模板卡位)")+" "+srcbadge(g.get("来源档","")))
    return f'<tr><td>{esc(g["首封"])}</td><td><b>{esc(g["名称"])}</b> <span class="mut">{esc(g["代码"])}</span></td><td>封{fdb} {kb}{lb}</td><td>{cat}</td><td>{qcell(g,mv,zl,lib)}</td></tr>'
def day_table(zt,mv,zl,lib):
    r=['<div class="card"><table><tr><th>首封</th><th>标的</th><th>封单·身位</th><th>催化 · 来源档</th><th>质量分 · 执行预测(T+1开买→收)</th></tr>']
    for t in zt['题材线']:
        r.append(f'<tr style="background:#f3eee1"><td colspan="5"><b>【{esc(t["大方向"])}】</b>{t["家数"]}只 · 最高{t["最高连板"]}板 · 承载{esc(t.get("承载环节") or "-")}</td></tr>')
        for s in t['环节']:
            r.append(f'<tr><td colspan="5" style="background:#faf7f0"><b>── {esc(s["环节"])}</b> <span class="mut">({s["家数"]}只·开板{s["开板占比"]})</span> <span class="{vcls(s["快判"])}">{esc(s["快判"])}</span></td></tr>')
            for g in s['个股']: r.append(row(g,mv,zl,lib))
    dg=zt.get('待归位_行业兜底') or []
    if dg:
        r.append(f'<tr style="background:#f3eee1"><td colspan="5"><b>【待归位 · 行业兜底】</b>{len(dg)}只 <span class="mut">(agent当日补催化归位;行业只兜底不作题材)</span></td></tr>')
        for g in dg: r.append(row(g,mv,zl,lib,catalyst='<span class="mut">行业:'+esc(g.get("行业",""))+'</span>'))
    r.append('</table></div>')
    return ''.join(r)
def build_from_data(d):
    ensure(d)
    zt=json.load(open(os.path.join(L,f"涨停对链条_{d}.json"),encoding="utf-8"))
    six=json.load(open(os.path.join(L,f"主流题材6有_{d}.json"),encoding="utf-8"))
    mv=load_mv(d); zl,lib=_qual()
    cl=six.get("题材_聚类口径") or []; top=cl[0] if cl else None
    dg=len(zt.get('待归位_行业兜底') or [])
    summary=(f'涨停{zt["涨停总数"]} · '+(f'主流{esc(top["题材(题材聚类口径)"])}{top["得分"]}/6({top["涨停数"]})' if top and top["得分"]>=5 else '无主流·分支轮动')+(f' · 待归位{dg}' if dg else ''))
    speed=(f'<div class="strip"><div class="kv"><div class="l">涨停</div><div class="v">{zt["涨停总数"]}</div></div>'
           f'<div class="kv"><div class="l">题材线</div><div class="v">{zt["题材线数"]}</div></div>'
           f'<div class="kv"><div class="l">全场判定</div><div class="v" style="font-size:12.5px">{esc(six.get("全场判定",""))}</div></div></div>')
    inner=speed+day_table(zt,mv,zl,lib)
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
    J=json.load(open(jp,encoding="utf-8")); b=J["bodies"]["limitup"]
    b=b[:b.find('<!--LEDGER-->')+len('<!--LEDGER-->')]+section+b[b.find('<!--/LEDGER-->'):]
    J["bodies"]["limitup"]=b; json.dump(J,open(jp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    return os.path.basename(jp)
def main():
    a=sys.argv[1:]; d=next((x for x in a if x.isdigit()),None)
    if d and "--from-data" in a:
        s,inner=build_from_data(d); save(d,s,inner); print(f"{d}日块(统一格式)已存: {s}")
    jp=inject(assemble())
    print(f"台账组装注入 {jp} | 存档日数 {len(glob.glob(os.path.join(STORE,'20*.json')))}")
if __name__=="__main__": main()
