# -*- coding: utf-8 -*-
"""一次性: 生成 cycle_body_20260821.html(七段, 参照 20260818 模板结构)。SVG 从先行指标卡提取, 投票/准确率从台账读。"""
import json, io, re, os
L = r'D:\股票数据\市场数据\_学习'

svg = re.search(r'<svg.*?</svg>', io.open(os.path.join(L, '先行指标卡_20260821.html'), encoding='utf-8').read(), re.S).group(0)
acc = json.load(io.open(os.path.join(L, '_周期投票准确率.json'), encoding='utf-8'))
votes = {r: json.load(io.open(os.path.join(L, f'周期投票_{r}_20260821.json'), encoding='utf-8')) for r in ['auction', 'lhb', 'theme', 'logic', 'limitup']}
main = json.load(io.open(os.path.join(L, '周期主判_20260821.json'), encoding='utf-8'))

def acc_s(r):
    a = acc.get(r, {'n': 0, 'hits': 0})
    return f"{a['hits']}/{a['n']}"

vote_cards = ''
for i, (r, nm) in enumerate([('auction', '①竞价'), ('lhb', '②席位'), ('theme', '③题材'), ('logic', '④产逻'), ('limitup', '⑤质量')]):
    v = votes[r]
    vote_cards += (f'<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">'
                   f'{nm} <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">{v["stage"]}·{v["direction"]}</b><br>'
                   f'<span style="color:#5c6674">置信{v["confidence"]}·准确率{acc_s(r)}</span></div>')

html = f'''<div class="rowA">
<div class="hero"><div class="kick">Cycle · 周期与情绪 · 截至 2026-08-21 收盘</div><h1>冰点段:温度29.4→23.4跌破冰点线,<em>修复一日游后再入冰点,防守空仓</em></h1><p>量能台阶→先行指标三窗→情绪五阶段(五路投票)→连板梯队→攻防总开关,五件事定仓位。</p><div class="stance"><span class="pill warn">周期 · <b class="s-mid">冰点</b></span><span class="pill ">量能 · <b>1.88万亿弱修档</b></span><span class="pill hot"><b class="s-ok">⚠冰点段 · 防守空仓</b></span></div></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M3 17l5-6 4 4 6-8 3 4"/></svg></span><span class="chip2 c-half">弱修</span></div><span class="lab">两市量能</span><span class="big" data-v="1.88" data-dec="2">1.88<span style="font-size:15px">万亿</span></span><span class="sub2">2.08→1.88缩量-9.6%(&lt;3.0弱修档);跌破2万亿地板</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span><span class="chip2 c-cool">冰点·平</span></div><span class="lab">情绪阶段(主判)</span><span class="big" style="font-size:20px">冰点·平</span><span class="sub2">五路投票5平(0反对);主判冰点·平(置信70)</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span><span class="chip2 c-cool">冰点</span></div><span class="lab">市场温度 · 250日分位</span><span class="big" data-v="23.4" data-dec="1">23.4</span><div class="gauge"><div class="gtrack"><i class="gmark" style="left:23.4%"></i></div><div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div><span class="sub2">昨29.4-6.0跌破冰点线25;冰点档=防守,等修复信号</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M4 20h16M6 16l4-8 4 5 4-9"/></svg></span><span class="chip2 c-cool">空仓0成</span></div><span class="lab">执行仓位上限</span><span class="big" style="font-size:20px">空仓0成</span><span class="sub2">总审C防守·仓位0;冰点段空仓,禁套利</span></div>
</div>
<h2>一 量能台阶 · 我站在哪一阶</h2>
<div class="steps">
<div class="step dim"><span class="sr">≥3.8</span><span class="sn">主升2确认<small>放量突破</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.5~3.8</span><span class="sn">突破压力<small>需增量</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.3~3.5</span><span class="sn">强修<small>量能承接</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.0~3.3</span><span class="sn">过渡<small>量能中枢</small></span><span class="sd"></span></div>
<div class="step cur"><span class="sr">&lt;3.0</span><span class="sn">弱修<small>缩量分歧</small></span><span class="sd"><span class="dayc now">08-21 1.88</span><span class="dayc">08-20 2.08</span><span class="dayc">08-18 2.40</span></span></div>
</div>
<div class="hint">量能18793亿=1.88万亿落"弱修"档,较昨2.08万亿缩量-2001亿(-9.6%)跌破2万亿地板——修复日量能未续,资金退潮不追高;距3.0过渡档尚有1.1万亿差距,量能台阶连续第2日落"弱修"档。A档:米开量能台阶换算(腾讯替代源)。</div>
<h2>二 先行指标 · 三窗触发器</h2><div class="card"><p style="font-weight:700;margin-bottom:2px">情绪先行指标 · 近20日 <span class="mut" style="font-weight:400">(脚本段A档 · 情绪先行指标.py --card · 当日温度 23.4·冰点,阈值冰点&lt;25/过热≥85)</span></p>{svg}</div>
<h2>三 情绪五阶段 · 五路周期投票</h2>
<div class="stages">
<div class="st on">冰点<small>温度23.4已至</small></div>
<div class="st">启动<small>昨修复夭折</small></div>
<div class="st">发酵·主升<small>主线全灭</small></div>
<div class="st">高潮<small>封板率75%续破80%</small></div>
<div class="st">退潮<small>跌停13未收敛</small></div></div>
<div style="margin:10px 0;padding:12px 14px;background:#14171e;border:1px solid #2a2f3a;border-radius:10px">
<div style="font-size:11px;letter-spacing:2px;color:#d9a441;font-family:monospace">五路周期投票 · 主判=冰点·平</div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
{vote_cards}
</div>
<div style="margin-top:8px;color:#5c6674;font-size:11px">分歧未达阈值(当日≥3/5或加权≥0.60复议;连续3日≥2路同向重做) · 次日A档三指标Δ客观结算,准确率定话语权 · ★一致率长期>0.8=回声室警示(evidence须私有数据)</div>
</div>
<p class="mut" style="margin:6px 0 0">当晚投票结算:五路投票5平(stage全冰点,方向与主判"平"一致,反对0未触发复议);主判=冰点·平(置信70),与五路stage同向——修复一日游后再入冰点无歧义(全池负期望第5日+量能跌破2万亿+医药宽度陷阱兑现)。次日A档三指标Δ客观结算(温度Δ±2/一进二Δ±3pp/溢价Δ±0.5pp),准确率定话语权。</p>
<h2>四 连板梯队</h2>
<div class="cols">
<div class="col hotc"><i style="height:9%"></i><b>1</b><span>3板</span></div>
<div class="col"><i style="height:90%"></i><b>10</b><span>2板</span></div>
<div class="col"><i style="height:100%"></i><b>43</b><span>首板</span></div>
</div><div class="colsub"><span>最高3板=汉森制药(中药,医药孤高标;昨4板金健米业断板)</span><span>2板10只(双鹭药业/键凯科技/中关村/贝瑞基因/科森科技/近岸蛋白/宇环数控/通鼎互联/深中华A/哈森股份5天4板)</span><span>首板43占79.6%·2板10只(医药系6只)=医药立高度但宽度收缩</span></div>
<div class="card"><p style="margin:0">梯队判读:高度3→3板(汉森制药3板中药,昨4板金健米业断板离场),2板10只(昨3只大扩)、首板43占79.6%——<b class="s-mid">高度塌缩+中位补涨</b>是冰点段"宽度散高度弱"典型。医药系连板6只(化学制药3+医疗服务1+生物制品1+中药1)立出高度(汉森3板)但宽度37→7大幅收缩(宽度陷阱兑现):医药从"宽度先行"退为"孤高标"。农业线(金健米业昨4板今日断板,万向德农/京粮控股/红四方/红棉股份跌停)虚胖第5次坐实崩塌。通信设备6只新候选线(通鼎互联2板)未确认。明日汉森制药能否晋级4板带出医药宽度=主线裁决点,但冰点段追高度=负期望。</p></div>
<h2>五 攻防 · 仓位总开关</h2>
<div class="card"><b>冰点段:防守空仓0成为主</b><div class="stages" style="margin-top:8px"><div class="st">主升<small>8-10成</small></div><div class="st">启动混沌<small>4-5成</small></div><div class="st on">防守<small>≤2成</small></div></div><div class="posmeter"><i style="width:0%"></i><em style="left:0%"></em></div><div class="posml"><span>0成</span><span>执行空仓0成 ▼</span><span>10成</span></div><p style="margin:8px 0 0">总开关锁定:防守空仓0成(总审C档防守·仓位0,全池负期望第5日空仓合法);五路全空仓0荐票(auction C/lhb C/theme C/logic C/limitup C)。禁:追高度(汉森3板孤高标)/追医药虚胖线(宽度37→7陷阱)/禁套利。明日观察:医药宽度修复(化学制药≥8)且汉森晋级4板+全池执1破50%+资金温度升破34分位→进攻窗口开启升B;否则维持防守等冰点走完。</p></div>
<h2>六 自主深挖 · 指标与阈值孵化</h2>
<div class="card"><b>清单应答</b><p style="margin:6px 0 0">今晚自主拓展scan的cycle域清单项=0条(无250日分位≥95/≤5极值项)——如实记录,无项不硬答;温度23.4为合成值非分位极值,已在段二判读card主动点评其冰点档位置(23.4冰点档&lt;25,触发防守环境规则)。</p></div>
<div class="obs"><div class="obs-head"><span class="obs-nm">冰点二次探底:修复一日游坐实(温度29.4→23.4/涨停79→54/量能跌破2万亿)</span><span class="obs-pos tag">探索 · 待次日结算</span></div><div class="obs-watch"><span class="obs-lab">判据</span>温度23.4跌破冰点线25+涨停54(-25)+量能18793亿跌破2万亿地板+全池执1胜率max45.8%无一&gt;50%(负期望第5日)=0820修复一日游坐实,但跌停13(非极端崩)+炸板率25%回落(封板质量修复)+一进二率18.4%/二进三率20%回升=局部改善信号。<b>今晚进度</b>:次日分辨"冰点延续"(温度&lt;25且涨停&lt;40)vs"修复再启动"(温度≥40+医药宽度≥8),沉淀"量能跌破2万亿+全池负期望是冰点防守硬约束,炸板率回落+晋级率回升只是局部修复不构成进攻条件"。</div></div>
<div class="card"><b>出页自检</b><p style="margin:6px 0 0">"用户明天问'冰点该空仓还是抄底?'"——段五总开关能直接回答(防守空仓0成,全池负期望第5日+量能跌破2万亿地板,冰点段禁套利);"温度为什么修复一日游后再入冰点?"——涨停79→54+量能跌破2万亿+医药宽度37→7陷阱兑现给出归因,但炸板率回落+晋级率回升说明是缩量退潮中的局部修复,非崩盘式冰点。</p></div>
<h2>七 我的认知迭代 · 最新</h2>
<div class="tl"><div class="tli"><b>08-21</b> 冰点二次探底坐实:0820"修复反抽"仅一日游——温度29.4→23.4跌破冰点线25、涨停79→54、量能20794→18793亿跌破2万亿地板、全池执1胜率max45.8%无一&gt;50%(负期望第5日)。关键认知:①医药"宽度先行·高度未立"(0820,36只全首板)→今日汉森制药3板立出高度但宽度37→7大幅收缩(宽度陷阱兑现),证明"宽度先行"的下一幕不是"高度接力"而是"宽度崩塌+孤高标"——冰点段宽度可以一夜间蒸发,高度是结果不是原因;②农业虚胖线第5次坐实(金健米业4板断板+4只跌停),宽度陷阱反复兑现=退潮段纯题材宽度不可信;③量能跌破2万亿地板是冰点防守硬约束,炸板率25%回落+一进二率18.4%回升只是局部修复,不构成进攻条件——防守空仓等"温度≥40+医药宽度≥8+全池执1破50%"三信号齐再谈进攻。</div></div>'''

io.open(os.path.join(L, 'cycle_body_20260821.html'), 'w', encoding='utf-8', newline='').write(html)
print('cycle body 写入完成, len =', len(html))
print('div配平:', html.count('<div') == html.count('</div>'))
print('h2 数:', len(re.findall(r'<h2[^>]*>', html)))
