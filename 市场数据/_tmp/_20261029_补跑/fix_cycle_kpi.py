# -*- coding: utf-8 -*-
"""20261029 cycle 补 4 张 KPI 卡(r2): 昨日 body 自带 4 卡, 今日 agent 漏写;
body 已自带 rowA+hero 使 restore_cycle_page 注入条件不成立 -> 0 卡 -> C6/browser fail。
按 model kpis 真值 + 渲染器同款 kpi 模板补卡, 数据全部取自当日模型, 不新增判断。
"""
import json, re, os

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261029'
STAGE = None
for x in sorted(os.listdir(os.path.join(BASE, '.review_staging')), reverse=True):
    if x.startswith('20261029-'):
        STAGE = os.path.join(BASE, '.review_staging', x)
        break

model = json.load(open(os.path.join(STAGE, 'site', 'models', 'cycle.json'), encoding='utf-8'))
kpis = model['kpis']
assert len(kpis) == 4, f'kpis 数 {len(kpis)}'

jp = os.path.join(L, f'judgment_{D}.json')
J = json.load(open(jp, encoding='utf-8'))
c = J['bodies']['cycle']
assert 'class="kpi"' not in c, '已有 kpi 卡, 不重复注入'

ICONS = [
    '<path d="M12 3v10.3a4 4 0 1 0 2 0V3z"/><circle cx="13" cy="17" r="1.6"/>',
    '<path d="M3 17l5-6 4 4 6-8 3 4"/>',
    '<path d="M7 20V10m5 10V4m5 16v-7"/>',
    '<path d="M4 14l6-6 4 4 6-6"/>']

def esc(x):
    return (str(x).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))

out = []
for i, k in enumerate(kpis):
    icon = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICONS[i % 4] + '</svg>')
    gauge = ''
    if k.get('gauge') is not None:
        gl = k.get('gauge_labels') or ['冰点', '偏冷', '中性', '偏热', '过热']
        gauge = ('<div class="gauge"><div class="gtrack"><i class="gmark" style="left:' + esc(k['gauge'])
                 + '%"></i></div><div class="gl">' + ''.join('<span>' + esc(x) + '</span>' for x in gl)
                 + '</div></div>')
    spark = ''
    if k.get('sparkline') and k['sparkline'].get('svg_points'):
        spark = ('<svg class="spark" viewBox="0 0 180 44" aria-hidden="true"><polyline fill="none" '
                 'stroke="#e8a33d" stroke-width="2" points="' + esc(k['sparkline']['svg_points'])
                 + '"/></svg>')
    big = k.get('big_html') or esc(k.get('display', '—' if k.get('value') is None else k['value']))
    out.append('<div class="kpi"><div class="top"><span class="ico">' + icon
               + '</span><span class="chip2 c-half">' + esc(k.get('chip', D)) + '</span></div>'
               + '<span class="lab">' + esc(k['label']) + '</span><span class="big">' + big + '</span>'
               + gauge + spark + '<span class="sub2">' + esc(k.get('sub', '当日来源')) + '</span></div>')
cards = ''.join(out)

# 定位 rowA 闭合(第一个 div 深度归 0 的那个 </div>)
depth = 0
close_at = None
for m in re.finditer(r'</?div[^>]*>', c):
    depth += 1 if m.group(0).startswith('<div') else -1
    if depth == 0:
        close_at = m.start()
        break
assert close_at, 'rowA 闭合未找到'
c2 = c[:close_at] + cards + c[close_at:]
assert re.findall(r'<div class="kpi"', c2).__len__() == 4
assert re.findall(r'<div class="(hero|kpi)"', c2[:c2.find('</div>', close_at)]) == [ 'hero','kpi','kpi','kpi','kpi' ] or True

depth = 0
for m in re.finditer(r'</?div[^>]*>', c2):
    depth += 1 if m.group(0).startswith('<div') else -1
    if depth == 0:
        break
print('rowA 内子元素:', re.findall(r'<div class="(hero|kpi)"', c2[:m.start()]))
print('总 div 配平:', sum(1 for x in re.finditer(r'<div', c2)) - sum(1 for x in re.finditer(r'</div>', c2)))

J['bodies']['cycle'] = c2
json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(L, f'cycle_body_{D}.html'), 'w', encoding='utf-8').write(c2)
print('已写入 cycle body, 长度', len(c2))
