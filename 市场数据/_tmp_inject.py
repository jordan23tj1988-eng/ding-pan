# -*- coding: utf-8 -*-
"""注入五路 body + 补齐锚点 + 填 ticker/一句话/archive_body 到 judgment_20260902.json"""
import io, json, os, re
L = r'D:\股票数据\市场数据\_学习'
J = os.path.join(L, 'judgment_20260902.json')
d = '20260902'

def rd(r):
    return io.open(os.path.join(L, f'{r}_body_20260902.html'), encoding='utf-8').read()

# 读五路 body
bodies = {}
for r in ['auction','lhb','theme','logic','limitup']:
    b = rd(r)
    # 补齐锚点
    if r == 'lhb':
        if '<!--LHBLEDGER-->' not in b:
            # 在 <h2>三 龙虎榜台账</h2> 后插入空锚对
            m = re.search(r'(<h2>三 龙虎榜台账.*?</h2>)', b)
            if m:
                b = b.replace(m.group(1), m.group(1) + '\n<!--LHBLEDGER--><!--/LHBLEDGER-->\n')
        if '<!--FUNDTEMP-->' not in b:
            m = re.search(r'(<h2>二 资金温度.*?</h2>)', b)
            if m:
                b = b.replace(m.group(1), m.group(1) + '\n<!--FUNDTEMP--><!--/FUNDTEMP-->\n')
    if r == 'auction':
        if '<!--POOLLEDGER-->' not in b:
            m = re.search(r'(<h2>二 昨日池今日终结算.*?</h2>)', b)
            if m:
                b = b.replace(m.group(1), m.group(1) + '\n<!--POOLLEDGER--><!--/POOLLEDGER-->\n')
    bodies[r] = b

# 载入 judgment 骨架
j = json.load(io.open(J, encoding='utf-8'))
for r, b in bodies.items():
    j['bodies'][r] = b

# 填 ticker + 一句话 + archive_body
j['更新label'] = '20260902 复盘'
j['一句话'] = '退潮第2日：昨日回暖被证伪为一日脉冲，温度63.1→30.5暴跌32.6点(中档→偏冷)，涨停83→52、跌停0→8、炸板率6.7%→22.4%、最高板7→4断层、量能20334→17912亿跌破2万亿；五维退潮共振(竞价追池套/资金3分位极冷/无主线第7日/业绩腿静默第5次/全池负期望第13日)，五路全C档空仓防守，总裁决C档(置信80)'
j['ticker'] = ('<div class="ticker"><div class="in"><div class="grp">'
               '<span>量能 <b class="a">1.79万亿</b></span>'
               '<span>涨停 <b class="u">52</b> / 跌停 <b class="d">8</b></span>'
               '<span>炸板 <b>15</b>·炸板率 <b>22.4%</b></span>'
               '<span>最高 <b>4</b>板</span>'
               '<span>温度 <b class="d">30.5</b> 偏冷</span>'
               '<span>2进3率 <b>44.4%</b></span>'
               '<span>1进2率 <b>10.8%</b></span>'
               '<span>主线 <b>无(第7日)</b></span>'
               '<span>档位 <b class="d">C 防守空仓</b></span>'
               '</div></div></div>')
j['archive_body'] = ('退潮第2日。昨日"回暖第1日"被今日全面证伪为一日脉冲：'
                     '竞价温度63.1→30.5(-32.6)、涨停83→52、跌停0→8、炸板率6.7%→22.4%、'
                     '最高板7→4断层、量能2.03万亿→1.79万亿跌破2万亿。'
                     '五维退潮共振：竞价回暖追池套(0901池-1.48%)、资金温度3分位极冷(单日脉冲第4次)、'
                     '无主线第7日、业绩腿静默第5次(T-1交叉首次归零)、全池负期望第13日(执1max45.4%<50%)。'
                     '五路全C档空仓防守，总裁决C档(置信80)。保留观察票：auction观2(道明光学/香溢融通)、'
                     'lhb观1(博云新材)、theme观3(集泰股份/国芳集团/欢瑞世纪)、limitup观3(飞龙股份/天禾股份/力鼎光电)。')

io.open(J, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1))
j2 = json.load(io.open(J, encoding='utf-8'))
print('注入完成 bodies keys:', list(j2['bodies'].keys()))
for r, b in j2['bodies'].items():
    print(f'  {r}: {len(b)} 字节')
print('锚点检查: LEDGER=%d LHBLEDGER=%d POOLLEDGER=%d FUNDTEMP=%d' % (
    j2['bodies']['limitup'].count('<!--LEDGER-->'),
    j2['bodies']['lhb'].count('<!--LHBLEDGER-->'),
    j2['bodies']['auction'].count('<!--POOLLEDGER-->'),
    j2['bodies']['lhb'].count('<!--FUNDTEMP-->')))
