# -*- coding: utf-8 -*-
"""20261104 judgment bodies 结构修复: lhb锚点成对 / logic rowA头 / limitup 裸null"""
import io, json, re, shutil, os

P = r'D:/股票数据/市场数据/_学习/judgment_20261104.json'
shutil.copyfile(P, P + '.bak_structfix')
j = json.load(io.open(P, encoding='utf-8-sig'))
B = j['bodies']

# ---- 1) lhb: LHBLEDGER 收尾锚点成对（仅一个当日日块，无更早存档）----
lhb = B['lhb']
if '<!--/LHBLEDGER-->' not in lhb:
    i = lhb.find('<!--LHBLEDGER-->')
    # 台账段结束位置 = 该 section 的 </section> 之前
    end = lhb.find('</section>', i)
    if end < 0:
        end = len(lhb)
    lhb = lhb[:end].rstrip() + '\n<!--/LHBLEDGER-->\n' + lhb[end:]
    B['lhb'] = lhb
    print('lhb anchor closed at', end)

# ---- 2) logic: 头部改建 rowA(hero+4kpi) ----
lg = B['logic']
if 'class="rowA"' not in lg:
    # 取原头部 card 里的 hint 与 一句话 + 4 个 kpi
    m = re.search(r'<div class="card"><div class="hint">(.*?)</div>\s*<p><b>一句话：(.*?)</b></p>\s*((?:<div class="kpi">.*?</div>\s*){4})</div>', lg, re.S)
    if not m:
        raise SystemExit('logic head pattern not matched')
    kick, onesent, kpis = m.group(1).strip(), m.group(2).strip(), m.group(3)
    head = ('<div class="rowA"><div class="hero"><div class="kick">%s</div>\n'
            '<h1>%s</h1>\n'
            '<div class="stance"><span class="pill"><span>档位</span><b>C</b></span>'
            '<span class="pill"><span>置信</span><b>72</b></span>'
            '<span class="pill"><span>荐票</span><b>0 只</b><span class="mut">空仓 · 观察 2 只</span></span>'
            '<span class="pill"><span>总仓</span><b>0%%</b><span class="mut">等确认</span></span></div>\n'
            '</div>' % (kick, onesent)) + kpis.rstrip() + '</div>\n'
    lg = lg[:m.start()] + head + lg[m.end():]
    B['logic'] = lg
    print('logic rowA built, kpis=', kpis.count('class="kpi"'))

# ---- 3) limitup: 裸 null 字面量 -> — ----
for k, v in list(B.items()):
    n = v.count('=null（源') + v.count('=null(源') + v.count('=null ')
    if n:
        v2 = v.replace('=null（源', '=—（源').replace('=null(源', '=—(源')
        v2 = re.sub(r'=null(?=\s|<|，|,|。)', '=—', v2)
        B[k] = v2
        print('null fixed in', k, n)

json.dump(j, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', P)
