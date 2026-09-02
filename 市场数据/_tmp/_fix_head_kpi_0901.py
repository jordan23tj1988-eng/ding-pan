# -*- coding: utf-8 -*-
"""2026-09-01 judgment body head 区补全: lhb 2→4 kpi(黄金版结构), logic 2→4 kpi
数据全部来自当日 head 段/判断文件已述事实, 零编造; 结构对齐 8/31 黄金版模板(ico/chip2/lab/big/sub2)。
"""
import json, re, shutil, os

JP = r'D:\股票数据\市场数据\_学习\judgment_20260901.json'
bak = JP + '.bak_headfix'
if not os.path.exists(bak):
    shutil.copy2(JP, bak)

j = json.load(open(JP, encoding='utf-8'))

SVG_LOCK = '<svg viewBox="0 0 24 24"><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M8 8V6a4 4 0 0 1 8 0v2"/></svg>'
SVG_STAR = '<svg viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg>'
SVG_TEMP = '<svg viewBox="0 0 24 24"><path d="M12 3v3M12 3c3 3 6 5 6 9a6 6 0 0 1-12 0c0-4 3-6 6-9z"/></svg>'
SVG_CLOCK = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>'

def kpi(ico, chip_cls, chip_txt, lab, big, sub2):
    return (f'<div class="kpi"><div class="top"><span class="ico">{ico}</span>'
            f'<span class="chip2 {chip_cls}">{chip_txt}</span></div>'
            f'<span class="lab">{lab}</span><span class="big">{big}</span>'
            f'<span class="sub2">{sub2}</span></div>')

# ============ lhb: 替换 2 张 kpi-h 卡 -> 4 张黄金版卡 ============
lhb = j['bodies']['lhb']
i0 = lhb.find('<h2>')
head = lhb[:i0]
body_rest = lhb[i0:]
# hero 区到 stance 结束(第二个</div>后的 </div> 是 rowA 闭?) 取 hero+stance 完整块:
hero_end = head.find('</div></div>')  # stance 块结束
hero_end2 = head.find('</div>', hero_end + 1)  # rowA 闭
assert hero_end > 0 and hero_end2 > hero_end, 'lhb head 结构异常'
hero_block = head[:hero_end2]  # rowA 开 + hero 全部(不含 rowA 闭)
print('lhb hero_block 尾:', hero_block[-80:])

kpi_lhb = [
    kpi(SVG_LOCK, 'c-miss', '机构', '机构买入',
        '7.9亿',
        '机构25席7.9亿(昨23席10.2亿,<b>-22%</b>)·北向28席29.7亿(昨28席32.6亿,-9%)·量化12席7.7亿(昨8席9.0亿,-14%)·总金额87.8亿(昨98.9亿,-11%)'),
    kpi(SVG_STAR, 'c-miss', 'S/A出手', 'S档出手',
        '4席次',
        '去名称变体后<b>独立S席位4个</b>(0831为6席):唯一干净进攻=杭州庆春路(n=25非小样本60.0%)→芒果超媒300413净买+1.88亿 · 顶级量化降档:开源西安西大街A→B/武汉紫阳东路A→B'),
    kpi(SVG_TEMP, 'c-miss', '温度分位', '资金温度',
        '27分位',
        '昨42分位→今日27分位(<b>-15跌破34</b>)，三档进攻窗条件第1项(温度≥34)不再满足，总金额98.9→87.8亿(-11%)'),
    kpi(SVG_CLOCK, 'c-half', '知名游资', '游资接棒',
        '124席',
        '知名游资124席37.4亿(昨139席35.8亿,<b>席次-15但额+4.5%</b>)·分歧承接未见同步放大,配置盘回流未获游资接棒确认'),
]
new_lhb = hero_block + ''.join(kpi_lhb) + '</div>' + body_rest
j['bodies']['lhb'] = new_lhb
print('lhb head kpi 数:', new_lhb[:new_lhb.find('<h2>')].count('class="kpi"'))

# ============ logic: 追加 2 张 kpi -> 4 张 ============
lg = j['bodies']['logic']
i0 = lg.find('<h2>')
head_l = lg[:i0]
body_rest_l = lg[i0:]
# 在最后一张 kpi 后、rowA 闭 </div> 前插入
# head_l 结构: rowA>hero+stance+2kpi+</div>(rowA闭)
# 找倒数第二个 </div> 前的 kpi 结束位置: 直接找 rowA 闭
# rowA 闭 = head_l 最后一个 '</div>' (hero/kpi 之后)
last_div = head_l.rfind('</div>')
assert last_div > 0, 'logic head 结构异常'
inner = head_l[:last_div]  # 不含 rowA 闭
kpi_logic_extra = [
    kpi(SVG_TEMP, 'c-half', '存储/HBM', '存储环节涨停',
        '0只',
        'HBM/存储(江波龙301308/德明利001309/兆易创新603986)+分销盈方微000670 <b>0涨停</b>&lt;2，业绩腿传导未通'),
    kpi(SVG_CLOCK, 'c-acc', '战绩', '本路累计战绩',
        '21.4%',
        '3/14胜率·均收-1.95%(五路最弱)，空仓防守纪律=业绩腿静默第4次坐实不硬做'),
]
new_lg = inner + ''.join(kpi_logic_extra) + '</div>' + body_rest_l
j['bodies']['logic'] = new_lg
print('logic head kpi 数:', new_lg[:new_lg.find('<h2>')].count('class="kpi"'))

json.dump(j, open(JP, 'w', encoding='utf-8'), ensure_ascii=False)
print('judgment 已写回 (备份: %s)' % os.path.basename(bak))
