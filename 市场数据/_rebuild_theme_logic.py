# -*- coding: utf-8 -*-
import json,html
esc=html.escape
L='_学习'
J=json.load(open(f'{L}/judgment_20260708.json',encoding='utf-8'))
six=json.load(open(f'{L}/主流题材6有_20260708.json',encoding='utf-8'))

def dcls(sc): return 'dA' if sc>=5 else ('dB' if sc==4 else 'mut')
def judge_table():
    hy=''.join(f'<tr><td>{esc(t["题材(行业口径)"])}</td><td>{t["涨停数"]}</td><td>{t["得分"]}/6</td><td class="{dcls(t["得分"])}">{esc(t["判定"])}</td></tr>' for t in six['题材'][:6])
    jl=''.join(f'<tr><td><b>{esc(t["题材(题材聚类口径)"])}</b></td><td>{t["涨停数"]}</td><td>{t["得分"]}/6</td><td class="{dcls(t["得分"])}"><b>{esc(t["判定"])}</b></td></tr>' for t in six.get('题材_聚类口径',[]))
    return ('<div class="two">'
      '<div class="mith"><h3>题材聚类口径(新·按催化)</h3><table><tr><th>题材线</th><th>涨停</th><th>6有</th><th>判定</th></tr>'+jl+'</table><p class="base">→ 按真实催化聚类,AI算力立现主流</p></div>'
      '<div class="mith"><h3>行业口径(旧·会误判)</h3><table><tr><th>行业</th><th>涨停</th><th>6有</th><th>判定</th></tr>'+hy+'</table><p class="base">→ 主线被行业字段打散成一堆"分支"</p></div></div>'
      f'<div class="card hotcard"><p><b>方向gate:</b> {esc(six["全场判定"])}。题材归属明细见 <a href="limitup.html">涨停复盘</a> 三层归位全表(本页不重复)。</p></div>')

theme=('<div class="hero"><div class="kick">Theme · 题材命门(方向)</div>'
 '<h1>主线题材 · 方向:主流还是分支</h1>'
 '<p>第三只眼管方向:今天主线是什么、是主流还是分支、能走多久。题材归属以催化为准(唯一真源在涨停复盘页),本页只做判定/生命周期/龙头。</p>'
 '<div class="stance"><span class="pill">唯一主流 · <b>AI算力 6/6(27只)</b></span><span class="pill warn">高度缺失 · <b>最高仅3板</b></span></div></div>'
 '<h2 class="hot">一 主流判定 · 5问6有(聚类口径优先)</h2>'
 '<div class="hint">6有=爆发日客观盘面(宽度/强度/容量/弹性/高度/换手),≥5主流候选/4大分支/≤3分支。聚类口径按真实题材线聚合,比行业口径准。</div>'
 +judge_table()+
 '<h2>二 主流生命周期</h2>'
 '<div class="card"><p><b>AI算力=主升浪初期,但缺高度确认。</b>驱动=业绩兑现(浪潮H1+288%、星网半年报预增、中报预告潮),27只跨6环节宽度足够(6/6);但全线最高仅3板、首板扩散为主(早封占比0.41),<b>没有空间龙带节奏=主升未真正成形</b>。断板≠结束,盯整机梯队(工业富联/中科曙光/紫光股份)能否接力、算力能否上4板。若竞价持续一字缺席(如07-09今晨)→退居分支、方向切换。</p></div>'
 '<h2>三 核心标的与龙头识别</h2>'
 '<div class="card"><p>'
 '· <b>浪潮信息(业绩龙)</b>:H1+288%、9:25一字54亿=当前算力最高身位,龙头候选但需封2板+带梯队确认。<br>'
 '· <b>星网锐捷</b>:数据中心+半年报预增,顶级量化净买近2亿=席位驱动的算力互联分支。<br>'
 '· <b>恒尚节能(7板)</b>:存储跨界重组孤峰=<b>情绪高标非算力主线</b>,只当情绪温度计,断板=退潮确认。<br>'
 '龙头尚未明确统一(业绩龙浪潮 vs 情绪龙恒尚分属两线)=<b>扩散型主线、无绝对核心</b>。</p></div>'
 '<h2>认知迭代</h2>'
 '<div class="tl"><div class="tli"><div class="d">2026-07-08</div><div class="h">聚类口径识别算力主流,行业口径误判</div>'
 '<div class="b">行业口径最高软件开发4/6=大分支,全场误判"无主流";题材聚类口径 AI算力6/6主流候选(27只)。方向gate以聚类口径为准。</div></div></div>')
J['bodies']['theme']=theme

logic=('<div class="hero"><div class="kick">Logic · 产业逻辑(纵深)</div>'
 '<h1>产业逻辑 · 逻辑硬不硬、链条谁卡位</h1>'
 '<p>题材命门管"形"(盘面强弱),产业逻辑管"神"(逻辑硬度+链条卡位+位置)。找洼地、排到位、给挖掘荐票。</p></div>'
 '<h2 class="hot">一 今日主线链条纵深 · AI算力</h2>'
 '<div class="hint">每环节量化位置(60日/距前高),判涨到位/洼地/透支,给高低切路径。</div>'
 '<div class="card"><p>'
 '<b>已到位/透支(规避):</b> 封测(华天+78%/距前高-4%,冲高回落=掩护出逃)、存储(+117%透支)。<br>'
 '<b>洼地(挖掘):</b> IDC/算力租赁(数据港60日-38/距高-44深洼)、液冷散热(英维克)、铜连接。<br>'
 '<b>业绩兑现(卡位硬):</b> 服务器整机(浪潮H1+288%,①业绩兑现档最高硬度)。<br>'
 '<b>高低切路径假设:</b> 资金从已到位封测/存储 → 洼地IDC/液冷/整机。数据港/华勤今日首板=高低切扩散第一脚印。</p></div>'
 '<h2>二 前置预期雷达</h2>'
 '<div class="card"><table><tr><th>消息(来源)</th><th>激活题材</th><th>潜在受益</th><th>时间点</th><th>状态</th></tr>'
 '<tr><td>算力链中报预告潮(公告)</td><td>AI算力业绩兑现</td><td>整机/光模块/PCB</td><td>7月中下旬</td><td class="dA">浪潮已兑现288%,续看星网/工业富联</td></tr>'
 '<tr><td>光通信率先修复(米开+券商)</td><td>光模块/CPO</td><td>中际旭创/新易盛</td><td>持续</td><td class="dB">观察,已+72%需防追高</td></tr></table></div>'
 '<h2>三 挖掘荐票追踪(第四路)</h2>'
 '<div class="card"><p>洼地扩散候选:<b>润泽科技(300442,IDC洼地)</b>、<b>英维克(002837,液冷)</b>=逻辑上受益但盘面未确认的观察位;环节内落后者需先排雷个股原因。盘面确认权在命门与总agent,此处只给"逻辑在场、等确认"名单。</p></div>'
 '<h2>四 链条深度地图库</h2>'
 '<details class="chain" open><summary><b>AI算力</b> <span class="chip hot">当日主线</span> 12环节 · 封测到位/IDC洼地</summary><div class="inner">'
 '<p>芯片(寒武纪/海光)· 光模块CPO(中际旭创/新易盛+72%)· HBM存储(+117%透支)· 先进封装(华天+78%到位)· PCB(沪电/胜宏)· 液冷(英维克 洼地)· 整机ICT(浪潮 业绩龙)· 铜连接(沃尔核材 洼地)· IDC算力租赁(数据港-38 深洼)· 数据中心交换机(星网)· 算力服务 · AI应用外溢(政务/视觉/教育/厨电 末端)。</p>'
 '<p class="base">位置口径:sina日线60日/距250日高,A档;末端应用环节=情绪外溢、可复制性差。</p></div></details>'
 '<h2>认知迭代</h2>'
 '<div class="tl"><div class="tli"><div class="d">2026-07-08</div><div class="h">产业逻辑必须量化位置,不讲故事</div>'
 '<div class="b">凭叙事判"光通信未涨"被打脸(实测60日+72%)。链条纵深必须每环节算位置,洼地=深调+逻辑在场,到位=距前高<10%。高低切=已到位→洼地。</div></div></div>')
J['bodies']['logic']=logic

json.dump(J,open(f'{L}/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('theme/logic 整段重写完成 | theme',len(theme),'logic',len(logic))
