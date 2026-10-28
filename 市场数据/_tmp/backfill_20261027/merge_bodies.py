# -*- coding: utf-8 -*-
"""1027 补跑：把新建 index/cycle body 写回 judgment，并做结构自检"""
import json, re, collections

L = '_学习/'
jp = L + 'judgment_20261027.json'
j = json.load(open(jp, encoding='utf-8'))
bodies = j['bodies']

for name in ('index', 'cycle'):
    h = open('%s%s_body_20261027.html' % (L, name), encoding='utf-8').read()
    opens = len(re.findall(r'<div\b', h))
    closes = len(re.findall(r'</div>', h))
    h2 = re.findall(r'<h2[^>]*>(.*?)</h2>', h, re.S)
    h3 = re.findall(r'<h3[^>]*>(.*?)</h3>', h, re.S)
    kpi = len(re.findall(r'<div class="kpi"', h))
    print('[%s] len=%d div open=%d close=%d %s h2=%d h3=%d kpi=%d' %
          (name, len(h), opens, closes, 'OK' if opens == closes else '失衡', len(h2), len(h3), kpi))
    for x in h2:
        print('    h2:', re.sub(r'<[^>]+>', '', x).strip()[:60])
    for x in h3:
        print('    h3:', re.sub(r'<[^>]+>', '', x).strip()[:60])
    bodies[name] = h

# logic body h2 七 归位到 cognition
lp = L + 'logic_body_20261027.html'
lb = open(lp, encoding='utf-8').read()
new_lb = lb.replace('<h2>七 独立盲区声明与自检', '<h2>七 认知迭代 · 独立盲区声明与自检')
if new_lb != lb:
    open(lp, 'w', encoding='utf-8').write(new_lb)
    print('\nlogic h2 七 已改名为「七 认知迭代 · 独立盲区声明与自检」')
    bodies['logic'] = new_lb
else:
    print('\nlogic h2 未见待改字符串，实际 h2：')
    for x in re.findall(r'<h2[^>]*>(.*?)</h2>', lb, re.S):
        print('   ', re.sub(r'<[^>]+>', '', x).strip()[:60])

json.dump(j, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nbodies keys:', list(bodies.keys()))
print('judgment 已写回，大小 %d bytes' % len(open(jp, encoding='utf-8').read()))
