# -*- coding: utf-8 -*-
import json
J=json.load(open("_tmp_j.json",encoding="utf-8"))

auction = """
<div class="hero"><div class="kick">Call Auction · 竞价认知与迭代</div>
<h1>集合竞价 · 今天能不能上、什么价上</h1>
<p>竞价是第一道证伪。这里是竞价选股池 + 昨日池结算 + 竞价语言→次日兑现的量化 + 认知迭代。</p>
<div class="stance"><span class="pill">今晨读数 · <b>算力一字引领</b></span><span class="pill">走强 · <b>浪潮(一字)/软件系</b></span></div></div>

<h2 class="hot">一、竞价选股池 · 07-08(全市场·首封≤9:31)</h2><div class="hint">以集合竞价为独立选股维度。池=今日涨停池首封≤9:31(一字/秒板);封单比=封板资金/流通市值(强&gt;3%/中1-3%/弱&lt;1%);T+1封板概率=竞价档×封单档单因子历史值。</div><div class="card"><table><tr><th>标的</th><th>首封</th><th>连板</th><th>题材</th><th>T+1封板概率(历史)</th><th>解读</th></tr>
<tr><td>浪潮信息 <span class="mut">000977</span></td><td><b>09:25一字</b></td><td>首板</td><td>算力·整机(业绩288%)</td><td>一字41.6%</td><td>★封板资金54亿+容量票+业绩硬逻辑,算力线竞价最强信号</td></tr>
<tr><td>恒尚节能 <span class="mut">603137</span></td><td><b>09:25一字</b></td><td>7板</td><td>存储跨界重组</td><td>一字41.6%×3板+31.7%</td><td>高位7板断层,概率与高度对冲,盯不炸板</td></tr>
<tr><td>华菱线缆 <span class="mut">001208</span></td><td>09:25一字</td><td>首板</td><td>电网/线缆</td><td>一字41.6%</td><td>题材待归类,散点一字</td></tr>
<tr><td>岭南控股 <span class="mut">000524</span></td><td>09:25一字</td><td>首板</td><td>旅游</td><td>一字41.6%</td><td>旅游散点</td></tr>
<tr><td>魅视科技 <span class="mut">001229</span></td><td>09:25秒板</td><td>2板</td><td>计算机设</td><td>秒板24.5%×2板21%</td><td>2板梯队票,含减持利空提示</td></tr>
<tr><td>威尔高 <span class="mut">301251</span></td><td>09:30秒板</td><td>2板</td><td>PCB(算力)</td><td>秒板24.5%×2板21%</td><td>PCB环节内相对低位,2板</td></tr>
<tr><td>华勤技术 <span class="mut">603296</span></td><td>09:30秒板</td><td>首板</td><td>算力·整机洼地</td><td>秒板24.5%</td><td>整机洼地环节点火,高低切扩散票</td></tr>
<tr><td>视源股份 <span class="mut">002841</span></td><td>09:34秒板</td><td>2板</td><td>消费电子</td><td>秒板24.5%×2板21%</td><td>含异动利空提示</td></tr>
</table></div><div class="hint">★今晨池信息:算力一字/秒板占主导(浪潮一字54亿+华勤秒板+威尔高秒板),叠加软件系(云赛/南天/深信服/绿盟)秒板扩散=竞价维度当日引领线明确指向算力+信创软件;恒尚7板一字强封续命但断层高危。</div>

<h2>二、昨日选股池结算 <span class="badge bA">每日18:00结算</span></h2><div class="hint">对前一日(07-07)竞价选股池内每只标的:T+1封板了吗/收益/炸板与否,判验证/打脸并写归因。选股池的每一天=对竞价信号库的一次实盘校准。</div><div class="card"><table><tr><th>07-07池标的</th><th>07-07竞价信号</th><th>07-08真实(T+1)</th><th>判定</th></tr>
<tr><td>浪潮信息</td><td>一字·封单强4.71%</td><td><b class="s-ok">07-08续一字涨停(2板路径)</b></td><td><span class="dA">✓强验证</span> 一字+业绩双buff,续板</td></tr>
<tr><td>恒尚节能</td><td>一字·封单强7.82%</td><td><b>07-08续一字7板</b></td><td><span class="dA">✓验证</span> 一字锁仓惯性</td></tr>
<tr><td>浪潮软件</td><td>秒板·封单强4.38%</td><td>07-08未在涨停池</td><td><span class="dC">◐ 退</span> 浪潮系分化,硬件强软件弱</td></tr>
<tr><td>威尔高</td><td>秒板·封单强4.28%</td><td><b>07-08续2板</b></td><td><span class="dA">✓验证</span> 强封单续板</td></tr>
<tr><td>紫光股份</td><td>秒板·封单薄1.11%·防烂板</td><td>07-08未封板(冲高回落+6.8%)</td><td><span class="dB">◐ 半中</span> 昨判"封单薄防烂板"应验,未封</td></tr>
<tr><td>华勤技术</td><td>秒板·封单弱0.87%·防炸</td><td><b class="s-ok">07-08续涨停(洼地点火)</b></td><td><span class="dB">◐ 意外强</span> 昨判封单弱防炸,今日反而洼地扩散封板——产业逻辑(洼地)盖过封单弱</td></tr>
</table>
<p style="font-size:12.5px;margin-top:8px"><b>★结算归因:</b>07-07池T+1封板率约3-4/8≈40-50%,符合一字41.6%历史概率。关键学习:<b>华勤(封单弱)反而续板</b>——单看竞价封单会漏判,叠加产业逻辑(整机洼地环节)才对;<b>竞价维度需与产业逻辑维度共振使用,不能单用封单强弱</b>。这是四维共振的又一注脚。</p></div>

<h2>三、竞价信号胜率追踪(训练库·持续更新) <span class="badge bA">每周一重训Δ</span></h2><div class="hint">T日竞价信号(9:25可知)→分口径统计。今日非周一未重训,Δ=基线。全表:_学习/_竞价信号胜率.md</div><div class="card"><table><tr><th>竞价信号</th><th>n</th><th>T+1(观察)</th><th>★T+2跟随</th><th>怎么用</th><th>Δ</th></tr>
<tr><td><b>竞价一字(9:25封)</b></td><td>81</td><td><b class="s-ok">77.8%/+5.39%</b></td><td><b class="s-ok">53.1%/+1.10%</b></td><td>★唯一两口径全胜信号:一字=锁仓惯性,溢价衰减慢</td><td><span class="mut">基线</span></td></tr>
<tr><td>一字×3板+</td><td>18</td><td>72.2%/+4.37%</td><td><b class="s-ok">55.6%/+1.62%</b></td><td>跟随最好组合(n小)</td><td><span class="mut">基线</span></td></tr>
<tr><td>秒板(≤9:31)</td><td>97</td><td>54.6%/+2.01%</td><td>44.3%/+0.40%</td><td>T+1还行,跟随平——弱于一字一档</td><td><span class="mut">基线</span></td></tr>
<tr><td>早盘封(≤10:00)</td><td>508</td><td>54.7%/+1.37%</td><td><span class="s-weak">45.9%/-0.16%</span></td><td>无跟随价值</td><td><span class="mut">基线</span></td></tr></table>
<p style="font-size:12.5px;margin-top:8px"><b>★核心发现(与龙虎榜相反):</b>竞价一字T+2跟随依然赢(53.1% vs 基准46.4%),龙虎榜最猛信号(净占&gt;20%)跟随崩到39%。<b>竞价一字=三口径通吃引领信号;龙虎榜信号只能观察与规避。</b>07-08浪潮一字=一字+业绩兑现双重加持,今日T+1续一字验证。</p>
<div class="hint">竞价语言→次日封板率(A档基线,窗口2026-06-15~07-07,1577样本,基准15%):</div>
<div class="card">
<div class="qbar"><div class="lab"><span>竞价一字</span><b>41.6%</b></div><div class="track"><i style="width:100%"></i></div></div>
<div class="qbar"><div class="lab"><span>秒板(≤9:31)</span><b>24.5%</b></div><div class="track"><i style="width:58.9%"></i></div></div>
<div class="qbar"><div class="lab"><span>封单强(&gt;3%)</span><b>35.0%</b></div><div class="track"><i style="width:84%"></i></div></div>
<div class="qbar"><div class="lab"><span>封单弱(&lt;1%)</span><b>12.6%</b></div><div class="track"><i style="width:30%"></i></div></div>
<div class="base">→ 封板越早、封单越强次日越强;但07-08华勤(封单弱)因产业逻辑(洼地)反续板=需四维共振校正。<span class="badge bA">A档</span></div></div>

<h2>我的认知迭代 · 时间线</h2>
<div class="tl">
<div class="tli"><div class="d">2026-07-07(首次记录)</div><div class="h">竞价证伪了算力接力</div><div class="b">07-06顶级量化重仓的算力龙紫光,07-07竞价直接低开-4.95%全天走弱 → 竞价是第一道证伪;有梯队的万通平开后+8.81。认知:退潮里竞价低开的高位算力要弃,梯队内的票才有承接。</div><div class="sup"><b>支撑:</b>紫光竞价26.9亿/高开-4.95%;万通平开/+8.81%。</div></div>
<div class="tli"><div class="d">2026-07-08</div><div class="h">★竞价不能单用:华勤(封单弱)因产业逻辑续板→四维共振校正</div><div class="b">07-07池T+1封板率约40-50%符合一字概率,一字信号(浪潮/恒尚/威尔高)全续板验证。但<b>华勤封单弱0.87%(昨判防炸)今日反而续涨停</b>——因它是算力整机洼地环节,产业逻辑盖过封单弱。<b>认知迭代:</b>①竞价维度是"点火了吗"的即时信号,但强弱判断要与产业逻辑(该不该涨)共振——单看封单会漏判洼地点火票;②浪潮一字+业绩兑现=竞价与产业双强的最高确定性组合,今日T+1续一字验证一字信号的三口径通吃;③紫光"封单薄防烂板"昨判应验(今日未封)——竞价封单强弱对"高位票"仍是好过滤器,对"洼地点火票"要让位产业逻辑。</b></div><div class="sup"><b>支撑:</b>竞价快照_20260708;07-07池6只结算(4-5只续板);华勤封单0.87%今日续板;浪潮一字54亿今日续一字。</div></div></div>

<div class="foot"><b>诚实边界:</b>竞价第一式核心信号(9:25成交额排名+开盘逐笔大单)是 <b>C档</b>只能实盘;一字/封板时间/连板层/封单强度是 <b>A档代理</b>可统计。</div>"""
J["bodies"]["auction"]=auction
json.dump(J, open("_tmp_j.json","w",encoding="utf-8"), ensure_ascii=False)
print("auction ok", len(auction))
