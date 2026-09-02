# -*- coding: utf-8 -*-
"""limitup body 六段契约重构: 把子agent自造段名(质量Top8荐票/全量归位台账/训练库/负期望追踪)
映射到契约段名(涨停复盘/市场温度/归位台账/涨停质量库/自主深挖/认知迭代), 保留LLM原文+LEDGER台账"""
import json, re
L = r'D:\股票数据\市场数据\_学习'
J = L + r'\judgment_20260902.json'
d = json.load(open(J, encoding='utf-8'))
b = d['bodies']['limitup']

# 标准 h2 标题(对齐 module_render_limitup._H2_STD)
H1 = '<h2>一 涨停复盘 · Top5荐票<span class="hint">排序=命中规则数→抓龙率→质量分;发出版不可覆盖</span></h2>\n'
H2 = '<h2>二 市场温度 · 涨停生态<span class="hint">温度卡+档位成绩单(脚本产出勿改数)</span></h2>\n'
H3 = '<h2>三 归位台账<span class="hint">LEDGER=台账脚本注入;题材归位=全系统唯一真源</span></h2>\n'
H4 = '<h2>四 涨停质量库 · 因子与规则<span class="hint">因子表/规则榜/分板胜率库/甜点=脚本产出折叠;LLM逐条说明见下</span></h2>\n'
H5 = '<h2>五 自主深挖 · 因子与归位孵化</h2>\n'
H6 = '<h2>六 我的认知迭代 · 最新</h2>\n'

def h2end(s, kw):
    i = s.find('<h2>%s' % kw)
    if i < 0:
        return -1
    e = s.find('</h2>', i)
    return e + 5 if e > 0 else -1

# 定位各段
p_head = b.find('<h2>一 质量Top8荐票')
p_h2_1 = b.find('<h2>一 质量Top8荐票')
p_h2_2 = b.find('<h2>二 全量归位台账')
p_led = b.find('<!--LEDGER-->')
p_led_end = b.find('<!--/LEDGER-->') + len('<!--/LEDGER-->')
p_h2_3 = b.find('<h2>三 训练库')
p_h2_4 = b.find('<h2>四 负期望追踪')
p_h2_5 = b.find('<h2>五 自主深挖')
p_h2_6 = b.find('<h2>六 我的认知迭代')

print('位置: head=%d 一=%d 二=%d LEDGER=%d LEDGERend=%d 三=%d 四=%d 五=%d 六=%d' % (
    p_head, p_h2_1, p_h2_2, p_led, p_led_end, p_h2_3, p_h2_4, p_h2_5, p_h2_6))

# 提取内容(去旧 h2 标签)
head = b[:p_h2_1]
sec1 = b[h2end(b, '一 质量Top8荐票') : p_h2_2]          # 洞察卡内容
sec2_intro = b[h2end(b, '二 全量归位台账') : p_led]      # 归位台账引语
ledger = b[p_led : p_led_end]                              # LEDGER 台账
sec2_tail = b[p_led_end : p_h2_3]                          # LEDGER 后残留
sec3 = b[h2end(b, '三 训练库') : p_h2_4]                  # 训练库内容
sec4 = b[h2end(b, '四 负期望追踪') : p_h2_5]              # 负期望内容
sec5 = b[h2end(b, '五 自主深挖') : p_h2_6]                # 自主深挖
sec6 = b[h2end(b, '六 我的认知迭代') :]                   # 认知迭代

# 重组
new = (head
       + H1 + sec1
       + H2
       + H3 + sec2_intro + ledger + sec2_tail
       + H4 + sec3 + sec4
       + H5 + sec5
       + H6 + sec6)

d['bodies']['limitup'] = new
json.dump(d, open(J, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 验证
print('重组后: div开%d div闭%d h2=%d LEDGER=%d' % (new.count('<div'), new.count('</div>'), new.count('<h2'), new.count('<!--LEDGER-->')))
for m in re.finditer(r'<h2[^>]*>', new):
    txt = re.sub(r'<[^>]+>', '', m.group(0))
    print('  h2:', txt[:44])
