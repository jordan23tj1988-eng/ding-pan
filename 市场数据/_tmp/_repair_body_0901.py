# -*- coding: utf-8 -*-
"""2026-09-01 judgment body 修复脚本
A. limitup: 补 head 区(rowA>hero+kpi4卡, 8/31模板换9/1权威数据) + h2一 Top8→Top5 + 补"二 市场温度·涨停生态"段
B. lhb: 补"二 资金温度·席位生态"段名(h2+hint方法说明, 内容由渲染器机器FUNDTEMP卡承载)
原则: 零编造(全部数字回源 _市场温度表.json/_情绪先行指标.json/20260901/zt_pool.csv/limitup判断_20260901.json)
     不触碰 LEDGER/LHBLEDGER 锚段(机器注入区保留), 改后跑注入脚本保险。
"""
import json, shutil, os, re, sys

LEARN = r'D:\股票数据\市场数据\_学习'
JP = os.path.join(LEARN, 'judgment_20260901.json')

# ---------- 1. 备份 ----------
bak = JP + '.bak_0901fix'
if not os.path.exists(bak):
    shutil.copy2(JP, bak)
print('[1] 备份 ->', os.path.basename(bak))

j = json.load(open(JP, encoding='utf-8'))
b = j['bodies']
lu = b['limitup']

# ---------- 2. limitup head 区(9/1 权威数据, 8/31 模板结构) ----------
HEAD = '''<div class="rowA">
<div class="hero"><div class="kick">Limitup · 涨停复盘 · 第5路 · 截至 2026-09-01 收盘</div><h1>情绪回暖×承接资金未跟背离:涨停83/温度63.1+10.5回升/炸板率6.7%大降/最高板7抬升,<em>全池负期望第12日『未终结』(执1max45.9%·83/83命中0规)·承接资金『质量型修复未兑现』(封板率93.3%重回80%但单票封单max3.53亿连续3日下移·封单≥4亿家数0)</em></h1><p>温度63.1中性(昨52.6,+10.5回升);涨停83(昨88,-5)/跌停0(昨11,-11)/炸板6(炸板率6.7%,昨25.4%大降-18.7pp)/封板率93.3%(昨74.6%重回80%+,但回升靠炸板30→6大降=抛压枯竭非承接回归)/最高板7=海鸥住工002084(重组·控制权变更,7连板,09:25真一字,接棒自身6板晋级)/封板总额78.2亿(昨91.4亿,-14.4%)/量能20334亿(昨21310亿,缩量-4.6%,仍站2万亿)。全池负期望第12日且『未终结』:83只执1胜率max仅45.9%(一鸣食品605179)无一&gt;50%、执1均涨池均-0.36%,<b>命中规则≥1只=0只(昨1只)</b>、命中≥3只=0只。承接资金分叉:封板率重回80%+但单票封单max5.30→4.59→3.53亿连续第3日下移+封单≥4亿家数0(昨2只)=广撒网回补未兑现为质量型大单承接。档位C防守(维持),置信度74。</p><p>归位(83/83全归位,待归位0):A1/B82/C0(THS涨停原因停更20260815第13日,A档=连板延续手写1只:海鸥住工,余82只为行业兜底B档)</p><div class="stance"><span class="pill cold">C档·防守</span><span class="pill warn">情绪回暖·炸板率6.7%大降·封板率93.3%重回80%</span><span class="pill hot">负期望第12日·单票封单max3.53亿连续3日下移</span></div></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M7 20V10m5 10V4m5 16v-7"/></svg></span><span class="chip2 c-miss">回落</span></div><span class="lab">涨停数(剔ST)</span><span class="big" data-v="83">83</span><span class="sub2">昨88-5;炸板6·炸板率6.7%大降;封板率93.3%重回80%</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M5 21V9l7-6 7 6v12"/></svg></span><span class="chip2 c-hit">改善</span></div><span class="lab">炸板数</span><span class="big" data-v="6">6</span><span class="sub2">炸板率6.7%(昨25.4%,-18.7pp);回封40(昨43,-3)</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/></svg></span><span class="chip2 c-miss">收缩</span></div><span class="lab">封板总额</span><span class="big" data-v="78.2">78.2亿</span><span class="sub2">昨91.4亿-14.4%;单票封单max3.53亿(福建金森)连3日下移·封单≥4亿0家</span></div>
<div class="kpi"><div class="top"><span class="ico"><svg viewBox="0 0 24 24"><path d="M12 3v10.3a4 4 0 1 0 2 0V3z"/><circle cx="13" cy="17" r="1.6"/></svg></span><span class="chip2 c-hit">回暖</span></div><span class="lab">市场温度</span><span class="big" data-v="63.1">63.1</span><span class="sub2">昨52.6+10.5;中性档(45-65)不触发冰点/过热规则;量能20334亿</span></div>
</div>

'''

# ---------- 3. limitup h2一 标题 Top8→Top5 ----------
old_h2 = '<h2>一 涨停复盘 · Top8荐票'
new_h2 = '<h2>一 涨停复盘 · Top5荐票'
assert old_h2 in lu, 'limitup h2一 Top8 锚未找到'
lu = lu.replace(old_h2, new_h2, 1)
print('[3] limitup h2一 Top8→Top5 已替换')

# ---------- 4. limitup 补"二 市场温度 · 涨停生态"段(插在 h2一 段尾/h2三 前) ----------
SEC2_LU = '''<h2>二 市场温度 · 涨停生态<span class="hint">方法:温度卡由市场温度.py权威生成(剔ST对齐THS口径),本路只引用不重算;涨停/炸板/跌停/炸板率/最高板/回封/二板加/成交额/封板总额一律回源_市场温度表.json,梯队与首封分桶另用当日zt_pool.csv独立自算做三源交叉核对,不一致即报</span></h2><div class="card"><b>洞察(agent)</b><p>温度<b>63.1中性</b>(昨52.6,+10.5回升),涨停83(昨88,-5)/跌停<b>0</b>(昨11,-11)/炸板6(炸板率<b>6.7%</b>,昨25.4%大降-18.7pp)/封板率<b>93.3%</b>(昨74.6%重回80%+,但靠炸板30→6大降=抛压枯竭非承接回归)/成交额<b>20334亿</b>(昨21310亿,缩量-4.6%,仍站2万亿)/封板总额<b>78.2亿</b>(昨91.4亿,-14.4%)/回封40(昨43,-3)。梯队自算<b>{1:65, 2:9, 3:5, 4:1, 6:2, 7:1}</b>=7板海鸥住工002084(家居用品,09:25真一字,炸0次封单1.72亿)+6板2只(捷荣技术002855消费电子09:30炸5次/万向德农600371种业09:32炸2次统计11/8)+4板新赛股份600540(种植业,09:30炸0封单2.01亿)+3板5只(福建金森002679林业09:25一字封单3.53亿全池最高/竞业达003005IT服务09:25一字/时代出版600551出版炸9次/国芳集团601086零售09:31/我爱我家000560地产09:33炸5次)+2板9只+首板65只(78.3%),与温度表梯队/zt_pool.csv三源一致;二板加18。晋级率(引擎_情绪先行指标.json)=一进二率<b>18.4%</b>(昨12.5%回升)/二进三率<b>80.0%</b>(昨25.0%大升)/高度晋级率<b>63.6%</b>(昨35.7%大升,高度板接棒);跌停0=核按钮率0(昨3.7%回落);昨日涨停溢价=<b>null</b>(引擎字段空,当日未产,不编造)</p></div>

'''
i3 = lu.find('<h2>三')
assert i3 > 0, 'limitup h2三 锚未找到'
lu = lu[:i3] + SEC2_LU + lu[i3:]
print('[4] limitup 补"二 市场温度"段 已插入(在 h2三 前)')

# ---------- 5. limitup head 区插入(body 开头, h2一 前) ----------
assert lu.startswith('<h2>一'), 'limitup body 应以 h2一 开头(无 head 区, 符合修复前提)'
lu = HEAD + lu
print('[5] limitup head 区已插入(body 开头)')

# ---------- 6. lhb 补"二 资金温度 · 席位生态"段名(h2+hint, 内容由机器 FUNDTEMP 卡承载) ----------
lb = b['lhb']
SEC2_LHB = '''<h2>二 资金温度 · 席位生态<span class="hint">方法:资金温度卡由模块渲染器机器注入(FUNDTEMP锚,回源_资金温度.json),本路只引用不重算;S/A出手/机构净买/席位分档见段三台账与段四分档库</span></h2>
'''
i3l = lb.find('<h2>三')
assert i3l > 0, 'lhb h2三 锚未找到'
lb = lb[:i3l] + SEC2_LHB + lb[i3l:]
print('[6] lhb 补"二 资金温度"段名 已插入(h2三 前)')

# ---------- 7. 写回 + 校验 ----------
b['limitup'] = lu
b['lhb'] = lb
j['bodies'] = b
with open(JP, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(j, f, ensure_ascii=False, indent=1)

# 校验
j2 = json.load(open(JP, encoding='utf-8'))
for page in ['limitup', 'lhb', 'logic']:
    body = j2['bodies'][page]
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.S)
    h2s = [re.sub(r'<[^>]+>', '', h).strip()[:30] for h in h2s]
    od = body.count('<div') - body.count('</div>')
    print(f'  校验 {page}: {len(body)//1024}KB h2={len(h2s)} div差={od} {h2s}')
    assert od == 0, f'{page} div 不配平'
lu2 = j2['bodies']['limitup']
assert lu2.startswith('<div class="rowA">'), 'head 区插入失败'
assert '一 涨停复盘 · Top5荐票' in lu2 and 'Top8' not in lu2[:6000], 'Top8→Top5 替换失败'
print('[7] 写回完成, 校验全过')
