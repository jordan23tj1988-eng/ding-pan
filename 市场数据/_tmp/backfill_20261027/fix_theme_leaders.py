# -*- coding: utf-8 -*-
"""1027 补跑：题材龙头判断 归位（口径→说明并入；龙头标的平铺→按题材分键）"""
import json, collections

p = '_学习/题材龙头判断_20261027.json'
j = json.load(open(p, encoding='utf-8'))

kou = j.pop('口径', '')
notes = (j.get('说明') or '').strip()
if kou:
    j['说明'] = (notes + '｜' if notes else '') + '口径：' + kou

flat = j['龙头标的']
grouped = collections.OrderedDict()
for r in flat:
    shen = r.get('身位', '')
    theme = shen.split('·')[0].strip() if '·' in shen else '未归位'
    grouped.setdefault(theme, []).append(r)

j['龙头标的'] = grouped
j['矩阵题材名'] = [k for k in j['判断'].keys() if k != '全场']

# 顺序：日期/路/说明/矩阵题材名/龙头标的/判断
order = ['日期', '路', '说明', '矩阵题材名', '龙头标的', '判断']
out = collections.OrderedDict((k, j[k]) for k in order if k in j)
for k in j:
    if k not in out:
        out[k] = j[k]
    if k not in order:
        print('警告：仍有未归位字段', k)

json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已写入。题材键：')
for k, v in out['龙头标的'].items():
    print('  %-12s %d 条：%s' % (k, len(v), '、'.join(x['名称'] for x in v)))
print('矩阵题材名：', out['矩阵题材名'])
print('说明前 120 字：', out['说明'][:120])
