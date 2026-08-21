# -*- coding: utf-8 -*-
"""补产 theme 0a闸门两json: 题材龙头判断/题材生命周期判断 (20260821) 逐字提取自 theme_body 二段矩阵+三段生命周期"""
import json, io, re, os
L = r'D:\股票数据\市场数据\_学习'
b = io.open(os.path.join(L, 'theme_body_20260821.html'), encoding='utf-8').read()
h2s = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', b, re.S))

def rows_of(seg):
    out = []
    for m in re.finditer(r'<tr><td(?: class="[^"]*")?>([^<]+)</td><td(?: class="[^"]*")?>([^<]+)</td><td(?: class="[^"]*")?>([^<]*)</td><td(?: class="[^"]*")?>(.*?)</td></tr>', seg, re.S):
        line, core, head, judge = m.groups()
        out.append((line.strip(), core.strip(), head.strip(), re.sub(r'<[^>]+>', '', judge).strip()))
    return out

# ===== 二段: 龙头标的 =====
seg2 = b[h2s[1].end():h2s[2].start()]
heads, judges = {}, {}
for line, core, head, judge in rows_of(seg2):
    heads.setdefault(line, [])
    if head and not head.startswith('—'):
        heads[line].append({'名称': head.split('(')[0].strip(), '身位': head})
    judges[line] = judge

longj = json.load(io.open(os.path.join(L, '题材生命周期_20260820.json'), encoding='utf-8')) if os.path.exists(os.path.join(L, '题材生命周期_20260820.json')) else None

lj = {
    '日期': '20260821', '路': 'theme',
    '来源': 'theme_body_20260821.html 二段(三级判定矩阵·龙头标的列) LLM原文逐字提取(键=6有题材聚类口径线名+退坡/退潮主线补充)',
    '龙头标的': heads,
    '判断': judges,
}
io.open(os.path.join(L, '题材龙头判断_20260821.json'), 'w', encoding='utf-8', newline='').write(json.dumps(lj, ensure_ascii=False, indent=1))
print('龙头判断: lines =', list(heads.keys()))

# ===== 三段: 生命周期 =====
seg3 = b[h2s[2].end():h2s[3].start()]
per_line = {}
for line, lc, stage, judge in rows_of(seg3):
    per_line[line] = {'定性': lc, '机械阶段': stage, '判据': judge}
# 高低切段
i_hc = seg3.find('高低切去向')
hc_seg = seg3[i_hc:] if i_hc > 0 else ''
hc_text = re.sub(r'<[^>]+>', ' ', hc_seg).replace('\xa0', ' ').strip()
hc_text = re.sub(r'\s+', ' ', hc_text)
lj2 = {
    '日期': '20260821', '路': 'theme',
    '来源': 'theme_body_20260821.html 三段(主流生命周期·判断) LLM原文逐字提取(键=6有题材聚类口径线名+退坡/退潮主线补充)',
    '逐线判断': {k: {'定性': v['定性'], '判据': v['判据']} for k, v in per_line.items()},
    '高低切': hc_text[:600],
}
io.open(os.path.join(L, '题材生命周期判断_20260821.json'), 'w', encoding='utf-8', newline='').write(json.dumps(lj2, ensure_ascii=False, indent=1))
print('生命周期判断: lines =', list(per_line.keys()))
print('高低切:', hc_text[:150])
