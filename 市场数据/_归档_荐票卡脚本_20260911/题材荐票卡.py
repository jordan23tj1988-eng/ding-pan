# -*- coding: utf-8 -*-
"""题材荐票卡.py {d} —— ③主线题材页「Top5 荐票卡」组件(2026-09-11 用户拍板:五路统一卡片形态)。

读当日 _学习/题材荐票_{d}.json(路=theme; 标的[{代码,名称,类型,身位,题材线,理由}]),
渲染与⑤涨停复盘同款的排序卡(表格): # / 标的 / 类型 / 身位 / 题材线 / 判据(理由)。
★零编造: 空仓(标的=[])时如实显示空仓+当日结论原文, 不凑票、不造行、不变形。
★非买入指令: 类型∈{荐票,观察}为本路判断; 理由原文照录, 不改写。
"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')


def load(name):
    p = os.path.join(L, name)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8-sig'))
    except Exception as exc:
        print('  [warn] 读取失败 %s: %s' % (p, exc))
        return None


def render(d, j):
    import html as H
    if j is None:
        body = ('<div class="card"><b>— 本日无题材荐票产出</b><br>'
                '<span class="mut">题材荐票_{d}.json 未落盘, 本卡不代填。</span></div>')
        hint = '<div class="hint">★口径: 卡片内容只回读当日题材路产物, 缺产物如实标 —。</div>'
        return '<!--THEMETICKET-->' + body + hint + '<!--/THEMETICKET-->'
    concl = str(j.get('结论') or '—')
    items = j.get('标的') or []
    if items:
        rows = []
        for i, x in enumerate(items[:5], 1):
            rows.append('<tr><td>%d</td>'
                        '<td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                        '<td style="white-space:nowrap">%s</td>'
                        '<td style="white-space:nowrap">%s</td>'
                        '<td style="white-space:nowrap">%s</td>'
                        '<td style="word-break:break-word">%s</td></tr>' % (
                            i, H.escape(str(x.get('名称') or '—')), H.escape(str(x.get('代码') or '—')),
                            H.escape(str(x.get('类型') or '—')), H.escape(str(x.get('身位') or '—')),
                            H.escape(str(x.get('题材线') or '—')), H.escape(str(x.get('理由') or '—'))))
        table = ('<div class="card"><table style="table-layout:fixed;width:100%">'
                 '<colgroup><col style="width:26px"><col style="width:104px"><col style="width:56px">'
                 '<col style="width:130px"><col style="width:118px"><col></colgroup>'
                 '<tr><th>#</th><th>标的</th><th>类型</th><th>身位</th><th>题材线</th><th>判据(原文照录)</th></tr>'
                 + ''.join(rows) + '</table></div>')
    else:
        table = ('<div class="card"><b>空仓: 本日不荐票</b><br><span class="mut">%s</span></div>'
                 % H.escape(concl))
    hint = ('<div class="hint">★本路口径: 题材归位 × 四维 × 生命周期; 类型∈{荐票,观察}(观察=仅验证备选, 非买入); '
            '空仓=无可靠题材依据, 不为满足数量凑票。当日结论: %s</div>' % H.escape(concl[:180]))
    return '<!--THEMETICKET-->' + table + hint + '<!--/THEMETICKET-->'


def main(d):
    j = load('题材荐票_%s.json' % d)
    html = render(d, j)
    p = os.path.join(L, '题材荐票卡_%s.html' % d)
    open(p, 'w', encoding='utf-8').write(html)
    n = len((j or {}).get('标的') or [])
    print('%s 题材荐票卡: %s' % (d, ('%d只' % n) if n else ('空仓' if j else '无产出')))
    print('  写入: %s' % os.path.basename(p))
    return html


if __name__ == '__main__':
    import datetime
    main(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime('%Y%m%d'))
