# -*- coding: utf-8 -*-
import json,html
esc=html.escape
L='_学习'
J=json.load(open(f'{L}/judgment_20260708.json',encoding='utf-8'))
summ=json.load(open('20260708/summary.json',encoding='utf-8'))

# ============ 观察点数据(基于已确立的真实判断+今晨竞价验证) ============
OBS=[
 dict(nm="浪潮信息",c="000977",shen="算力·服务器整机首板 · <b>H1业绩+226~288%</b><br>一字54亿强封 + 顶级资金/外资/机构爆买",
   guan="<b>算力主线核心</b>。看竞价能否高开+封2板确认龙头,能否带出整机梯队(工业富联/中科曙光/紫光股份)。带得出=主升成形;带不出=业绩兑现一日游。",
   rec="5路全荐(产业·题材·席位·竞价·质量)", res='<b class="s-ok">四维✓✓✓✓</b>', typ='<span class="tag2 t-attack">进攻观察</span>',
   jj="高开+6.18% / 竞价13.9亿领跑,盘中封涨停 = <b>强验证</b>,主线资金坚定"),
 dict(nm="数据港 / 华勤",c="603881 / 603296",shen="算力洼地环节(IDC/整机)首板<br>数据港IDC-38/距高-44深洼地",
   guan="高低切扩散第一梯队。看洼地环节能否续板、盯润泽科技(300442)跟随;数据港今日10:31封晚,看明日能否早封转强。",
   rec="产业逻辑+题材(2路)", res='<span class="s-mid">三维✓✓·竞价待验</span>', typ='<span class="tag2 t-attack">进攻观察</span>',
   jj="平开+0.37% / 竞价0.2亿极清淡 = 资金只认核心不认扩散,<b>扩散熄火</b>"),
 dict(nm="星网锐捷",c="002396",shen="通信设备·算力互联首板<br>顶级量化(太华路+知春派神)净买近2亿",
   guan="席位驱动。看顶级量化明日是否续做、通信设备(算力互联)能否成算力线又一分支。量化撤退=纯博弈一日。",
   rec="席位+涨停质量(2路)", res='<span class="s-mid">二维✓·产逻/题材待验</span>', typ='<span class="tag2 t-watch">观察</span>',
   jj="低开-7.22% / 顶级量化竞价撤退 = <b>打脸</b>,席位驱动缺基本面接力"),
 dict(nm="大恒科技",c="600288",shen="软件/机器视觉·<b>3板(全场连板次高)</b><br>外资3.1亿+华泰2.3亿但席位胜率杂·封板晚11:16",
   guan="全场身位次高接力票(仅次恒尚)。看4板能否续、软件(信创/AI)还是机器视觉主导资金。封晚+胜率杂=接力质量存疑。",
   rec="涨停质量(身位·3板)", res='<span class="s-mid">身位✓·席位质量弱</span>', typ='<span class="tag2 t-watch">高危观察</span>',
   jj="平开0.00% / 竞价0.5亿 = 4板后观望、方向未定,高位分歧上升"),
 dict(nm="恒尚节能",c="603137",shen="存储跨界重组·<b>7板孤悬</b>·题材情绪高标<br>梯队断层(7/断/断/断/3/2)",
   guan="<b>异动红线、7板极高危</b>。看竞价与首封;一旦炸板/低开=情绪见顶信号弹,高位抱团瓦解。不追。",
   rec="无(情绪温度计·规避)", res='<span class="s-weak">情绪孤票·断层</span>', typ='<span class="tag2 t-avoid">高危规避</span>',
   jj="高开+5.67% 续封8板,今晨暂稳未见顶,但异动红线不变、规避"),
 dict(nm="华天科技",c="002185",shen="半导体封测首板·套利已证伪",
   guan="封测60日+78%距前高仅-4%已到位,今日冲高回落未2板——米开'高辨识度标单独走强=掩护出逃'验证。规避高位封测。",
   rec="无(规避)", res='<span class="s-weak">位置到位</span>', typ='<span class="tag2 t-avoid">规避</span>',
   jj="平开+0.83% 无异动,掩护出逃风险延续,规避维持"),
]
def obs_table():
    r=['<div class="card hotcard"><table><tr><th>标的</th><th>身位 / 逻辑</th><th>明日(07-09)观察点</th></tr>']
    for o in OBS:
        r.append(f'<tr><td><b>{o["nm"]}</b><br><span class="mut">{o["c"]}</span></td><td>{o["shen"]}</td><td>{o["guan"]}</td></tr>')
        r.append(f'<tr class="jjr"><td colspan="3"><span class="jjtag">荐票·共振·类型</span>荐票 {o["rec"]} · {o["res"]} · {o["typ"]}</td></tr>')
        r.append(f'<tr class="jjr"><td colspan="3"><span class="jjtag">今晨竞价 07-09</span>{o["jj"]}</td></tr>')
    r.append('</table></div>')
    return ''.join(r)

# ============ 四维+质量 五张看牌 ============
CARDS=[
 ("产业逻辑 · 该不该涨","logic.html","算力高低切扩散兑现:浪潮(整机业绩288%一字)+华勤(整机洼地)+数据港(IDC深洼)全在低位环节点火;华天封测已到位=掩护出逃。","温度:洼地环节涨停≥3起=扩散加速"),
 ("题材 · 方向gate","theme.html","★聚类口径 AI算力 6/6 主流(27只跨6环节);行业口径会拆成软件开发4/6、误判'无主流分支轮动'。题材≠行业。","温度:算力真实成色 6/6 > 行业字段"),
 ("席位 · 钱在买什么","lhb.html","顶级资金爆买浪潮(整机业绩兑现方向)、太华路+知春买星网(算力互联);顶级量化重仓算力一条链。","温度:S/A真金集中算力≥6笔=偏暖、方向明确"),
 ("竞价 · 点火了吗","auction.html","浪潮9:25一字54亿领+恒尚7板续+软件系秒板=昨强;但今晨(07-09)算力一字缺席、资金切军工(高德红外)。","温度:昨强→今晨转分歧"),
 ("涨停复盘 · 质量","limitup.html","全场47涨停按封单比+首封+连板查表打分,Top5荐票=业绩硬+封单强+早封;末端AI应用(政务/教育/厨电)质量低、别追。","温度:Top5均 T1胜率 > 基准"),
]
def cards():
    s='<div class="two">'
    for i,(t,href,body,temp) in enumerate(CARDS):
        s+=f'<a class="mith" href="{href}"><h3>{t} <span class="arw">→</span></h3><p>{body}</p><p class="base" style="margin-top:6px">{temp}</p></a>'
        if i==2: s+='</div><div class="two">'  # 换行
    return s+'</div>'

# ============ INDEX 正文(瘦身:判断+看牌) ============
index=('<div class="hero"><div class="kick">Daily Overview · 我当前的判断</div>'
 '<h1>复盘概览 · 截至 2026-07-08 收盘</h1>'
 '<p>此刻我对市场的判断+明日看牌。环境/周期看 cycle、题材归属看 涨停复盘、方向看 主线题材、资金看 龙虎榜、时机看 竞价。每天18:00更新,旧的进历史存档。</p>'
 '<div class="stance"><span class="pill">情绪档 · <b>退潮末期/结构分化</b></span><span class="pill">周期 · <b>混沌偏退</b></span><span class="pill warn">攻防 · <b>防守·仅算力主线内进攻3-4成</b></span></div></div>'
 '<h2 class="hot">明日核心观察点(07-09)· 五路荐票综合</h2>'
 '<div class="hint">五路荐票(竞价/席位/题材/产业逻辑/涨停复盘质量)→总agent裁决。每只标身位逻辑|明日触发,子行给荐票来源·共振数·类型+今晨竞价兑现。给观察点不给买卖指令,含规避型。</div>'
 +obs_table()+
 '<h2>四维 · 操盘手看牌</h2>'
 '<div class="hint">五张卡=四命门+涨停质量各出一句话判断与温度读数,点进各页看纵深。背离时看拐点预警。</div>'
 +cards()+
 '<h2 class="hot">拐点预警</h2>'
 '<div class="card"><p><b>两处背离,退潮/切换风险上升:</b><br>'
 '· <b>量价背离</b>:成交额2.56万亿仍高,但跌停41家(≈涨停87%)+炸板率23%+连板断层(7板孤峰、无4/5/6板)=赚钱效应差。<br>'
 '· <b>方向与情绪背离</b>:算力方向真(业绩兑现)但情绪不接力(全线最高仅3板),没有空间龙带节奏。<br>'
 '需竞价确认——★07-09今晨算力一字缺席、资金切军工(高德红外一字封19.4亿),切换风险显性化。<b>可证伪:</b>若明日算力仍无票上4板、恒尚断板、跌停继续两位数=退潮确认,防守。</p></div>'
 '<h2>认知迭代 · 最新</h2>'
 '<div class="tl"><div class="tli"><div class="d">2026-07-09</div><div class="h">题材≠行业 + 封板质量四维上线</div>'
 '<div class="b">题材校正改三层归位(大方向→环节→个股催化),行业只兜底。07-08实证:行业口径误判"无主流",聚类口径识别 AI算力6/6主流。07-08竞价池今晨初读盘中封板2/12=17%(远低历史),印证"方向真、高度弱、末端散"。</div>'
 '<div class="sup">完整时间线见各页;此处只显最新一条。</div></div></div>')
J['bodies']['index']=index

# ============ CYCLE 正文(环境+周期+情绪) ============
qt=summ["连板梯队"]
def ladder():
    seq=[("7板",qt.get("7",0),"high"),("6板",0,"gap"),("5板",0,"gap"),("4板",0,"gap"),("3板",qt.get("3",0),""),("2板",qt.get("2",0),""),("1板",qt.get("1",0),"")]
    s='<div class="ladder">'
    for lv,n,cls in seq:
        nm={"7板":"恒尚(存储)","3板":"大恒(算力)"}.get(lv, f"{n}只" if n else "断层")
        s+=f'<div class="rung {cls}"><div class="lv">{lv}</div><div class="nm">{nm if n or cls=="gap" else str(n)+"只"}</div></div>'
    return s+'</div>'
cycle=('<div class="hero"><div class="kick">Cycle · 环境 → 周期 → 情绪</div>'
 '<h1>周期情绪 · 市场温度与攻防档</h1>'
 '<p>四层框架的顶层:环境(量能)定周期空间,周期定情绪阶段,情绪档锁总仓位。这一页决定"今天几成仓、攻还是守"。</p></div>'
 '<h2>环境 · 量能台阶</h2>'
 f'<div class="strip"><div class="kv"><div class="l">两市成交额</div><div class="v">2.56万亿</div></div>'
 f'<div class="kv"><div class="l">涨停 / 跌停</div><div class="v">{summ["涨停家数"]} <span class="mut">/</span> {summ["跌停家数"]}</div></div>'
 f'<div class="kv"><div class="l">炸板率</div><div class="v">{round(summ["炸板率"]*100)}%</div></div>'
 f'<div class="kv"><div class="l">最高板</div><div class="v up">{summ["最高连板"]}板</div></div></div>'
 '<div class="card"><p>量能2.56万亿处<b>万亿+高位区</b>但较前日缩;然而跌停41家≈涨停47的87%、炸板率23%——<b>放量但赚钱效应差,量价背离</b>。高量掩护下个股分歧极大。</p></div>'
 '<h2>情绪 · 五阶段定位</h2>'
 '<div class="gate"><div class="g"><div class="t">冰点</div><div class="s mut">—</div></div>'
 '<div class="g"><div class="t">启动</div><div class="s mut">—</div></div>'
 '<div class="g"><div class="t">主升</div><div class="s mut">—</div></div>'
 '<div class="g"><div class="t">混沌</div><div class="s s-mid">◀ 偏此</div></div>'
 '<div class="g"><div class="t">退潮</div><div class="s s-weak">◀ 末期苗头</div></div></div>'
 '<div class="card"><p>定位=<b>退潮末期/混沌</b>:高量但分歧,业绩线(算力)独强、其余板块杀跌(41跌停)。不是冰点(还有47涨停+算力主线),也非主升(无高度接力、跌停一片)。</p></div>'
 '<h2 class="hot">连板梯队 · 断层</h2>'
 '<div class="hint">最高梯队严重断层,7板孤峰之下直接断到3板,无4/5/6板承接=没有高度接力、情绪难以为继。</div>'
 +ladder()+
 '<div class="card"><p>恒尚节能7板(存储重组孤峰,情绪票)→<b>断4/5/6板</b>→大恒科技3板(算力次高)→2板仅6只→1板39只。<b>断层=高度真空</b>,主升需要的梯队接力不存在,印证退潮特征。恒尚断板=退潮确认信号。</p></div>'
 '<h2>攻防 · 仓位总开关</h2>'
 '<div class="card"><p><b>量能台阶→仓位映射(米开口径):</b>主升8-10成 / 混沌4-5成 / 退潮0-2成。<br>当前=退潮末期/混沌→<b>防守为主,总仓压到低位;仅在算力主线内、业绩硬+竞价确认的标的上进攻3-4成</b>。退潮不硬凑,宁可空仓等主升信号(算力上4板+梯队重建)。</p></div>'
 '<h2>认知迭代</h2>'
 '<div class="tl"><div class="tli"><div class="d">2026-07-08</div><div class="h">量价背离+梯队断层=退潮末期</div>'
 '<div class="b">2.56万亿高量但跌停41、炸板23%、连板断层(7→3)。A档4/4确认退潮结构;情绪档判混沌偏退,防守。</div></div></div>')
J['bodies']['cycle']=cycle

json.dump(J,open(f'{L}/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('index/cycle 整段重写完成 | index',len(index),'cycle',len(cycle))
