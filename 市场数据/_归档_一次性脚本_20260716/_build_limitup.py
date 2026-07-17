# -*- coding: utf-8 -*-
import json,html,os
L='_学习'; d='20260708'; esc=html.escape
zt=json.load(open(f'{L}/涨停对链条_{d}.json',encoding='utf-8'))
ov=json.load(open(f'{L}/题材归位_{d}.json',encoding='utf-8'))['映射']
six=json.load(open(f'{L}/主流题材6有_{d}.json',encoding='utf-8'))
rec=json.load(open(f'{L}/涨停质量荐票_{d}.json',encoding='utf-8'))
lib=json.load(open(f'{L}/_涨停质量库.json',encoding='utf-8'))
J=json.load(open(f'{L}/judgment_{d}.json',encoding='utf-8'))
pred={x['代码']:x for x in rec['明细']}

def srcbadge(s):
    if s=='A': return '<span class="badge bA">A</span>'
    if s=='C': return '<span class="badge bC">C</span>'
    if s in('模板','模板匹配'): return '<span class="tag2 t-watch">模板</span>'
    return '<span class="dB" style="font-size:11px">B</span>'
def kbtag(g):
    t=''
    if g['开板次数']>0: t+='<span class="tag2 t-avoid">开</span> '
    if g['连板']>1: t+=f'<span class="tag2 t-attack">{g["连板"]}板</span>'
    return t or '<span class="mut" style="font-size:11px">封</span>'
def vcls(v):
    return {'主线承载核心':'s-ok','分歧/末端':'s-weak','末端扩散':'s-mid'}.get(v.split(':')[0],'mut')
def predcell(c):
    q=pred.get(c)
    if not q: return '—'
    sc=q['质量分']; col='s-ok' if sc>=70 else 's-mid' if sc>=45 else 'mut'
    return f'<span class="{col}"><b>{sc}</b></span> <span class="mut">T1 {q["预测T1胜率"]}%/{q["预测T1均涨"]}%·T2 {q["预测T2均涨"]}%</span>'
def table(lines):
    rows='<tr><th>首封</th><th>标的</th><th>封单比</th><th>身位</th><th>催化(档)</th><th>质量分·预测T1/T2</th></tr>'
    for t in lines:
        rows+=f'<tr style="background:#f3eee1"><td colspan="6"><b>【{esc(t["大方向"])}】</b> {t["家数"]}只·最高{t["最高连板"]}板 <span class="mut">承载={esc(t["承载环节"] or "-")}</span></td></tr>'
        for s in t['环节']:
            rows+=f'<tr><td colspan="6" style="background:#faf7f0"><b>── {esc(s["环节"])}</b> <span class="mut">({s["家数"]}只)</span> <span class="{vcls(s["快判"])}">{esc(s["快判"])}</span></td></tr>'
            for g in s['个股']:
                fdb=f'{g["封单比"]}%' if g['封单比'] is not None else '—'
                rows+=(f'<tr><td>{esc(g["首封"])}</td><td><b>{esc(g["名称"])}</b> <span class="mut">{esc(g["代码"])}</span></td>'
                       f'<td>{fdb}</td><td>{kbtag(g)}</td><td>{esc((g.get("催化") or "-")[:22])} {srcbadge(g.get("来源档",""))}</td><td>{predcell(g["代码"])}</td></tr>')
    return '<div class="card"><table>'+rows+'</table></div>'

cA=sum(1 for v in ov.values() if v.get('来源档')=='A'); cB=sum(1 for v in ov.values() if v.get('来源档')=='B'); cC=sum(1 for v in ov.values() if v.get('来源档')=='C')
themes=zt['题材线']; zong=zt['涨停总数']
main=next((t for t in themes if t['大方向']=='AI算力'),None); san=next((t for t in themes if t['大方向']=='散票/待核'),None)
cl=six.get('题材_聚类口径',[])

# Top5荐票卡
t5=''
for i,x in enumerate(rec['top5'],1):
    t5+=(f'<tr><td><b>{i}</b></td><td><b>{esc(x["名称"])}</b> <span class="mut">{esc(x["代码"])}</span></td>'
         f'<td><span class="ret">{x["质量分"]}</span></td><td>T1 {x["预测T1胜率"]}%/<b>{x["预测T1均涨"]}%</b> · T2 {x["预测T2均涨"]}%</td>'
         f'<td class="mut">{esc(x["匹配桶"])}</td><td class="mut">{esc(x["大方向"])}</td></tr>')

# 训练库折叠块
def libtbl(dim):
    r='<tr><th>档</th><th>n</th><th>T1胜率</th><th>T1均涨</th><th>T2胜率</th><th>T2均涨</th></tr>'
    for k,v in lib[dim].items():
        r+=f'<tr><td>{esc(k)}</td><td>{v["n"]}</td><td>{v["T1胜率"]}%</td><td class="ret">{v["T1均涨"]}%</td><td>{v.get("T2胜率")}%</td><td>{v.get("T2均涨")}%</td></tr>'
    return '<table>'+r+'</table>'
train=('<details class="chain"><summary>涨停质量训练库(每日滚动·零后视镜) <span class="chip">窗口'+lib["窗口"]+' 样本'+str(lib["样本"])+'</span> <span class="chip cold">点开看</span></summary><div class="inner">'
 f'<p class="mut" style="font-size:12.5px">口径:{esc(lib["口径"])}</p>'
 f'<p style="font-size:13px"><b>基准</b> T1胜率{lib["基准"]["T1胜率"]}%/均涨{lib["基准"]["T1均涨"]}% · T2 {lib["基准"]["T2胜率"]}%/{lib["基准"]["T2均涨"]}%</p>'
 '<h3 style="font-size:13.5px;margin-top:10px">封单比档(主因子·2%台阶)</h3>'+libtbl('封单比')+
 '<h3 style="font-size:13.5px;margin-top:10px">首封时间(最强单因子)</h3>'+libtbl('首封')+
 '<h3 style="font-size:13.5px;margin-top:10px">连板层</h3>'+libtbl('连板')+
 '<h3 style="font-size:13.5px;margin-top:10px">★交叉:首封×封单(天花板=一字×封单≥2%)</h3>'+libtbl('交叉_首封x封单')+
 '<p class="mut" style="font-size:12px;margin-top:8px">每日18:00随新涨停的T+1/T+2兑现滚动重训;当日涨停无前向不入库=零后视镜。可执行性打折:封死票T收买不进,真实T+1开盘介入。</p>'
 '</div></details>')

body=('<div class="hero"><div class="kick">Limit-Up Review · 涨停复盘(题材核对+质量训练)</div>'
 '<h1>涨停复盘 · 全量题材核对 + 质量打分</h1>'
 '<p>抓当日全部涨停→逐只催化核对三层归位→按"涨停质量训练库"给每只标预测T+1/T+2胜率与涨幅→选综合质量Top5荐票交总agent。行业只兜底,催化定题材;质量分纯机械(因子→历史桶),题材/席位/竞价/周期由总agent叠加。</p>'
 f'<div class="stance"><span class="pill">涨停·<b>{zong}只</b></span><span class="pill">主流·<b>AI算力{main["家数"] if main else 0}只(6/6)</b></span><span class="pill warn">散乱·<b>散票{san["家数"] if san else 0}只</b></span><span class="pill">质量库·<b>{lib["样本"]}样本</b></span></div></div>'
 '<h2 class="hot">★ 涨停质量 Top5 荐票 → 总agent(第5路)</h2>'
 '<div class="hint">按综合质量分(预测T1/T2胜率+涨幅)排序,桶内按封单比/连板/未开板细分。这是12号涨停复盘给总agent的机械荐票,总agent叠加题材/席位/竞价/周期综合定夺首页明日观察点。质量分高≠一定买(如魅视有减持利空,总agent会压)。</div>'
 '<div class="card hotcard"><table><tr><th>#</th><th>标的</th><th>质量分</th><th>预测溢价</th><th>匹配桶</th><th>题材线</th></tr>'+t5+'</table></div>'
 '<h2>〇 全场速览</h2>'
 '<div class="strip">'
 f'<div class="kv"><div class="l">涨停总数</div><div class="v">{zong}</div></div>'
 f'<div class="kv"><div class="l">主流(聚类6有)</div><div class="v up">{("AI算力 "+str(cl[0]["得分"])+"/6") if cl else "-"}</div></div>'
 f'<div class="kv"><div class="l">来源档A/B/C</div><div class="v">{cA}<span class="mut">/</span>{cB}<span class="mut">/</span>{cC}</div></div>'
 f'<div class="kv"><div class="l">质量分≥70</div><div class="v up">{sum(1 for x in rec["明细"] if x["质量分"]>=70)}只</div></div>'
 '</div>'
 '<h2 class="hot">一 全量三层题材归位表(含质量打分)</h2>'
 '<div class="hint">每只带封板质量四维+质量分(0-100)+预测T1/T2(该因子桶历史均值)。质量分≥70绿=强身位。</div>'
 +table(themes)+
 '<h2>二 题材核对说明 · 行业≠题材</h2>'
 '<div class="card"><p><b>跨界识别(行业与催化背离):</b> 恒尚节能"装修装饰"→存储重组(A) · 浪潮信息"计算机设备"→AI服务器业绩龙(A) · 大名城"房地产"→算力运营(C) · 浙江美大"厨卫"→AI厨电 · 视源"消费电子"→AI教育 · 大恒科技"软件开发"→机器视觉AI(3板)。'
 f'本日来源档 A{cA}/B{cB}/C{cC},C档偏多=情绪散跟风票多。</p></div>'
 '<h2>三 主线 vs 散乱结构</h2>'
 f'<div class="card"><p>主流=AI算力{main["家数"] if main else 0}只(6环节·聚类6有满分),但最高仅3板、早封占比0.41=方向真高度弱首板扩散;存储孤峰=恒尚7板(断板即退潮确认);其余电网3/旅游2/黄金1+散票{san["家数"] if san else 0}只无题材线。主线外散乱+跌停41家=分歧/退潮特征。</p></div>'
 '<h2>四 训练</h2>'
 '<div class="hint">质量因子结论沉淀在下面折叠库里,每日滚动进化。</div>'
 +train)

J['bodies']['limitup']=body
json.dump(J,open(f'{L}/judgment_{d}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('limitup重建,',len(body),'字符 | Top5第一=',rec['top5'][0]['名称'])
