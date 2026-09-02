# -*- coding: utf-8 -*-
"""生成 index + cycle body 并注入 judgment_20260902.json"""
import json, os
L = r'D:\股票数据\市场数据\_学习'
d = '20260902'
J = os.path.join(L, 'judgment_%s.json' % d)

# ============ 数据 ============
temp = '30.5'; tf = '偏冷'; temp_prev = '63.1'; temp_chg = '-32.6'
zt = 52; dt = 8; zb = '22.4%'; fb = '77.6%'; vol = '17912'; vol_prev = '20334'; maxb = 4
yijin2 = '10.8%'; erjin3 = '44.4%'; gaodu = '40.0%'
ladder = '4板2 · 3板4 · 2板7 · 1板39'
stage = '退潮第2日'

# ============ index body ============
index_body = '''<div class="rowA">
<div class="hero"><div class="kick">Index · 总判断 · 截至 09-02 收盘</div>
<h1>五维退潮共振 · 冷档空仓防守</h1>
<p>回暖第1日证伪为一日脉冲：温度63.1→30.5单日-32.6、涨停83→52、跌停0→8、炸板率6.7%→22.4%、最高板7→4断层、量能破2万亿。五路全C档防守空仓，无分歧。</p>
<div class="stance"><span class="pill warn">状态 · <b class="s-weak">C档防守 · 总仓0%</b></span></div></div>
<div class="kpi" data-v="30.5"><b>情绪温度</b><span class="big">30.5<small>°C · 偏冷(-32.6)</small></span></div>
<div class="kpi" data-v="52"><b>涨停/跌停</b><span class="big">52<small>只 / 8只 · 炸板22.4%</small></span></div>
<div class="kpi" data-v="17912"><b>两市量能</b><span class="big">1.79<small>T · 跌破2万亿</small></span></div>
<div class="kpi" data-v="4"><b>最高板</b><span class="big">4<small>板 · 7→4断层</small></span></div>
</div>

<h2>一 总判断<span class="hint">总裁决 · 五路对抗总审</span></h2>
<div class="card"><b>总裁决：C档防守 · 置信80</b>
<p style="margin:6px 0 0">五路全C档防守空仓，无分歧。五维退潮证据各自独立同向：竞价回暖追池套(0901池结算-1.48%)、资金温度3分位极冷单日脉冲第4次、题材无主线第7日、业绩腿静默第5次(T-1交叉首次归零)、全池负期望第13日(执1max45.4%&lt;50%)。昨日总裁决C档防守(置信72)被今日全面验证正确——保留的auction轻仓窄窗(掌阅科技)今日结算-2.82%套、theme的B档观察(农业/消费低切)全缩圈证伪、情绪回暖被证实为抛压枯竭式一日脉冲。今日防守共识比昨日更硬：量能跌破2万亿+最高板7→4断层+跌停0→8，冷档空仓是唯一共识且为铁律内最优。</p></div>

<h2>二 五路裁决<span class="hint">五命门独立判断 · 全C档</span></h2>
<div class="routes">
<div class="rt"><b>竞价</b><span class="chip warn">C</span><p>回暖第1日追池套坐实、反转日买新不买旧回归。0901池19只执行均收-1.48%、封板率31.6%、胜率26.3%。温度63.1→30.5暴跌，8只一字全高开≥5被闸门挡、秒板负edge，全池无可吃正期望带→空仓。<span class="mut">置信72</span></p></div>
<div class="rt"><b>席位</b><span class="chip warn">C</span><p>资金温度3分位极冷(&lt;34)，单日脉冲第4次坐实；S档3席同向率0/4=0%完全瓦解；机构/北向/量化三方配置盘冻结，总金额56.4亿较昨87.8亿-36%。唯一干净进攻=博云新材(A档江苏路)但单A档无S档共现且温度极冷，按纪律不下手。<span class="mut">置信85</span></p></div>
<div class="rt"><b>题材</b><span class="chip warn">C</span><p>无主线第7日坐实+情绪回暖一日游证伪。低切承接线(农业/消费)次日全缩圈未立主线：农业8→2、消费6→3、传媒11→3续缩，无一线宽≥13。叠加温度偏冷/涨停52/最高板4高度出清。空仓0荐3观察。<span class="mut">置信62</span></p></div>
<div class="rt"><b>逻辑</b><span class="chip warn">C</span><p>业绩腿静默第5次坐实。T-1交叉(A池0901·211∩涨停0902)=0只首次归零+存储0涨停+三票未回池。广汇能源600256持仓已于0831 T_close以6.76元了结(+25.0%)，口径缺口闭合，当前空仓。<span class="mut">置信80</span></p></div>
<div class="rt"><b>质量</b><span class="chip warn">C</span><p>全池负期望第13日：执1max45.4%(飞龙股份)&lt;50%且命中≥3只=0。承接资金低位回补≠质量修复——单票封单max4.30亿&lt;5.65亿门槛、封单≥4亿家数1&lt;3，资金只回补低位首板不接力高位连板。<span class="mut">置信74</span></p></div>
</div>

<h2>三 检查四项<span class="hint">零编造 · 零后视镜 · 题材一致 · 趋同盲区</span></h2>
<div class="rowC">
<div class="card"><b>A档编造</b><p style="margin:4px 0 0">五路无A档、荐票全0。观察/持仓代码逐一核验∈20260902 zt_pool(52只剔ST)全通过。观察理由均含量化历史对照(auction带桶n值/lhb带A档江苏路n=140/limitup带质量桶n值)，无编造代码、无非池荐票。</p></div>
<div class="card"><b>题材一致性</b><p style="margin:4px 0 0">抽查五路全部标的题材标注与题材归位_20260902.json逐一比对全部一致(归位52/52全B档行业兜底，A档0)。</p></div>
<div class="card"><b>零后视镜</b><p style="margin:4px 0 0">五路判断只用≤20260902留档数据；可证伪条件均为次日验证点非后视镜；无竞价第一式事后高胜率类引用。</p></div>
<div class="card"><b>趋同盲区/矛盾</b><p style="margin:4px 0 0">五路全C防守但各自由不同数据独立算出(竞价套/资金冷/业绩静默/质量负期望/无主线五维)，非趋同盲区；lhb不读竞价、theme不读质量等路间盲区已在各路"问题"字段如实声明。</p></div>
</div>

<h2>四 总裁决<span class="hint">档位 · 环境加权 · 次日验证点</span></h2>
<div class="card"><b>C档防守 · 置信80 · 总仓0%</b>
<p style="margin:6px 0 0">环境加权依据：当前温度档=偏冷(30.5)。战绩画像汇总为aggregate口径无温度分层维度，故温度档机械加权不启用(n&lt;5不参与)，退用各路整体战绩作方向性参考。均收排序：limitup +0.72% &gt; theme +0.46% &gt; auction -0.50% &gt; lhb -0.56% &gt; logic -1.95%。正edge的limitup/theme今日也判防守空仓，进一步印证冷档空仓为全系统共识非某一路保守。</p>
<p style="margin:6px 0 0" class="mut">次日验证点：①20260903读涨停质量荐票，全池执1胜率max≥48.4%(重校阈值)且命中≥3只→负期望终结升B/A；②20260903读竞价池结算_20260902，均收&gt;0且封板率≥50%→空仓踏空升B/A；③20260903读题材归位+涨停对链条，有无一线宽≥13→主线是否立；④20260903读资金温度，分位≥34→单日脉冲证伪。</p></div>
'''

# ============ cycle body ============
cycle_body = '''<div class="rowA">
<div class="hero"><div class="kick">Cycle · 周期 · 截至 09-02 收盘</div>
<h1>退潮第2日 · 五路投票全降</h1>
<p>量能17912亿跌破2万亿地板、最高板7→4断层、跌停0→8。五路周期投票全降(升0平0降5)，主判=降，无复议。</p>
<div class="stance"><span class="pill warn">周期 · <b class="s-weak">退潮 · 降</b></span></div></div>
<div class="kpi" data-v="30.5"><b>市场温度</b><span class="big">30.5<small>°C · 偏冷</small></span></div>
<div class="kpi" data-v="17912"><b>两市量能</b><span class="big">1.79<small>T · 破2万亿</small></span></div>
<div class="kpi" data-v="52"><b>涨停/炸板率</b><span class="big">52<small>只 · 22.4%</small></span></div>
<div class="kpi" data-v="4"><b>最高板</b><span class="big">4<small>板 · 7→4断层</small></span></div>
</div>

<h2>一 量能台阶<span class="hint">米开量能台阶 · 手册V2 §2.3</span></h2>
<div class="card"><div class="steps">
<div><span class="sr">缩量</span><span class="sn">1.79T<small>今</small></span></div>
<div><span class="sr">地板</span><span class="sn">2.0T<small>破</small></span></div>
<div><span class="sr">温和</span><span class="sn">2.5T<small>—</small></span></div>
<div><span class="sr">活跃</span><span class="sn">3.0T<small>—</small></span></div>
<div><span class="sr">沸腾</span><span class="sn">3.5T<small>—</small></span></div>
</div>
<p style="margin:8px 0 0" class="mut">量能20334→17912亿(-11.9%)，跌破2万亿地板，退潮期典型缩量下杀。近3日量能：08-31 20334 · 09-01 20334 · 09-02 17912。量能跌破地板是今日防守共识比昨日更硬的核心证据之一。</p></div>

<h2>二 先行指标<span class="hint">晋级率 · 三窗触发器</span></h2>
<div class="card"><table class="p2"><tr><th class="l">指标</th><th>读数</th><th>含义</th></tr>
<tr><td class="l">一进二率</td><td>10.8%</td><td>首板晋级骤降(昨18.4%)，承接意愿枯竭</td></tr>
<tr><td class="l">二进三率</td><td>44.4%</td><td>高位仍可晋级(昨80%高基数回落)</td></tr>
<tr><td class="l">高度晋级率</td><td>40.0%</td><td>高度梯队收窄(昨63.6%)</td></tr>
</table>
<p style="margin:6px 0 0" class="mut">三窗触发器：冰点&lt;25未触发(温度30.5)、过热≥85未触发、昨停溢价连负3日未触发。一进二率骤降是退潮期的领先信号。</p></div>

<h2>三 情绪五阶段 · 五路周期投票<span class="hint">周期投票台账 · 主判=降</span></h2>
<!--VOTEBOARD-->
<div class="card"><div class="stages">
<div class="st"><b>启动</b><span class="mut">—</span></div>
<div class="st"><b>加速</b><span class="mut">—</span></div>
<div class="st"><b>分歧</b><span class="mut">—</span></div>
<div class="st"><b>筑顶</b><span class="mut">—</span></div>
<div class="st on"><b>退潮</b><span class="mut">第2日</span></div>
</div>
<p style="margin:8px 0 0">五路周期投票全降：竞价降(温度-32.6)、席位降(资金3分位冷)、题材降(无主线第7日)、逻辑降(业绩静默第5次)、质量降(负期望第13日)。主判=降，加权反对份额0，无复议。</p></div>

<h2>四 连板梯队<span class="hint">4-4-3-3-3-3-2×7-1×39</span></h2>
<div class="card"><p style="margin:0 0 6px">最高板4(昨7断层)：<b>竞业达(IT服务)</b> · <b>国芳集团(零售)</b></p>
<p style="margin:0 0 6px">3板4：欢瑞世纪(影视) · 集泰股份(液冷材料) · 大晟文化(游戏) · 龙版传媒(出版)</p>
<p style="margin:0 0 6px">2板7：英力特 · 茂业商业 · 小方制药 · 香溢融通 · 九牧王 · 内蒙一机 · 恒宝股份</p>
<p style="margin:0" class="mut">高度出清(7→4断层)、梯队头重脚轻，退潮期典型结构。1板39只。</p></div>

<h2>五 攻防 · 仓位总开关<span class="hint">自适应仓位 · C档</span></h2>
<div class="card"><div class="posmeter"><span class="pm">0%</span><span class="mut">总仓 · 空仓防守</span></div>
<p style="margin:8px 0 0">退潮+冷档+C档防守，总仓0%。五路全空仓，仅保留各观察票作次日主线/反转验证备选池(竞价2/席位1/题材3/质量3观察)。进攻条件：温度≥45回暖+涨停≥60+封板率≥80%三窗齐开。</p></div>

<h2>六 自主深挖<span class="hint">指标与阈值孵化</span></h2>
<div class="card"><p style="margin:0 0 4px">负期望50%门槛重校：limitup路建议采纳「终结阈值=当日基准+5pp动态锚定(今日43.3%→48.3%非固定50%)+附加执1均涨池均≥0第二确认」，Master已拍板。</p>
<p style="margin:0">竞价闸门「高开≥5必弃」在冷档退潮日止损价值再验证：0902池8只一字全落一年桶-1.69%/21.8%最差档，闸门挡下后全池无可吃标的。</p></div>

<h2>七 我的认知迭代<span class="hint">最新在前</span></h2>
<div class="tl">
<div class="tli"><div class="d"><b>09-02</b></div><div class="h">高潮顶次日分化兑现(米开锚点坐实)</div><div class="b">封板率≥80%为高潮顶信号：0901封板率93.3%→0902兑现涨停83→52/封板率77.6%/炸板率6.7%→22.4%/温度63.1→30.5/最高板7→4断层/量能破2万亿。三路独立同向互证。</div></div>
<div class="tli"><div class="d"><b>09-02</b></div><div class="h">情绪回暖一日游(抛压枯竭式修复不传导承接资金)</div><div class="b">0901温度63.1回暖被0902证伪为一日脉冲。回暖是抛压枯竭式修复而非承接资金回归，第2日即回吐。</div></div>
</div>
'''

# ============ 注入 ============
jd = json.load(open(J, encoding='utf-8'))
bodies = jd.get('bodies', {})
bodies['index'] = index_body
bodies['cycle'] = cycle_body
jd['bodies'] = bodies
jd['一句话'] = '五维退潮共振(温度-32.6/量能破2万亿/最高板7→4断层/跌停0→8)，五路全C档防守空仓，冷档空仓为全系统共识。'
jd['ticker'] = '退潮第2日 · 温度30.5偏冷 · 涨停52/跌停8 · 炸板率22.4% · 最高板4 · 量能1.79T'
jd['archive_body'] = '退潮第2日 · C档防守 · 总仓0% · 五路全空仓'
json.dump(jd, open(J, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ============ 验证 ============
for pg in ['index', 'cycle']:
    b = bodies[pg]
    print('%s: div开%d div闭%d h2=%d' % (pg, b.count('<div'), b.count('</div>'), b.count('<h2')))
print('bodies keys:', list(bodies.keys()))
print('judgment 一句话:', jd['一句话'][:40])
