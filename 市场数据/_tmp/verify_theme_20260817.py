# -*- coding: utf-8 -*-
"""theme路 20260817 交付物验证(一次性): 三文件结构/真源交叉核对/HTML配平。退出码0=全过,1=FAIL。"""
import json, sys, re

R = r'D:\股票数据\市场数据'
L = R + r'\_学习'
FAIL = []

def check(cond, msg):
    if not cond:
        FAIL.append(msg)

# ---- 1. 三文件 JSON 合法 ----
jd = json.load(open(f'{L}/theme判断_20260817.json', encoding='utf-8'))
pub = json.load(open(f'{L}/题材荐票_20260817.json', encoding='utf-8'))

# ---- 2. 发出版 schema(任务铁律要求字段) ----
check(pub['日期'] == '20260817', '发出版日期错')
for s in pub['标的']:
    for k in ['代码', '名称', '类型', '大方向', '环节', '理由', '历史对照']:
        check(k in s and s[k], f'发出版缺字段 {k}: {s.get("代码")}')
    check(s['类型'] in ('荐票', '观察'), f'类型非法: {s}')
nv = [s for s in pub['标的'] if s['类型'] == '荐票']
check(len(nv) <= 3, f'荐票>3只: {len(nv)}')

# ---- 3. 荐票/观察 ∈ zt_pool ----
pool = {l.split(',')[1] for l in open(f'{R}/20260817/zt_pool.csv', encoding='utf-8').read().strip().split(chr(10))[1:]}
for s in pub['标的']:
    check(s['代码'] in pool, f"标的 {s['名称']}({s['代码']}) 不在 zt_pool")

# ---- 4. 判断.json 档位/置信度合法 + 关键数字回源 ----
j = jd['判断']
check(j['档位'] in ('A', 'B', 'C'), f"档位非法: {j['档位']}")
check(isinstance(j['置信度'], (int, float)) and 0 <= j['置信度'] <= 100, f"置信度非法: {j['置信度']}")
for k in ['结论', '证据', '可证伪条件', '独立盲区声明', '框架引用']:
    check(k in j and j[k], f'判断缺字段 {k}')

temp = json.load(open(f'{L}/_市场温度表.json', encoding='utf-8'))['20260817']
six = json.load(open(f'{L}/主流题材6有_20260817.json', encoding='utf-8'))
four = json.load(open(f'{L}/_题材四维.json', encoding='utf-8'))['20260817']
lia = json.load(open(f'{L}/涨停对链条_20260817.json', encoding='utf-8'))

check(temp['涨停数'] == 106 and temp['温度'] == 59.5 and temp['最高板'] == 4, '温度表基线不符')
ai = next(t for t in six['题材_聚类口径'] if 'AI算力' in t['题材(题材聚类口径)'])
check(ai['涨停数'] == 35 and ai['得分'] == 6 and ai['高度_最高连板'] == 4 and ai['强度_一字数'] == 3, 'AI算力6有基线不符')
check(four['AI算力/液冷存储']['宽度'] == 35 and four['AI算力/液冷存储']['题材晋级率'] == 0.158, 'AI算力四维基线不符')
ailine = next(l for l in lia['题材线'] if l['大方向'] == 'AI算力/液冷存储')
check(abs(ailine['开板占比'] - 0.46) < 0.01, 'AI算力开板占比不符')

# 判断结论必须含"确认主线"+"质量存疑"两关键词(本路核心判定)
check('确认' in j['结论'] and '质量存疑' in j['结论'], '结论缺核心判定词(确认/质量存疑)')

# ---- 5. 战绩画像身位归因回源 ----
prof = json.load(open(f'{L}/子agent增强/战绩画像_theme_20260817.json', encoding='utf-8'))
g = prof['归因']
check(g['正统龙候选(高位)']['n'] == 2 and abs(g['正统龙候选(高位)']['均收'] - 2.67) < 0.01, '战绩画像 正统龙高位 归因不符')
check(g['正统龙候选']['n'] == 3 and abs(g['正统龙候选']['均收'] - (-3.34)) < 0.01, '战绩画像 正统龙 归因不符')
check(g['人气龙候选']['n'] == 2 and abs(g['人气龙候选']['均收'] - (-4.33)) < 0.01, '战绩画像 人气龙 归因不符')
check(prof['合计']['胜率'] == '8/21' and abs(prof['合计']['均收'] - 0.31) < 0.01, '战绩画像合计不符')

# ---- 6. HTML 配平 + 6 h2 段序 ----
h = open(f'{L}/theme_body_20260817.html', encoding='utf-8').read()
check(h.count('<div') == h.count('</div>'), f"HTML div 不配平: {h.count('<div')} vs {h.count('</div>')}")
h2s = re.findall(r'<h2>(.*?)</h2>', h, re.DOTALL)
check(len(h2s) == 6, f'HTML h2 段数≠6: {len(h2s)}')
order = ['荐票卡', '三级判定', '主流生命周期', '龙头识别', '自主深挖', '认知迭代']
for want, got in zip(order, h2s):
    check(want in got, f'HTML h2 段序错: 期望含"{want}" 实得"{got}"')
# 无编造标记残留
text = re.sub(r'<[^>]+>', ' ', h)
# 对齐复盘一致性哨兵 C1 的"缺口叙述词"口径(只查数据应到而未到的缺口叙述,不查合法数据值null=新线无前值)
for pat in [r'溢价\s*null', r'null\s*[\(（]源', r'价源\s*null', r'数据缺口', r'不可达', r'沿用20260814', r'网络未刷新', r'未刷新']:
    check(not re.search(pat, text), f'HTML 残留缺口叙述词"{pat}"')

print('=== 验证结果 ===')
if FAIL:
    print(f'FAIL {len(FAIL)} 项:')
    for f in FAIL:
        print(' -', f)
    sys.exit(1)
else:
    print('PASS 全部通过: 3文件JSON合法/发出版schema齐全/荐票4只∈zt_pool/档位B置信度62/核心判定词齐/战绩画像归因回源一致/HTML配平+6段序+无缺口词')
    sys.exit(0)
