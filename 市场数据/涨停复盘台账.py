# -*- coding: utf-8 -*-
"""涨停复盘台账.py {d} [--from-data] —— 每日涨停复盘按日累积台账(格式统一)。
每天日块=速览+三层归位表(含质量分·执行预测)+待归位兜底;存 _学习/涨停复盘存档/{d}.json,
组装成台账(最新在上、当天展开、旧日折叠)注入最新judgment的limitup页<!--LEDGER-->段。
--from-data: 从 涨停对链条_{d}.json+主流题材6有_{d}.json 现算日块(缺则自动跑脚本)。
v3标签口径(2026-07-11): 抓龙率+命中规则+质量分v5(负筛)。v2(2026-07-10): 分数唯一源=涨停质量荐票_{d}.json(缺则自动补跑)——与荐票同源,
口径永远一致,杜绝台账/荐票两套分数(v2.4教训:只换Top5不换台账=一页两种口径)。"""
import os,sys,re,json,glob,subprocess,html
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习"); STORE=os.path.join(L,"涨停复盘存档")
esc=html.escape
def ensure(d):
    for scr,out in [("涨停对链条.py",f"涨停对链条_{d}.json"),("主流题材6有.py",f"主流题材6有_{d}.json")]:
        if not os.path.isfile(os.path.join(L,out)):
            subprocess.run([sys.executable,os.path.join(BASE,scr),d],check=True)
def _qmap(d):
    """代码→v5打标记录(抓龙率/命中数/质量分/预测执1)。唯一分数源=涨停质量荐票_{d}.json,缺则自动补跑。"""
    p=os.path.join(L,f"涨停质量荐票_{d}.json")
    if not os.path.isfile(p):
        try: subprocess.run([sys.executable,os.path.join(BASE,"涨停质量荐票.py"),d],check=True)
        except Exception: pass
    if not os.path.isfile(p): return {}
    try:
        j=json.load(open(p,encoding="utf-8"))
        return {x["代码"]:x for x in j.get("明细",[])}
    except Exception: return {}
def vcls(v): return {'主线承载核心':'s-ok','分歧/末端':'s-weak','末端扩散':'s-mid'}.get(v.split(':')[0],'mut')
def qcell(g,qmap):
    q=qmap.get(g["代码"])
    if not q or q.get("质量分") is None: return '<span class="mut">—</span>'
    hit=f' <span class="tag2 t-attack">中{q["命中数"]}规</span>' if q.get("命中数") else ''
    zl=q.get("抓龙率")
    return f'<b>抓{zl if zl is not None else "—"}%</b>{hit} <span class="mut">分{q["质量分"]} 执1 {q.get("预测执1胜率","—")}%/{q.get("预测执1均涨","—")}%</span>'
def srcbadge(s):
    return {'A':'<span class="badge bA">A</span>','C':'<span class="badge bC">C</span>'}.get(s,'<span class="mut" style="font-size:11px">B</span>') if s not in('模板','模板匹配') else '<span class="tag2 t-watch">模板</span>'
def row(g,qmap,catalyst=None):
    fdb=f'{g["封单比"]}%' if g.get("封单比") is not None else '—'
    kb='<span class="tag2 t-avoid">开</span>' if g.get("开板次数",0)>0 else ''
    lb=f'<span class="tag2 t-attack">{g["连板"]}板</span>' if g["连板"]>1 else ''
    cat=catalyst if catalyst is not None else (esc(g.get("催化") or "(模板卡位)")+" "+srcbadge(g.get("来源档","")))
    return f'<tr><td>{esc(g["首封"])}</td><td><b>{esc(g["名称"])}</b> <span class="mut">{esc(g["代码"])}</span></td><td>封{fdb} {kb}{lb}</td><td>{cat}</td><td>{qcell(g,qmap)}</td></tr>'
def day_table(zt,qmap):
    r=['<div class="card"><table><tr><th>首封</th><th>标的</th><th>封单·身位</th><th>催化 · 来源档</th><th>抓龙率·命中规则·质量分v5 · 执行预测(T+1开买→收)</th></tr>']
    for t in zt['题材线']:
        r.append(f'<tr style="background:#f3eee1"><td colspan="5"><b>【{esc(t["大方向"])}】</b>{t["家数"]}只 · 最高{t["最高连板"]}板 · 承载{esc(t.get("承载环节") or "-")}</td></tr>')
        for s in t['环节']:
            r.append(f'<tr><td colspan="5" style="background:#faf7f0"><b>── {esc(s["环节"])}</b> <span class="mut">({s["家数"]}只·开板{s["开板占比"]})</span> <span class="{vcls(s["快判"])}">{esc(s["快判"])}</span></td></tr>')
            for g in s['个股']: r.append(row(g,qmap))
    dg=zt.get('待归位_行业兜底') or []
    if dg:
        r.append(f'<tr style="background:#f3eee1"><td colspan="5"><b>【待归位 · 行业兜底】</b>{len(dg)}只 <span class="mut">(agent当日补催化归位;行业只兜底不作题材)</span></td></tr>')
        for g in dg: r.append(row(g,qmap,catalyst='<span class="mut">行业:'+esc(g.get("行业",""))+'</span>'))
    r.append('</table></div>')
    return ''.join(r)
def build_from_data(d):
    ensure(d)
    zt=json.load(open(os.path.join(L,f"涨停对链条_{d}.json"),encoding="utf-8"))
    six=json.load(open(os.path.join(L,f"主流题材6有_{d}.json"),encoding="utf-8"))
    qmap=_qmap(d)
    cl=six.get("题材_聚类口径") or []; top=cl[0] if cl else None
    dg=len(zt.get('待归位_行业兜底') or [])
    summary=(f'涨停{zt["涨停总数"]} · '+(f'主流{esc(top["题材(题材聚类口径)"])}{top["得分"]}/6({top["涨停数"]})' if top and top["得分"]>=5 else '无主流·分支轮动')+(f' · 待归位{dg}' if dg else ''))
    speed=(f'<div class="strip"><div class="kv"><div class="l">涨停</div><div class="v">{zt["涨停总数"]}</div></div>'
           f'<div class="kv"><div class="l">题材线</div><div class="v">{zt["题材线数"]}</div></div>'
           f'<div class="kv"><div class="l">全场判定</div><div class="v" style="font-size:12.5px">{esc(six.get("全场判定",""))}</div></div></div>')
    cardp=os.path.join(L,f"涨停质量荐票卡_{d}.html")
    card=('<p style="font-weight:700;margin:4px 0 4px;border-left:3px solid var(--accent);padding-left:8px">当日涨停质量Top5荐票(v5规则榜+抓龙率·第5路)</p>'+open(cardp,encoding="utf-8").read()) if os.path.isfile(cardp) else ""
    inner=speed+card+day_table(zt,qmap)
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
