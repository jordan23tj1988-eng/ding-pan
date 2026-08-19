# -*- coding: utf-8 -*-
"""补产 cycle_body_20260818.html(七段) + 注入 judgment_20260818.json bodies.cycle
2026-08-18 晚补跑: cycle 路漏产 body 致页面断档,数据源全部 ≤0818 收盘,零后视镜零编造。"""
import json, os, shutil

R = r'D:\股票数据\市场数据'
L = os.path.join(R, '_学习')

# 段二: 权威脚本产物(情绪先行指标.py --card 已生成)
card2 = open(os.path.join(L, '先行指标卡_20260818.html'), encoding='utf-8').read().strip()

rowA = '''<div class="rowA">
<div class="hero"><div class="kick">Cycle · 周期与情绪 · 截至 2026-08-18 收盘</div><h1>退潮段:温度59.5→44.5单日-15转偏冷,<em>普涨首板潮次日温和退潮,防守为主</em></h1><p>量能台阶→先行指标三窗→情绪五阶段(五路投票)→连板梯队→攻防总开关,五件事定仓位。</p><div class="stance"><span class="pill warn">周期 · <b class="s-mid">退潮</b></span><span class="pill ">量能 · <b>2.40万亿弱修档</b></span><span class="pill hot"><b class="s-ok">⚠退潮段 · 防守为主</b></span></div></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M3 17l5-6 4 4 6-8 3 4"/></svg></span><span class="chip2 c-half">弱修</span></div><span class="lab">两市量能</span><span class="big" data-v="2.40" data-dec="2">2.40<span style="font-size:15px">万亿</span></span><span class="sub2">2.39→2.40微增+0.4%(&lt;3.0弱修档);量平价缩转退潮</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span><span class="chip2 c-cool">退潮·降</span></div><span class="lab">情绪阶段(主判)</span><span class="big" style="font-size:20px">退潮·降</span><span class="sub2">五路投票5降(0反对);主判退潮·降(置信65)</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span><span class="chip2 c-cool">偏冷</span></div><span class="lab">市场温度 · 250日分位</span><span class="big" data-v="44.5" data-dec="1">44.5</span><div class="gauge"><div class="gtrack"><i class="gmark" style="left:44.5%"></i></div><div class="gl"><span>冰点</span><span>偏冷</span><span>中性</span><span>偏热</span><span>过热</span></div></div><span class="sub2">昨59.5-15.0转偏冷;偏冷档=退潮,距冰点&lt;25尚有距离</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M4 20h16M6 16l4-8 4 5 4-9"/></svg></span><span class="chip2 c-cool">空仓0成</span></div><span class="lab">执行仓位上限</span><span class="big" style="font-size:20px">空仓0成</span><span class="sub2">总审B中性偏防守·仓位0;退潮段空仓为主,禁套利</span></div>
</div>'''

sec1 = '''<h2>一 量能台阶 · 我站在哪一阶</h2>
<div class="steps">
<div class="step dim"><span class="sr">≥3.8</span><span class="sn">主升2确认<small>放量突破</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.5~3.8</span><span class="sn">突破压力<small>需增量</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.3~3.5</span><span class="sn">强修<small>量能承接</small></span><span class="sd"></span></div>
<div class="step dim"><span class="sr">3.0~3.3</span><span class="sn">过渡<small>量能中枢</small></span><span class="sd"></span></div>
<div class="step cur"><span class="sr">&lt;3.0</span><span class="sn">弱修<small>缩量分歧</small></span><span class="sd"><span class="dayc now">08-18 2.40</span><span class="dayc">08-17 2.39</span><span class="dayc">08-14 2.14</span></span></div>
</div>
<div class="hint">量能2.40万亿落"弱修"档,较昨2.39万亿微增+0.01万亿基本持平——量能守住2万亿平台但未抬升;较08-14的2.14万亿放量+0.26万亿、距3.0过渡档尚有0.60万亿差距;量平价缩(涨停106→79回落+炸板率10.2%→22.5%翻倍)=启动段夭折转退潮,资金只退不追高度。A档:米开量能台阶换算(腾讯替代源)。</div>'''

sec2 = '<h2>二 先行指标 · 三窗触发器</h2>' + card2

sec3 = '''<h2>三 情绪五阶段 · 五路周期投票</h2>
<div class="stages">
<div class="st">冰点<small>温度44.5未至</small></div>
<div class="st">启动<small>昨已结束</small></div>
<div class="st">发酵·主升<small>主线AI缩圈未成</small></div>
<div class="st">高潮<small>封板率77.5%已破80%</small></div>
<div class="st on">退潮<small>温度44.5·涨停79</small></div></div>
<div style="margin:10px 0;padding:12px 14px;background:#14171e;border:1px solid #2a2f3a;border-radius:10px">
<div style="font-size:11px;letter-spacing:2px;color:#d9a441;font-family:monospace">五路周期投票 · 主判=退潮·降</div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">①竞价 <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">退潮·降</b><br><span style="color:#5c6674">置信58·准确率1/6</span></div>
<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">②席位 <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">退潮·降</b><br><span style="color:#5c6674">置信60·准确率1/6</span></div>
<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">③题材 <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">退潮·降</b><br><span style="color:#5c6674">置信60·准确率1/4</span></div>
<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">④产逻 <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">退潮·降</b><br><span style="color:#5c6674">置信57·准确率2/6</span></div>
<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;font-size:11.5px;color:#d8dee9">⑤质量 <span style="color:#4caf7d">同意</span><br><b style="color:#d8dee9">退潮·降</b><br><span style="color:#5c6674">置信70·准确率1/6</span></div>
</div>
<div style="margin-top:8px;color:#5c6674;font-size:11px">分歧未达阈值(当日≥3/5或加权≥0.60复议;连续3日≥2路同向重做) · 次日A档三指标Δ客观结算,准确率定话语权 · ★一致率长期>0.8=回声室警示(evidence须私有数据)</div>
</div>
<p class="mut" style="margin:6px 0 0">当晚投票结算:五路投票5降(stage全退潮,方向与主判"降"一致,反对0未触发复议);主判=退潮·降(置信65),与五路stage同向——启动段夭折转退潮无歧义。次日A档三指标Δ客观结算(温度Δ±2/一进二Δ±3pp/溢价Δ±0.5pp),准确率定话语权。</p>'''

sec4 = '''<h2>四 连板梯队</h2>
<div class="cols">
<div class="col hotc"><i style="height:4%"></i><b>1</b><span>4板</span></div>
<div class="col"><i style="height:15%"></i><b>4</b><span>3板</span></div>
<div class="col"><i style="height:48%"></i><b>13</b><span>2板</span></div>
<div class="col"><i style="height:100%"></i><b>61</b><span>首板</span></div>
</div><div class="colsub"><span>最高4板=神奇制药(化学制药,医药孤标;昨4板天洋新材/金螳螂/澳洋健康全断)</span><span>3板4只(桂发祥/正裕工业/旭光电子/中石科技)</span><span>首板61占77.2%·2板13只(农发种业/金健米业等农业占多)=低位补涨但高度未立</span></div>
<div class="card"><p style="margin:0">梯队判读:高度4→4板维持(神奇制药4板孤标接棒,昨4板天洋新材/金螳螂/澳洋健康全断板离场),3板4只、2板13只(昨8只增加)、首板61占77.2%——<b class="s-mid">高度真空+中位补涨</b>是退潮段"宽度散高度弱"典型。农业2板多只(农发种业/金健米业/京粮控股/天山生物/红四方)但纯正种业龙头(隆平/登海)仅1板=宽度陷阱虚胖;医药神奇制药4板孤标。明日神奇制药能否晋级5板纯正高标=主线高度真立判据,但退潮段追高度=负期望。</p></div>'''

sec5 = '''<h2>五 攻防 · 仓位总开关</h2>
<div class="card"><b>退潮段:防守空仓0成为主</b><div class="stages" style="margin-top:8px"><div class="st">主升<small>8-10成</small></div><div class="st">启动混沌<small>4-5成</small></div><div class="st on">防守<small>≤2成</small></div></div><div class="posmeter"><i style="width:5%"></i><em style="left:0%"></em></div><div class="posml"><span>0成</span><span>执行空仓0成 ▼</span><span>10成</span></div><p style="margin:8px 0 0">总开关锁定:防守空仓0成(总审B中性偏防守·仓位0,退潮段空仓合法);五路全空仓0荐票(auction B/lhb C/theme C/logic B/limitup B实质全空仓)。禁:追首板/追农业虚胖线(宽22但纯正种业仅1板)/追4板神奇制药(医药孤标)。明日观察:农业立3板纯正种业龙头+全池执1破50%+资金温度升破34分位→进攻窗口开启升A;否则维持防守等退潮走完。</p></div>'''

sec6 = '''<h2>六 自主深挖 · 指标与阈值孵化</h2>
<div class="card"><b>清单应答</b><p style="margin:6px 0 0">今晚自主拓展scan的cycle域清单项=0条(无250日分位≥95/≤5极值项)——如实记录,无项不硬答;温度44.5为合成值非分位极值,已在段二判读card主动点评其偏冷档位置(44.5偏冷档,不触发冰点&lt;25进攻/过热≥85回避两端环境规则)。</p></div>
<div class="obs"><div class="obs-head"><span class="obs-nm">封板率77.5%跌破80%退潮线但温度仅偏冷未冰点</span><span class="obs-pos tag">探索 · 待次日结算</span></div><div class="obs-watch"><span class="obs-lab">判据</span>封板率89.8%→77.5%跌破80%+涨停106→79+炸板率翻倍=退潮坐实,但跌停5(非崩)+温度44.5(未冰点)+一进二率20.4%回升+二进三率80%中位板接力未断链=退潮温和非冰点。<b>今晚进度</b>:次日分辨"退潮走完"(温度逼近冰点&lt;25且跌停≥两位数)vs"退潮中继反弹"(温度企稳+主线立高度),沉淀"封板率跌破80%是退潮确认线,但退潮烈度看跌停数+一进二率是否断链而非只看封板率"。</div></div>
<div class="card"><b>出页自检</b><p style="margin:6px 0 0">"用户明天问'退潮该空仓还是抢反弹?'"——段五总开关能直接回答(防守空仓0成,退潮段禁套利);"温度为什么单日-15转偏冷?"——涨停106→79+炸板率10.2%→22.5%翻倍+封板率跌破80%给出归因,但跌停5+一进二率20.4%回升说明退潮温和,是普涨首板潮次日分化兑现而非崩盘式退潮。</p></div>'''

sec7 = '''<h2>七 我的认知迭代 · 最新</h2>
<div class="tl"><div class="tli"><b>08-18</b> 启动段"普涨首板潮"次日温和退潮坐实——0817总审预判"次日分化日概率大"五维同向精准兑现(封板率89.8%→77.5%/炸板率10.2%→22.5%翻倍/涨停106→79/温度59.5→44.5/封板总额96.1→58.4亿-38%),退潮确认线=封板率跌破80%。但退潮烈度温和(跌停5非崩/涨停79未腰斩/一进二率20.4%回升/二进三率80%中位板未断链/温度44.5未冰点)故非C档冰点防守,判"退潮温和"三判据=跌停数+一进二率断链否+温度距冰点,而非只看封板率。主线真空(AI算力缩圈-63%退坡+农业22只宽度第一但纯正种业隆平登海仅1板=宽度陷阱虚胖+医药神奇制药4板孤标)vs资金5分位极冷(北向41.1→18.0亿腰斩/机构10.4→6.1亿)双杀,五路全空仓0荐票趋同防守有据(全池负期望max45.8%+业绩零共振第5日)。</div></div>'''

body = rowA + '\n' + sec1 + '\n' + sec2 + '\n' + sec3 + '\n' + sec4 + '\n' + sec5 + '\n' + sec6 + '\n' + sec7

# ── 验证 ──
d_open = body.count('<div')
d_close = body.count('</div>')
h2 = body.count('<h2>')
print(f'[验证] div开={d_open} div闭={d_close} 配平={d_open==d_close} h2段数={h2}')
assert d_open == d_close, f'div不配平: 开{d_open} 闭{d_close}'
assert h2 == 7, f'h2段数={h2} 应为7'

# 写 body 文件
body_path = os.path.join(L, 'cycle_body_20260818.html')
open(body_path, 'w', encoding='utf-8', newline='\n').write(body)
print(f'[写] {body_path} ({len(body)} 字符)')

# 注入 judgment
jud_path = os.path.join(L, 'judgment_20260818.json')
bak = jud_path + '.bak_cycle'
shutil.copy2(jud_path, bak)
d = json.load(open(jud_path, encoding='utf-8'))
d['bodies']['cycle'] = body
json.dump(d, open(jud_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'[注入] bodies.cycle 已写入 ({len(body)} 字符), 备份={bak}')
print(f'[注入后] bodies keys = {list(d["bodies"].keys())}')
