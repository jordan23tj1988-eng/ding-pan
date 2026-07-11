# -*- coding: utf-8 -*-
import json
J=json.load(open("_tmp_j.json",encoding="utf-8"))

logic = """
<div class="hero"><div class="kick">Industry Logic · 第四荐票源</div><h1>产业逻辑 · 逻辑纵深与卡位挖掘</h1><p>每个涨停背后必有消息。溯源→判逻辑硬度→找链条卡位→列受益公司,未涨的卡位受益股=挖掘候选荐票。题材命门管"形"(盘面强度),本页管"神"(逻辑硬不硬、能走多远)。</p><div class="stance"><span class="pill">硬度①业绩兑现 &gt; ②订单落地 &gt; ③政策/事件预期 &gt; ④纯讲故事</span><span class="pill">今日主角 · <b>算力·业绩兑现①档</b></span></div></div>

<h2 class="hot">一、今日涨停×链条快照(07-08,每日铁例行)</h2><div class="hint">当日全部涨停股逐只对产业链快照(涨停对链条.py)。<b>低位环节涨停=扩散起点候选;透支环节涨停=情绪票,高度风险大于产业逻辑。</b>已入库4/47,待建档43(优先连板股/涨停聚集行业逐只研究补库)。</div><div class="card"><table><tr><th>涨停股</th><th>板块/环节</th><th>环节位置</th><th>快判</th></tr>
<tr><td><b>浪潮信息</b>(1板一字)</td><td>AI算力/服务器整机ICT</td><td><b class="s-ok">中低位</b>(整机均+12%,浪潮+20/-0)</td><td>★<b>H1业绩+226~288%=①业绩兑现档</b>,整机低位环节+一字54亿强封,产业逻辑与位置双合,算力主线核心</td></tr>
<tr><td><b>华勤技术</b>(1板)</td><td>AI算力/服务器整机ICT</td><td><b class="s-ok">洼地</b>(华勤-21/距高-37)</td><td>★整机环节内的洼地个股点火=高低切扩散,昨判"洼地环节涨停=扩散起点"兑现</td></tr>
<tr><td><b>数据港</b>(1板)</td><td>AI算力/IDC算力租赁</td><td><b class="s-ok">深洼地</b>(IDC均-24%,数据港-38/距高-44)</td><td>★IDC深洼地环节续点火,昨判"数据港IDC预期差最大"再兑现,盯润泽跟随</td></tr>
<tr><td>星网锐捷(1板)</td><td>AI算力/通信互联</td><td>待建档(通信设备)</td><td>顶级量化(太华+知春)驱动,算力互联卡位</td></tr>
<tr><td>威尔高(2板)</td><td>AI算力/PCB</td><td>中位(PCB均+27%,威尔高-6/-19)</td><td>PCB环节内相对低位,2板梯队票</td></tr>
<tr><td>大恒科技(3板)</td><td>软件开发/机器人(待核)</td><td>待建档</td><td>身位次高,软件/机器人属性待明确,今晚建档</td></tr>
<tr><td class="mut">待建档43只</td><td class="mut">云赛智联/南天信息/深信服/绿盟/浪潮软件/网宿/岭南控股等</td><td class="mut">-</td><td class="mut">软件开发5只(信创/AI/网安)与算力软件外延优先建档</td></tr></table>
<p style="font-size:12.5px;margin-top:8px"><b>★铁例行结论:</b>今日已入库4只涨停(浪潮/华勤/数据港/威尔高)<b>全部落在AI算力链</b>,且3只在低位/洼地环节(整机/IDC)——<b>算力高低切扩散加速,资金从已到位环节(封测华天+78/存储+108)切向洼地环节(整机/IDC)</b>,昨日高低切地图判断今日大胜兑现。</p></div>

<h2>二、前置预期雷达 <span class="badge bC">明日之事·今晚增补</span></h2><div class="hint">每日扫最新消息建预期库,喂三命门做前置。每条带来源与关键时间点;事件落地日=兑现/证伪日,过期结案不删。</div><div class="card"><table><tr><th>消息(来源)</th><th>可能激活题材</th><th>潜在受益(卡位口径)</th><th>关键时间点</th><th>状态</th></tr>
<tr><td>浪潮H1预告净利+226~288%(公告·实)</td><td>算力链业绩兑现潮</td><td>整机/光模块/PCB/IDC等环节的业绩兑现者</td><td>7月中下旬预告密集期</td><td><span class="badge bA">✓兑现</span> 07-08浪潮一字涨停+爆买;<b>雷达升级:同链公司中报预告陆续披露=下一批点火扳机</b></td></tr>
<tr><td>算力中报预告季开启(行业·预期)</td><td>算力链内谁先预增谁先点火</td><td>工业富联/中科曙光/沪电/胜宏等待披露预告的算力标</td><td>7月中下旬~8月中报季</td><td><span class="badge bA">在场</span> 盯预增公告→次日竞价</td></tr>
<tr><td>机器人:埃斯顿明牌总龙(投喂·米开07-07)</td><td>人形机器人主升2能否启动</td><td>启动信号=零件环节(丝杠/传感器/灵巧手)放量首板</td><td>盯零件何时跟</td><td><span class="badge bC">观察</span> 07-08本体埃斯顿回落(距高+0→-10),零件仍未跟=独舞警示延续</td></tr>
<tr><td colspan="5" class="mut">本表由产业逻辑agent每日增补与结案。海外映射/政策/会议日程本日无新增硬事件。</td></tr></table></div>

<h2>三、挖掘荐票追踪 <span class="badge bA">每日结算·只加不删</span></h2><div class="hint">本页荐出的"逻辑硬+卡位纯+未透支"挖掘候选,逐日用真实表现结算——荐票准不准记账进化。挖掘候选≠买入推荐,盘面确认权在命门与总agent。</div><div class="card"><table><tr><th>立案日</th><th>挖掘候选</th><th>逻辑依据</th><th>状态</th><th>结算</th></tr>
<tr><td>07-08晨</td><td>光通信(方向)</td><td>原判"未涨挖掘"</td><td><span class="badge bMix">已结案</span></td><td><b class="s-weak">深度数据打脸:环节60日+72%非未涨</b>,修正为环节内落后者口径</td></tr>
<tr><td>07-08午</td><td><b>环节内落后者:新易盛/胜宏科技/欧陆通</b></td><td>所属环节大涨而个股滞涨,补涨逻辑</td><td><span class="badge bC">观察中</span></td><td>07-08:三只均未涨停(新易盛+4/胜宏+1/欧陆通未动)——补涨未启动,<b>继续观察</b>,盯环节龙头是否新高带动</td></tr>
<tr><td>07-08午</td><td><b>洼地环节:液冷/IDC/铜连接</b>(英维克/润泽/沃尔核材)</td><td>逻辑在场+价格深调=预期差最大;等催化确认</td><td><span class="badge bA">部分兑现</span></td><td><b class="s-ok">07-08:IDC环节数据港涨停✓(洼地扩散确认)</b>;液冷/铜连接仍未动。盯润泽(IDC跟随)、英维克(液冷),催化未到不追</td></tr>
<tr><td>07-08收盘</td><td><b>整机梯队:工业富联/中科曙光/紫光股份</b></td><td>浪潮业绩兑现点火整机环节,同环节中低位(+12~24%/距高-15~-22)待跟随;买预期→卖事实链条内传导</td><td><span class="badge bC">新立案</span></td><td><span class="mut">07-09起结算——看浪潮2板能否带出整机梯队</span></td></tr>
<tr><td>07-08收盘</td><td><b>IDC跟随:润泽科技(300442)</b></td><td>数据港(IDC洼地)涨停后,润泽同环节-9/距高-23为环节内相对强者,CSP开支逻辑未破</td><td><span class="badge bC">新立案</span></td><td><span class="mut">07-09起结算</span></td></tr></table></div>

<h2>四、链条深度地图库 <span class="badge bA">按产业折叠·当日主线默认展开</span></h2><div class="hint">每个产业一个折叠块(点击展开),摘要行=位置速览。数据=链条位置.py本日刷新(sina日线60日涨幅/距250日高,A档)。</div>
<details class="chain" open><summary>AI算力 · 8环节·当日主线 <span class="chip hot">存储+109%透支</span><span class="chip hot">封测到位(华天距高-4)</span><span class="chip cold">洼地:液冷/IDC/铜连接</span><span class="chip">07-08刷新</span></summary><div class="inner"><div class="hint">驱动:浪潮H1预告净利+226~288%(公告·实)=①业绩兑现档。高低切进行中:资金从已到位(封测/存储/光模块)→洼地(整机/IDC/液冷)。个股格式:60日涨幅/距250日高%。</div><div class="card"><table><tr><th>环节</th><th>卡位/逻辑</th><th>代表公司(60日/距高%)</th><th>均60日</th><th>位置判定</th><th>结论</th></tr>
<tr><td><b>HBM/存储模组</b></td><td>涨价周期+国产HBM</td><td><span style="font-size:12px">江波龙+82/-18 德明利+103/-15 兆易+141/-28</span></td><td><b>+108.6%</b></td><td><b class="s-weak">严重透支</b></td><td>翻倍,短线不追;恒尚(重组)是情绪票非产能</td></tr>
<tr><td><b>先进封装/封测</b></td><td>国产芯片必经</td><td><span style="font-size:12px">华天+78/<b class="s-weak">-4</b> 长电+125/-12 通富+47/-16</span></td><td>+83.0%</td><td><b class="s-weak">基本到位</b></td><td>★华天距前高仅-4%,07-08冲高回落未2板=<b>掩护出逃验证</b>,规避</td></tr>
<tr><td><b>光模块/CPO</b></td><td>超节点互联核心</td><td><span style="font-size:12px">旭创+63/-18 <b class="s-ok">新易盛+4/-35</b> 光迅+101/-22 东山+80/-14</span></td><td>+62.0%</td><td>高位分化</td><td>机会在环节内落后者(新易盛距高-35最深)</td></tr>
<tr><td><b>PCB(高多层)</b></td><td>AI服务器价值量</td><td><span style="font-size:12px">沪电+49/-17 <b class="s-ok">胜宏+1/-29</b> 深南+66/-12 威尔高-6/-19</span></td><td>+27.4%</td><td>中位</td><td>胜宏滞涨者;威尔高今日2板=PCB环节内相对低位补涨</td></tr>
<tr><td><b>服务器整机/ICT</b></td><td>★业绩兑现主战场(浪潮预告)</td><td><span style="font-size:12px"><b class="s-ok">浪潮+20/-0</b> 工业富联+20/-19 曙光+18/-22 紫光+24/-0 <b class="s-ok">华勤-21/-37</b></span></td><td>+12.3%</td><td><b class="s-ok">中低位·点火中</b></td><td>★本轮主战场:浪潮一字领涨、华勤(洼地)跟涨=环节内高低切;<b>工业富联/曙光待跟</b></td></tr>
<tr><td><b>液冷散热</b></td><td>超节点必配</td><td><span style="font-size:12px">英维克-22/-40 高澜+0/-21</span></td><td><b class="s-ok">-11.2%</b></td><td><b class="s-ok">洼地</b></td><td>逻辑在场价格深调=真挖掘区,等催化</td></tr>
<tr><td><b>IDC/算力租赁</b></td><td>CSP开支+70%预期</td><td><span style="font-size:12px"><b class="s-ok">数据港-38/-44</b> 润泽-9/-23</span></td><td><b class="s-ok">-23.6%</b></td><td><b class="s-ok">深洼地</b></td><td>★数据港07-08涨停=洼地扩散兑现;润泽=环节内跟随候选</td></tr>
<tr><td><b>铜连接/线缆</b></td><td>柜内互联增量</td><td><span style="font-size:12px">沃尔核材-28/-49 精达-30/-46</span></td><td><b class="s-ok">-29.2%</b></td><td><b class="s-ok">最深洼地</b></td><td>腰斩位;超节点落地叙事重启则弹性最大,需等催化</td></tr></table>
<p style="font-size:13px;margin-top:8px"><b>★链条结论(高低切地图·07-08更新):</b>已到位=封测(华天-4,已出逃)/存储(+108%透支)/光模块(+62%);<b class="s-ok">点火中=整机(浪潮业绩兑现领涨+华勤洼地跟涨)+IDC(数据港扩散)</b>;真洼地待催化=液冷/铜连接/整机内工业富联曙光。资金高低切路径今日明确验证:<b>封测/存储(到位)→整机/IDC(洼地点火)</b>,下一跳大概率整机梯队(工业富联/曙光)或IDC跟随(润泽)。</p></div></div></details>
<details class="chain"><summary>人形机器人 · 7环节 <span class="chip hot">本体埃斯顿+120%回落(距高-10)</span><span class="chip cold">洼地:灵巧手/传感器/丝杠</span><span class="chip">07-08刷新</span></summary><div class="inner"><div class="hint">个股格式:60日涨幅/距250日高%。07-08本体埃斯顿从新高回落至距高-10,零件仍未跟。</div><div class="card"><table><tr><th>核心环节</th><th>代表公司(60日/距高)</th><th>均60日</th><th>位置</th><th>结论</th></tr>
<tr><td><b>本体/集成</b></td><td><span style="font-size:12px">埃斯顿+120/<b class="s-mid">-10(回落)</b> 拓斯达+50/-28 昊志+65/-21</span></td><td><b>+78.5%</b></td><td><b class="s-weak">高位分化</b></td><td>明牌龙从新高回落,独舞降温;不接加速</td></tr>
<tr><td><b>谐波减速器</b></td><td><span style="font-size:12px">绿的+96/-20 <b class="s-ok">中大力德+2/-30</b></span></td><td>+49.2%</td><td>高位分化</td><td>中大力德=环节内落后者</td></tr>
<tr><td><b>行星滚柱丝杠</b></td><td><span style="font-size:12px">贝斯特-3/-25 五洲新春-13/-35 北特-6/-22</span></td><td>-7.5%</td><td><b class="s-ok">中低位·未启动</b></td><td>本体放量则丝杠价值量最确定,盯放量首板</td></tr>
<tr><td><b>六维力传感器</b></td><td><span style="font-size:12px">柯力+16/-22 东华-2/-35 <b class="s-ok">安培龙-42/-65</b></span></td><td>-9.3%</td><td><b class="s-ok">洼地</b></td><td>灵巧手/力控必配,深调</td></tr>
<tr><td><b>灵巧手传动</b></td><td><span style="font-size:12px">兆威机电-13/-43</span></td><td>-12.7%</td><td><b class="s-ok">洼地</b></td><td>特斯拉灵巧手迭代直接受益却在低位</td></tr>
<tr><td><b>无框力矩/空心杯</b></td><td><span style="font-size:12px">步科+8/-30 鸣志+2/-31 伟创-20/-52</span></td><td>-3.2%</td><td>洼地</td><td>量产逻辑在场,价格没走</td></tr></table>
<p style="font-size:13px;margin-top:8px"><b>★链条结论:本体独舞降温、零件仍缺席。</b>埃斯顿从新高回落(距高+0→-10),而丝杠/传感器/灵巧手三个核心价值环节仍在中低位/洼地——机器人主升2仍未启动,零件环节放量首板是启动信号。当前维持分歧调整,不接本体加速。</p></div></div></details>
<details class="chain"><summary>存储(简评) <span class="chip hot">模组+108%透支</span><span class="chip">恒尚=情绪票非产业票</span></summary><div class="inner"><div class="card"><p style="font-size:12.5px" class="mut"><b>存储线(次要):</b>恒尚6亿收购金胜电子(公告)=重组卡位非产能卡位,蹭链条度低;存储模组环节本体60日+108%已透支——恒尚7板是情绪票不是产业票,断层孤悬,情绪见顶风险。</p></div></div></details>

<h2>我的认知迭代 · 时间线</h2><div class="tl">
<div class="tli"><div class="d">2026-07-08(建页)</div><div class="h">产业逻辑独立成页,首例=算力线业绩兑现</div><div class="b">浪潮H1预告净利+226~288%(公告)→算力线是①业绩兑现档;卡位=超节点互联(光模块)/液冷;首个挖掘荐票=光通信。<b>认知:逻辑硬度决定题材能走多远,买预期卖事实。</b></div><div class="sup"><b>支撑:</b>浪潮07-07晚业绩预告公告;07-08竞价浪潮一字54.6亿。</div></div>
<div class="tli"><div class="d">2026-07-08(午·深度修正)</div><div class="h">浅层产业逻辑被全链条量化打脸——建立深度标准</div><div class="b">上午凭叙事判"光通信未涨可挖",全链27股一算光通信60日+72%非未涨,真洼地是液冷/IDC/铜连接。<b>认知:产业逻辑不量化位置=讲故事;高低切地图=已到位→洼地/落后者。</b></div><div class="sup"><b>支撑:</b>10环节代表股60日涨幅/距高全量计算。</div></div>
<div class="tli"><div class="d">2026-07-08(收盘·兑现)</div><div class="h">★高低切地图今日大胜:洼地环节全线点火</div><div class="b">昨判"资金从已到位环节切向洼地"——07-08今日已入库4只涨停(浪潮/华勤/数据港/威尔高)全在算力链,其中<b>整机(浪潮业绩兑现+华勤洼地)+IDC(数据港深洼地)三只在低位/洼地环节点火</b>,封测华天(已到位)冲高回落出逃。<b>认知迭代:</b>①产业逻辑量化位置法(高低切地图)是我的强项维度,今日四维记账里产业逻辑✓✓大胜;②买预期→卖事实的兑现(浪潮业绩落地)是硬逻辑主线点火方式,比纯情绪票可持续;③下一跳研究=整机梯队(工业富联/曙光)与IDC跟随(润泽)何时接力。</b></div><div class="sup"><b>支撑:</b>涨停对链条_20260708(入库4全落算力);链条位置整机+12%中低位/IDC-24%深洼地/封测华天-4已到位;浪潮H1+226~288%公告兑现一字涨停。</div></div></div>

<div class="foot"><b>方法:</b>消息溯源/卡位受益名单为可查证事实;逻辑硬度分档为分析框架;挖掘荐票每日结算入在案库(A档)。零编造。</div>"""
J["bodies"]["logic"]=logic
json.dump(J, open("_tmp_j.json","w",encoding="utf-8"), ensure_ascii=False)
print("logic ok", len(logic))
