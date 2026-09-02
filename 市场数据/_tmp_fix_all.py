# -*- coding: utf-8 -*-
"""综合修复: ticker + lhb head(4kpi) + cycle(VOTEBOARD/量能/主判) + index body(6段全组件)"""
import json, re
L = r'D:\股票数据\市场数据\_学习'
J = L + r'\judgment_20260902.json'
d = json.load(open(J, encoding='utf-8'))

# ============ 1. Ticker ============
g1 = ('<div class="ticker"><div class="in"><div class="grp">'
      '<span>量能 <b class="a">1.79万亿</b></span>'
      '<span>涨停 <b class="u">52</b> / 跌停 <b class="d">8</b></span>'
      '<span>炸板 <b>15</b>·炸板率 <b>22.4%</b></span>'
      '<span>最高 <b class="u">4板</b>·竞业达</span>'
      '<span>梯队 4板2·3板4·2板7·1板39</span>'
      '<span>情绪温度 <b>30.5</b>(偏冷)</span>'
      '<span>一进二 <b>10.8%</b>·二进三 <b>44.4%</b></span>'
      '</div>')
g2 = g1.replace('<div class="ticker">', '<div class="ticker"><div class="grp" aria-hidden="true">', 1)
# 修正: 直接构造重复grp
tick = ('<div class="ticker"><div class="in">'
        '<div class="grp">'
        '<span>量能 <b class="a">1.79万亿</b></span>'
        '<span>涨停 <b class="u">52</b> / 跌停 <b class="d">8</b></span>'
        '<span>炸板 <b>15</b>·炸板率 <b>22.4%</b></span>'
        '<span>最高 <b class="u">4板</b>·竞业达</span>'
        '<span>梯队 4板2·3板4·2板7·1板39</span>'
        '<span>情绪温度 <b>30.5</b>(偏冷)</span>'
        '<span>一进二 <b>10.8%</b>·二进三 <b>44.4%</b></span>'
        '</div>'
        '<div class="grp" aria-hidden="true">'
        '<span>量能 <b class="a">1.79万亿</b></span>'
        '<span>涨停 <b class="u">52</b> / 跌停 <b class="d">8</b></span>'
        '<span>炸板 <b>15</b>·炸板率 <b>22.4%</b></span>'
        '<span>最高 <b class="u">4板</b>·竞业达</span>'
        '<span>梯队 4板2·3板4·2板7·1板39</span>'
        '<span>情绪温度 <b>30.5</b>(偏冷)</span>'
        '<span>一进二 <b>10.8%</b>·二进三 <b>44.4%</b></span>'
        '</div></div></div>')
d['ticker'] = tick

# ============ 2. lhb head: 2kpi → 4kpi ============
b = d['bodies']['lhb']
hero_end = b.find('<div class="kpi"')
hero = b[:hero_end]  # 含 rowA 开 + hero 完整 + hero闭合
# 4个标准 kpi
kpi = (
 '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M12 3v3M12 3c3 3 6 5 6 9a6 6 0 0 1-12 0c0-4 3-6 6-9z"/></svg></span><span class="chip2 c-miss">温度分位</span></div><span class="lab">资金温度</span><span class="big">3分位</span><span class="sub2">昨27分位→今日3分位(<b>极冷跌破34</b>)，单日脉冲第4次坐实(0825/0827/0831/0902四连)，三档进攻窗条件第1项(温度≥34)不再满足</span></div>'
 '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M8 8V6a4 4 0 0 1 8 0v2"/></svg></span><span class="chip2 c-miss">机构</span></div><span class="lab">机构买入</span><span class="big">5.3亿</span><span class="sub2">机构27席5.3亿(昨25席7.9亿,-33%)·北向21席13.5亿(昨28席29.7亿,-55%)·量化7席4.4亿(昨12席7.7亿,-43%)·总金额56.4亿(昨87.8亿,<b>-36%</b>)</span></div>'
 '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg></span><span class="chip2 c-miss">S/A出手</span></div><span class="lab">S档出手</span><span class="big">3席次</span><span class="sub2">独立S席位3个(0901为4席)且同向率<b>0/4=0%</b>完全瓦解；唯一干净A档=江苏路(n=140)→博云新材002297+4659万</span></div>'
 '<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span><span class="chip2 c-half">知名游资</span></div><span class="lab">游资接棒</span><span class="big">147席</span><span class="sub2">知名游资147席27.4亿(昨124席37.4亿,席次+23但额-27%)·配置盘冻结、游资仅低位接刀(百洋/敦煌双接刀)，无进攻</span></div>'
 '</div>'
# 原 head 末尾的 </div> 闭合 rowA 被 kpi 串自带
# hero 以 </div> 闭合, 需确认 hero 结尾
if not hero.rstrip().endswith('</div>'):
    hero = hero.rstrip() + '</div>'
new_head = hero + kpi
d['bodies']['lhb'] = new_head + b[b.find('<h2'):]

# ============ 3. cycle: VOTEBOARD闭合 + 量能 + 主判 ============
c = d['bodies']['cycle']
# 3a. 量能: 段一文本 17912亿 → 加 1.79万亿
c = c.replace('量能20334→17912亿(-11.9%)', '量能20334→17912亿(1.79万亿,-11.9%)')
# 3b. 主判: 主判=降 → 主判=退潮·降 (h2 hint + 文本两处)
c = c.replace('周期投票台账 · 主判=降', '周期投票台账 · 主判=退潮·降')
c = c.replace('主判=降，加权反对份额0', '主判=退潮·降，加权反对份额0')
# 3c. VOTEBOARD 闭合: 在 <!--VOTEBOARD--> 后段三末尾加 <!--/VOTEBOARD-->
# 找到 段三 的 h2 和 段四 h2, 在段四 h2 前加闭合
i4 = c.find('<h2>四 连板梯队')
if i4 > 0 and '<!--/VOTEBOARD-->' not in c:
    c = c[:i4] + '<!--/VOTEBOARD-->\n' + c[i4:]
d['bodies']['cycle'] = c

# ============ 4. index body (6段全组件) ============
def hb(pct, week, name):
    p = pct
    neg = p < 0
    w = max(int(abs(p) * 8), 4)
    cls = 'neg' if neg else 'pos'
    hbv = 'dn' if neg else 'up'
    return ('<div class="hb"><span class="hbl">%s</span><div class="hbt"><i class="%s" style="width:%d%%"></i></div>'
            '<span class="hbv %s">%+.2f%%</span><span class="hbs">本周%+.2f%%</span></div>' % (name, cls, w, hbv, p, week))

hbs = ''.join([
    hb(-2.34, -0.65, '竞价auction'),
    hb(2.88, -0.23, '龙虎榜席位'),
    hb(2.0, -0.34, '主线题材'),
    hb(1.05, 0.31, '产业逻辑'),
    hb(-1.16, 0.0, '涨停质量'),
    hb(0.9, 0.0, 'Master总账'),
])

routes = (
 '<div class="routes">'
 '<a class="rt" href="auction.html"><span class="rtn">01 / 第一路</span><span class="rtm">竞价·时机</span><b class="rtt s-weak">C·防守</b><span class="rtd">C · 回暖第1日追池套坐实(0901池结算-1.48%/封板率31.6%&lt;50%)，竞价温度63.1→30.5暴跌-32.6点，一字8只全高开≥5被闸门挡，全池无可吃正期望带，空仓</span></a>'
 '<a class="rt" href="lhb.html"><span class="rtn">02 / 第二路</span><span class="rtm">龙虎榜·席位</span><b class="rtt s-weak">C·防守</b><span class="rtd">C · 资金温度3分位极冷(&lt;34)，单日脉冲第4次坐实，S档3席同向率0/4瓦解，机构/北向/量化三方配置盘冻结、总金额-36%，空仓</span></a>'
 '<a class="rt" href="theme.html"><span class="rtn">03 / 第三路</span><span class="rtm">主线·题材</span><b class="rtt s-weak">C·防守</b><span class="rtd">C · 无主线第7日，农业8→2拆线/消费6→3/传媒11→3续缩，无一线宽≥13(最宽算力/液冷仅7)，情绪回暖一日游证伪，观察不参与</span></a>'
 '<a class="rt" href="logic.html"><span class="rtn">04 / 第四路</span><span class="rtm">产业·逻辑</span><b class="rtt s-weak">C·防守</b><span class="rtd">C · 业绩腿静默第5次(T-1交叉首次归零226∩涨停=0)，存储环节无涨停、露头转沉寂，无产业共振，空仓</span></a>'
 '<a class="rt" href="limitup.html"><span class="rtn">05 / 第五路</span><span class="rtm">涨停·质量</span><b class="rtt s-weak">C·防守</b><span class="rtd">C · 全池负期望第13日(执1max45.4%&lt;50%/52只命中0规)，封板率93.3%→77.6%跌破80%，最高板7→4断层，空仓</span></a>'
 '</div>')

# 认知迭代 tli
tli_cog = (
 '<div class="card"><b>认知迭代 · 今日3条</b>'
 '<div class="tli"><b>高潮顶次日分化兑现</b>封板率≥80%为高潮顶信号→0901封板率93.3%≥80%→0902兑现涨停83→52/封板率77.6%/温度63.1→30.5暴跌/最高板7→4断层。依据:limitup/auction/theme三路独立同向。可证伪:20260903涨停≥60且封板率≥80%→分化结束;否则退潮第2日。<span class="mut">·20260902</span></div>'
 '<div class="tli"><b>情绪回暖一日游</b>0901温度63.1回暖被0902证伪为抛压枯竭式修复(非承接资金回归),第2日即回吐。依据:竞价温度暴跌+lhb资金3分位极冷+theme无主线三路同向。可证伪:20260903资金温度≥34且涨停≥60且执1max≥48.4%→真回暖。<span class="mut">·20260902</span></div>'
 '<div class="tli"><b>竞价闸门冷档止损再验证</b>高开≥5必弃在退潮日止损:0902一字8只全高开9.94~10.08%落一年桶最差档(-1.69%/21.8%),闸门挡下后全池无可吃标的。<span class="mut">·20260902</span></div>'
 '</div>')

# 指派清单 tli
tli_assign = (
 '<div class="card"><b>指派清单 · 5条(全部已承接·完成)</b>'
 '<div class="tli"><b>AS-20260901-001→auction</b>回暖第1日轻仓进攻是否兑现:读竞价池结算_20260901.json,0901池执行均收-1.48%&lt;0且封板率31.6%&lt;50%→降C、反转日买新不买旧回归坐实<span class="mut">·已完成</span></div>'
 '<div class="tli"><b>AS-20260901-002→lhb</b>单日脉冲第4次验证:温度3分位&lt;34且S档同向率0/4→第4次坐实,验证点关闭<span class="mut">·已完成</span></div>'
 '<div class="tli"><b>AS-20260901-003→theme</b>农业/消费低切是否立主线:农业8→2拆线/消费6→3/无一线宽≥13→反抽一日游证伪<span class="mut">·已完成</span></div>'
 '<div class="tli"><b>AS-20260901-004→logic</b>业绩腿是否回归:T-1交叉226∩涨停=0归零→静默第5次坐实<span class="mut">·已完成</span></div>'
 '<div class="tli"><b>AS-20260901-005→limitup</b>负期望是否终结:执1max45.4%&lt;50%→第13日坐实<span class="mut">·已完成</span></div>'
 '</div>')

# obs 线索跟踪
obs = (
 '<div class="obs"><div class="obs-head"><span class="obs-nm">线索跟踪 <span class="mut">3条·覆盖五路</span></span><span class="obs-pos tag">看板</span></div>'
 '<div class="obs-watch"><span class="obs-lab">观察中</span>AS-20260901-001→auction中档池负期望连续打破是否重估(已证实:0901池-1.48%证伪,转正属身位噪声) · AS-20260901-002→lhb单日脉冲第4次(已证实:坐实,验证点关闭) · AS-20260901-003→theme低切是否立主线(已证实:拆线证伪)</div>'
 '<div class="obs-rec"><span class="obs-lab2">观察备选池(次日主线/反转验证)</span>auction观2(道明光学002632/香溢融通600830)·lhb观1(博云新材002297)·theme观3(集泰股份002909/国芳集团601086/欢瑞世纪000892)·limitup观3(飞龙股份002536/天禾股份002999/力鼎光电605118)——全部∈今日zt_pool,零编造</div>'
 '</div>')

index_body = (
 '<div class="rowA">'
 '<div class="hero"><div class="kick">Index · 总判断 · 截至 09-02 收盘</div>'
 '<h1>退潮第2日 · 五路全C档防守空仓</h1>'
 '<p>情绪温度<b>30.5偏冷</b>(昨63.1,-32.6)，涨停52(昨83)/跌停8(昨0)/炸板率22.4%(昨6.7%)/封板率77.6%跌破80%/最高板7→4断层/量能17912亿跌破2万亿地板。昨日「回暖第1日」被全面证伪为一日脉冲，五维退潮共振(竞价回暖追池套/资金3分位极冷/无主线第7日/业绩腿静默第5次/全池负期望第13日)，五路独立同向算出防守，<b>总裁决C档(置信80)</b>，总仓0%。</p>'
 '<div class="stance"><span class="pill cold">C档·防守空仓</span><span class="pill warn">退潮第2日·封板率77.6%跌破80%</span><span class="pill hot">五维退潮共振·无分歧</span></div></div>'
 '<div class="kpi"><div class="top"><span class="ico">🌡</span><span class="chip2 c-miss">温度</span></div><span class="lab">情绪温度</span><span class="big">30.5</span><span class="sub2">昨63.1 → <b>-32.6</b> 暴跌 · 偏冷</span><div class="gauge"><div class="gv">30.5 <span class="mut">偏冷</span></div><div class="gtrack"><i class="gmark" style="left:30.5%"></i></div><div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div></div>'
 '<div class="kpi"><div class="top"><span class="ico">🔥</span><span class="chip2 c-miss">涨停</span></div><span class="lab">涨停/跌停</span><span class="big">52<small>/ 8</small></span><span class="sub2">涨停52(昨83,-37.3%)·跌停8(昨0)·炸板15(22.4%)</span></div>'
 '<div class="kpi"><div class="top"><span class="ico">💰</span><span class="chip2 c-miss">量能</span></div><span class="lab">两市成交额</span><span class="big">1.79<small>T</small></span><span class="sub2">17912亿(昨20334亿,-11.9%)·跌破2万亿地板</span></div>'
 '<div class="kpi"><div class="top"><span class="ico">🏔</span><span class="chip2 c-miss">最高板</span></div><span class="lab">连板高度</span><span class="big">4<small>板</small></span><span class="sub2">竞业达/国芳集团 · 梯队4板2·3板4·2板7·1板39</span></div>'
 '</div>'
 '<h2>一 总判断</h2>'
 '<div class="card"><b>总裁决 · C档防守(置信80)</b>五路全C档防守空仓，无分歧。五维退潮证据各自独立同向：竞价回暖追池套(0901池结算-1.48%)、资金温度3分位极冷单日脉冲第4次、题材无主线第7日、业绩腿静默第5次(T-1交叉首次归零)、全池负期望第13日(执1max45.4%&lt;50%)。昨日总裁决C档防守被今日全面验证正确，今日防守共识比昨日更硬：量能跌破2万亿地板+最高板7→4断层+跌停0→8，五路无一路主张进攻，冷档空仓是唯一共识且为铁律内最优。</div>'
 '<h2>二 五路裁决</h2>'
 + routes +
 '<h2>三 检查四项</h2>'
 '<div class="card"><b>① A档编造核查 · 通过</b>五路无A档(全C)、荐票全0。观察/持仓代码逐一核验∈20260902 zt_pool(52只剔ST)：auction观2/lhb观1/theme观3/limitup观3全部∈今日池，无编造代码、无非池荐票。观察理由均含量化历史对照(桶n值/身位n值/江苏路n=140非小样本)。</div>'
 '<div class="card"><b>② 题材一致性 · 通过</b>五路全部标的题材标注与题材归位_20260902.json逐一比对全部一致(归位52/52全B档行业兜底,A档0)，无任一标的退回用申万行业口径冒充题材口径。</div>'
 '<div class="card"><b>③ 后视镜核查 · 通过</b>决策仅用≤20260902已留档数据；昨日总裁决C档防守被今日数据机械化验证正确，非后视镜补记。</div>'
 '<div class="card"><b>④ 可证伪条件 · 5条</b>总裁决带次日验证点5条(质量执1max阈值/竞价池结算/题材宽≥13/业绩T-1交叉/资金温度S档共振)，每条带判定条件可机械化结算。</div>'
 '<h2>四 总裁决 · 自主进化</h2>'
 '<div class="rowE">'
 '<div class="card"><b>六路独立核算 · 战绩画像</b>' + hbs + '</div>'
 '<div class="card"><b>总裁决 · C档防守空仓</b>总仓0%，仅保留各观察票作次日主线/反转验证备选池。环境加权：当前温度档偏冷(30.5)，战绩画像汇总为aggregate口径无温度分层维度，温度档机械加权不启用(n&lt;5)，退用各路整体战绩作方向性参考——正edge的limitup(+0.72%)/theme(+0.46%)今日也判防守空仓，进一步印证冷档空仓为全系统共识。置信80(五路高置信C档共识加权)。</div>'
 '</div>'
 '<h2>五 深挖与线索</h2>'
 + obs +
 '<h2>六 指派清单 · 认知迭代</h2>'
 + tli_assign + tli_cog
)

d['bodies']['index'] = index_body

# 写回
json.dump(d, open(J, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 验证
print('=== 验证 ===')
print('ticker div开=%d 闭=%d' % (tick.count('<div'), tick.count('</div>')))
lb = d['bodies']['lhb']
print('lhb head kpi=%d div开=%d闭=%d' % (lb[:lb.find('<h2')].count('class="kpi"'), lb[:lb.find('<h2')].count('<div'), lb[:lb.find('<h2')].count('</div>')))
cy = d['bodies']['cycle']
print('cycle VOTEBOARD 起=%d 止=%d, 1.79万亿=%d, 主判=退潮·降=%d' % (cy.count('<!--VOTEBOARD-->'), cy.count('<!--/VOTEBOARD-->'), cy.count('1.79万亿'), cy.count('主判=退潮·降')))
ix = d['bodies']['index']
print('index 段数=%d div开=%d闭=%d gauge=%d obs=%d obs-head=%d hb=%d rtn=%d tli=%d rowE=%d' % (
    ix.count('<h2'), ix.count('<div'), ix.count('</div>'),
    ix.count('class="gauge"'), ix.count('class="obs"'), ix.count('class="obs-head"'),
    ix.count('class="hb"'), ix.count('class="rtn"'), ix.count('class="tli"'), ix.count('class="rowE"')))
