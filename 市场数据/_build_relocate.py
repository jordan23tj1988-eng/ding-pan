# -*- coding: utf-8 -*-
"""按三层题材归位标准重建 07-08 judgment 的 index/theme/logic 三页(cycle/lhb/auction复用)。"""
import json,html,os
L='_学习'; d='20260708'
esc=html.escape
zt=json.load(open(f'{L}/涨停对链条_{d}.json',encoding='utf-8'))
six=json.load(open(f'{L}/主流题材6有_{d}.json',encoding='utf-8'))
J=json.load(open(f'{L}/judgment_{d}.json',encoding='utf-8'))
b=J['bodies']

def srcbadge(s):
    if s=='A': return '<span class="badge bA">A实锤</span>'
    if s=='C': return '<span class="badge bC">C存疑</span>'
    if s in('模板','模板匹配'): return '<span class="tag2 t-watch">模板</span>'
    return '<span class="dB" style="font-size:11px">B盘面</span>'
def kbtag(g):
    t=''
    if g['开板次数']>0: t+='<span class="tag2 t-avoid">开板</span> '
    if g['连板']>1: t+=f'<span class="tag2 t-attack">{g["连板"]}板</span>'
    return t or '<span class="mut" style="font-size:11px">封住</span>'
def vcls(v):
    h=v.split(':')[0]
    return {'主线承载核心':'s-ok','分歧/末端':'s-weak','末端扩散':'s-mid'}.get(h,'mut')

# ---------- 三层归位大表(theme主用) ----------
def three_layer_table(only=None):
    rows=[]
    for t in zt['题材线']:
        if only and t['大方向'] not in only: continue
        rows.append(f'<tr style="background:#f3eee1"><td colspan="5"><b>【{esc(t["大方向"])}】</b> {t["家数"]}只 · 最高{t["最高连板"]}板 · 早封占比{t.get("开板占比")} <span class="mut">承载={esc(t["承载环节"] or "-")}</span></td></tr>')
        for s in t['环节']:
            rows.append(f'<tr><td colspan="5" style="background:#faf7f0"><b>── {esc(s["环节"])}</b> <span class="mut">({s["家数"]}只·早封{s.get("早封占比")}·开板{s["开板占比"]})</span> <span class="{vcls(s["快判"])}">{esc(s["快判"])}</span></td></tr>')
            for g in s['个股']:
                fdb=f'{g["封单比"]}%' if g['封单比'] is not None else '—'
                rows.append(f'<tr><td>{esc(g["首封"])}</td><td><b>{esc(g["名称"])}</b> <span class="mut">{esc(g["代码"])}</span></td><td>封单{fdb}</td><td>{kbtag(g)}</td><td>{esc(g.get("催化") or "(模板卡位)")} {srcbadge(g.get("来源档",""))}</td></tr>')
    return '<div class="card"><table>'+''.join(rows)+'</table></div>'

# ---------- 6有两口径判定表 ----------
def sixtable():
    hy=''.join(f'<tr><td>{esc(t["题材(行业口径)"])}</td><td>{t["涨停数"]}</td><td>{t["得分"]}/6</td><td class="{"dA" if t["得分"]>=5 else ("dB" if t["得分"]==4 else "mut")}">{esc(t["判定"])}</td></tr>' for t in six['题材'][:6])
    jl=''.join(f'<tr><td><b>{esc(t["题材(题材聚类口径)"])}</b></td><td>{t["涨停数"]}</td><td>{t["得分"]}/6</td><td class="{"dA" if t["得分"]>=5 else ("dB" if t["得分"]==4 else "mut")}"><b>{esc(t["判定"])}</b></td></tr>' for t in six.get('题材_聚类口径',[]))
    return ('<div class="two">'
      '<div class="mith"><h3>行业口径(旧·会误判)</h3><table><tr><th>题材(行业)</th><th>涨停</th><th>6有</th><th>判定</th></tr>'+hy+'</table><p class="base">→ 主线被打散成一堆"分支",全场误判"无主流分支轮动"</p></div>'
      '<div class="mith"><h3>题材聚类口径(新·按催化)</h3><table><tr><th>题材线</th><th>涨停</th><th>6有</th><th>判定</th></tr>'+jl+'</table><p class="base">→ AI算力立现主流候选</p></div></div>'
      f'<div class="card hotcard"><p><b>全场判定:</b> {esc(six["全场判定"])}</p></div>')

# ========== INDEX callout(插在hero后) ==========
callout=('<h2 class="hot">题材校正 · 所属行业 ≠ 所属题材</h2>'
 '<div class="hint">本次复盘按"催化"三层归位重做。同一天两口径结论相反,这是方法升级的核心。</div>'
 +sixtable()+
 '<div class="card"><p><b>四个铁证(行业分类会把主线打散,催化才是题材):</b><br>'
 '· 恒尚节能7板 — 行业"装修装饰",实为<b>存储跨界重组</b>(6亿收购金胜电子SSD厂,A档公告)<br>'
 '· 浪潮信息 — 行业"计算机设备",实为<b>AI服务器业绩龙</b>(H1净利+226~288%,A档)<br>'
 '· 大名城 — 行业"房地产",实为<b>算力运营</b>跨界;浙江美大 — 行业"厨卫电器",实为<b>AI厨电</b><br>'
 '按行业口径这些票四散,按题材归位它们同属算力生态——<b>27只算力涨停跨6大环节,才是今日唯一主流</b>。</p></div>')

# 用callout替换index里旧的"题材·主线 算力成形中"叙述之前?——直接插在hero之后
idx=b['index']
anchor='</div></div>\n\n<h2 class="hot">明日核心观察点'
if anchor in idx:
    idx=idx.replace(anchor, '</div></div>\n\n'+callout+'\n\n<h2 class="hot">明日核心观察点',1)
else:
    # 兜底:插在第一个</div></div>之后
    p=idx.find('</div></div>')
    idx=idx[:p+12]+'\n\n'+callout+'\n\n'+idx[p+12:]
b['index']=idx

# ========== THEME 全新三层 ==========
theme=('<div class="hero"><div class="kick">Theme · 主线题材(题材命门)</div>'
 '<h1>主线题材 · 三层归位</h1>'
 '<p>大方向 → 细分环节 → 个股催化。所属行业只兜底,催化定题材。封板质量四维(首封/连板/开板/封单比)排身位。来源档 A公告实锤/B盘面/C存疑。</p>'
 '<div class="stance"><span class="pill">唯一主流 · <b>AI算力 6/6(27只)</b></span><span class="pill warn">高度缺失 · <b>算力最高仅3板</b></span><span class="pill">孤峰 · <b>恒尚存储7板</b></span></div></div>'
 '<h2>〇 主流判定 · 题材聚类口径(优先) vs 行业口径</h2>'+sixtable()+
 '<h2 class="hot">一 三层题材归位全表(47只涨停)</h2>'
 '<div class="hint">环节快判:主线承载核心=早封多家封板扎实 / 分歧末端=过半开板 / 末端扩散=普遍晚封情绪外溢。</div>'
 +three_layer_table()+
 '<h2>二 我的主线判断(操盘手读法)</h2>'
 '<div class="card"><p>'
 '<b>①主线=AI算力,方向明确但缺高度。</b>27只涨停跨6环节(服务器/数据中心/算力租赁/液冷电源/AI应用/机器视觉),6有满分6/6。驱动是业绩兑现(浪潮H1+288%、星网半年报预增、中报预告潮),不是纯情绪。但全线最高才3板(大恒)、早封占比0.41/开板0.44=<b>首板扩散为主、没有空间龙带节奏</b>=方向确定但情绪不聚焦的扩散型主线。<br>'
 '<b>②真强身位=AI服务器/PC环节。</b>浪潮信息9:25一字、封单3%、早封多家开板仅0.25=核心承载;而AI应用外溢(政务/视觉/教育/厨电/安全,7只,开板0.57)=情绪末端,可复制性差别追。<br>'
 '<b>③恒尚节能7板=存储重组孤峰,只当情绪温度计。</b>今日炸板1次+封单仅1.13%+反复风险提示,重组情绪票随时分歧;它<b>断板=退潮确认信号</b>,不作可持续主线。<br>'
 '<b>④主线外一片散乱。</b>47涨停里散票/待核13只(3/6分支,无题材线)+电网3+旅游2+黄金1,叠加跌停41家=资金在算力外找不到合力=分歧/退潮特征。</p></div>')
# 若旧theme有龙头/核心标的实数据,追加在后(保真)
old=b.get('theme','')
mk=old.find('<h2')
if mk>0:
    theme+='<h2>三 核心标的与龙头(沿用当日席位/资金实测)</h2>'+old[mk:]
b['theme']=theme

# ========== LOGIC 前置三层快照 ==========
logic_pre=('<h2 class="hot">〇 今日涨停×链条 · 三层题材归位快照</h2>'
 '<div class="hint">每只涨停的产业坐标+封板质量四维。算力线看下方环节强度;主线外散乱见"散票/待核"。</div>'
 +three_layer_table(only={'AI算力'})+
 '<div class="card"><p><b>算力线读法:</b>承载=算力租赁/服务(9只最宽)+数据中心(5只),但多为10-13点封+开板=中后段扩散;强身位=AI服务器/PC(浪潮业绩龙早封);末端=AI应用外溢(7只开板0.57)。<b>方向真、高度弱、末端散。</b></p></div>'
 '<h2>〇b 主线外题材线(存储孤峰/电网/散乱)</h2>'
 +three_layer_table(only={'存储/半导体重组','电网/特高压','黄金/贵金属','旅游/免税','散票/待核'}))
b['logic']=logic_pre+'\n'+b.get('logic','')

# ========== 一句话 & stance 刷新 ==========
J['一句话']='退潮末期·结构分化 | 题材归位:AI算力6/6唯一主流(27只跨6环节,行业口径误判无主流),但最高仅3板=方向真高度弱;恒尚存储7板孤峰、跌停仍41、散票13只=分歧退潮'
J['更新label']='2026-07-08 收盘 · 题材归位重做'

json.dump(J,open(f'{L}/judgment_{d}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('rebuilt. lens:',{k:len(v) for k,v in b.items()})
