# -*- coding: utf-8 -*-
import json
J=json.load(open("_tmp_j.json",encoding="utf-8"))

lhb = """
<div class="hero"><div class="kick">Dragon-Tiger · 席位认知与迭代</div>
<h1>龙虎榜 · 资金是谁的、认不认</h1>
<p>全局扫描全市场席位(不只盯米开点名的),用真实上榜后表现判主控与接力。下面是系统化解读 + 我的认知怎么迭代 + 靠什么数据撑着。</p>
<div class="stance"><span class="pill">主控 · <b>顶级资金+外资(算力)</b></span><span class="pill">方向 · <b>算力(整机/通信)</b></span><span class="pill">接力 · <b>业绩兑现驱动(比昨强)</b></span></div></div>

<h2 class="hot">一、S/A档席位今日买了什么 · 综合量化判断</h2><div class="hint">综合=席位维度(跟随口径胜率)×资金信号维度(净占/多空/换手挂信号胜率库)。两维都好才偏多;任一维出货即规避。判断供参考,不给买卖指令。</div><div class="card"><table><tr><th>席位·档</th><th>标的·身位</th><th>动作(核实)</th><th>席位维度</th><th>资金信号维度</th><th>★综合判断</th></tr>
<tr><td>机构+外资+A档群 <span class="dA">A</span></td><td>浪潮信息 <span class="mut">算力整机·一字首板</span></td><td>净买 <b>合计&gt;18亿</b><br><span class="mut">外资4.06亿+A档60%席1.74亿+机构0.85亿+多路</span></td><td>跟随友好<br><span class="mut">A档席2日胜率60%档</span></td><td>业绩兑现①档·一字54亿强封<br><span class="mut">一字=三口径通吃(T+2跟随53.1%)</span></td><td><b class="s-ok">方向最强·核心</b> 顶级资金+外资+机构共振爆买,算力整机业绩兑现方向;身位首板一字,盯T+1能否2板带梯队</td></tr>
<tr><td>西安太华路 <span class="dB">B(量化)</span><br>知春路派神 <span class="dA">A(量化)</span></td><td>星网锐捷 <span class="mut">算力互联·首板</span></td><td>净买 太华1.05亿+知春0.93亿</td><td>知春A档<br><span class="mut">2日59.8%/涨2.3</span></td><td>顶级量化共振·通信设备<br><span class="mut">量化系太华/知春双进=方向情报</span></td><td><b class="s-mid">方向强·量化博弈</b> 顶级量化进算力互联=通信线纳入算力主线;量化票次日看承接,别追高</td></tr>
<tr><td>沪股通+机构 <span class="dB">B</span></td><td>大恒科技 <span class="mut">软件/机器人·3板</span></td><td>净买 外资3.11亿+华泰2.27亿+平安1.0亿+高盛0.92亿</td><td>胜率杂<br><span class="mut">多席B/C档,封板晚11:16</span></td><td>身位次高但净买席胜率44.9-51.6%普通<br><span class="mut">高位3板接力,量能大但质量杂</span></td><td><b class="s-mid">身位高·质量存疑</b> 外资+机构大买给身位,但席位胜率普通+封板晚=接力质量弱于浪潮;高位分歧风险</td></tr>
<tr><td>紫阳东路 <span class="dB">B</span></td><td>恒尚节能 <span class="mut">存储·7板</span></td><td>净买 +0.57亿(+散钱封单)</td><td>2日胜率58.9%<br><span class="mut">友好但标的高危</span></td><td>7板封单锁量·情绪票<br><span class="mut">断层孤悬</span></td><td><b class="s-weak">高危规避</b> 席位友好但标的7板断层孤悬,情绪见顶风险&gt;席位价值</td></tr>
<tr><td>外资+A档 <span class="dA">A</span></td><td>视源股份 <span class="mut">消费电子·2板</span></td><td>净买 深股通0.51亿+A档60%席0.27亿</td><td>A档友好<br><span class="mut">松江中山东路60%</span></td><td>净占中档·2板梯队<br><span class="mut">消费电子(算力整机外延?)</span></td><td><b class="s-mid">中性偏多</b> 外资+A档小仓,2板身位;非主线核心,观察</td></tr></table></div><div class="hint">★底层认知(4433样本):榜单信号越猛观察越准、跟随越亏——edge在"谁买"(席位)非"买成什么样"。今日核心情报=<b>顶级资金+外资+机构+量化四方共振指向算力(浪潮整机/星网互联)</b>,方向情报价值&gt;个股跟随价值。</div>

<h2>二、席位胜率追踪 <span class="badge bA">每日更新Δ</span></h2><div class="hint">口径:榜单T日盘后出→T+1才能买/T+2才能卖,"1日"仅观察,2日/3日=可吃区间。数据源近三月稳态(_席位胜率库.json,较昨口径统一为近三月)。胜率漂移=席位风格切换信号。</div><div class="card"><table><tr><th>席位</th><th>1日·仅观察</th><th>2日·可卖日</th><th>3日</th><th>次数·档</th><th>跟随意义</th><th>Δ较昨日</th></tr>
<tr><td><b>成都北一环路</b></td><td><span class="mut">+1.77%/58.1%</span></td><td><b>+2.36%/58.9%</b></td><td>+?/56.2%</td><td>74·<span class="dA">A</span></td><td>跟随友好</td><td><span class="mut">口径校正近三月</span></td></tr>
<tr><td><b>北京知春路(派神)</b></td><td><span class="mut">+1.79%/59.6%</span></td><td><b class="s-ok">+2.30%/59.8%</b></td><td>+?/52.1%</td><td>99·<span class="dA">A</span></td><td>跟随友好·今日进星网</td><td><span class="s-ok">↑今日上榜(算力)</span></td></tr>
<tr><td><b>紫阳东路</b></td><td><span class="mut">+1.43%/56.2%</span></td><td><b>+1.93%/58.9%</b></td><td>+?/55.2%</td><td>176·<span class="dB">B</span></td><td>跟随友好·今日进恒尚</td><td><span class="mut">持平</span></td></tr>
<tr><td><b>西安太华路(量化)</b></td><td><span class="mut">+1.19%/54.7%</span></td><td>+1.46%/52.9%</td><td>+?/51.2%</td><td>472·<span class="dB">B</span></td><td>量化·小肉·今日进星网</td><td><span class="s-ok">↑今日上榜(算力)</span></td></tr>
<tr><td><b>益田路免税</b></td><td><span class="mut">+1.01%/54.0%</span></td><td><b class="s-weak">-0.84%/41.3%</b></td><td>-?/34.4%</td><td>63·<span class="dB">B</span></td><td>只利日内·勿跟</td><td><span class="mut">今日未上榜</span></td></tr></table>
<p style="font-size:12px;margin-top:6px" class="mut">★注:较07-07页口径统一为"近三月稳态",故绝对数值与昨页(近一月)有落差,非漂移;真实漂移看同口径Δ。今日看点=知春派神+太华路两大顶级量化齐进算力(星网),紫阳东路进恒尚(存储)。</p></div>

<h2>三、资金信号胜率追踪 <span class="badge bA">每周一重训Δ</span></h2><div class="hint">2026-04~07·4433股次,零后视镜。基准跟随45.0%。今日非周一未重训,Δ=基线。全表:_学习/_龙虎榜信号胜率.md</div><div class="card"><table><tr><th>信号</th><th>观察(T→T+1,不可交易)</th><th>★跟随(可吃口径)</th><th>怎么用</th><th>Δ较上期</th></tr>
<tr><td>净买占比&gt;20%</td><td><span class="mut">67.2%/+4.66%</span></td><td><b class="s-weak">38.9%/-0.25%</b></td><td>溢价被抢光,只作方向确认</td><td><span class="mut">基线</span></td></tr>
<tr><td>净买占比5-10%</td><td><span class="mut">55.6%/+1.24%</span></td><td><b class="s-ok">49.0%/+0.77%</b></td><td>跟随最好桶</td><td><span class="mut">基线</span></td></tr>
<tr><td>净买占比≤0(净卖)</td><td><span class="mut">39.9%/-0.93%</span></td><td>43.3%/-0.42%</td><td>规避信号,有效</td><td><span class="mut">基线</span></td></tr>
<tr><td>多空比≥3</td><td><span class="mut">60.6%/+3.19%</span></td><td><b class="s-weak">37.4%/-0.47%</b></td><td>越猛越无肉</td><td><span class="mut">基线</span></td></tr>
<tr><td>强档+一字锁仓(换手&lt;3%)</td><td><span class="mut">66.2%/+4.26%</span></td><td>42.6%/+0.99%</td><td>赔率型(胜率低赢时大)</td><td><span class="mut">基线</span></td></tr>
<tr><td>机构卖出解读</td><td><span class="mut">37.2%/-1.06%</span></td><td>40.6%/-0.63%</td><td>强规避信号</td><td><span class="mut">基线</span></td></tr></table></div>

<h2>我的认知迭代 · 时间线</h2>
<div class="tl">
<div class="tli"><div class="d">2026-07-06</div><div class="h">顶级量化在算力低位建仓</div><div class="b">知春路、太华路、紫阳东路三大顶级量化齐聚<b>算力</b>(紫光、中国长城)。判:退潮里唯一有真金的方向是科技/算力。</div><div class="sup"><b>支撑:</b>紫光 知春路净1.92亿+太华2.13亿+紫阳2.08亿。</div></div>
<div class="tli"><div class="d">2026-07-07</div><div class="h">一天换方向:算力 → 半导体</div><div class="b">资金没走,切到半导体华天科技爆买。认知:①科技暗线成立但载体一天一换;②算力龙紫光次日竞价低开被弃;③退潮里科技也只是首板套利。跟方向不跟高度。</div><div class="sup"><b>支撑:</b>华天 深股通6.45亿+紫阳2.71亿;净买占比13.14%、多空比3.33。</div></div>
<div class="tli"><div class="d">2026-07-08</div><div class="h">★资金回算力,但这次有业绩硬逻辑撑腰(载体从半导体→算力整机)</div><div class="b">半导体华天今日哑火(掩护出逃验证),资金<b>大举回算力整机浪潮</b>:外资4亿+A档60%席1.74亿+机构0.85亿+多路合计&gt;18亿爆买;顶级量化太华+知春派神进星网锐捷(算力互联)。<b>认知迭代:</b>①"跟方向不跟高度"再验证——半导体一日游、算力接棒;②但这次不同:浪潮有H1业绩+288%硬逻辑,不是纯情绪套利,顶级资金+外资+机构+量化四方共振=方向确定性高于07-07的半导体单资金;③席位方向情报连续三日拼图:算力(06)→半导体(07)→算力整机业绩兑现(08),资金一直在科技里找"有业绩兑现的洼地环节"。</b></div><div class="sup"><b>支撑:</b>analysis.json席位动向41条:浪潮多路净买(外资4.06亿/A档60%席1.74亿/机构0.85亿)、星网太华1.05亿+知春派神(A60.8%)0.93亿;华天今日未涨停未入强势池。校准:紫光"规避"判错(算力方向对)记在案。</div></div></div>

<div class="foot"><b>方法:</b>全局扫描全市场席位,米开固定席位表仅作先验参照、非白名单。<b>A档</b>(历史胜率/买卖力/五分类)可回测;<b>C档</b>(当日盘中操纵)只能实盘、次日榜才确认。</div>"""
J["bodies"]["lhb"]=lhb
json.dump(J, open("_tmp_j.json","w",encoding="utf-8"), ensure_ascii=False)
print("lhb ok", len(lhb))
