# -*- coding: utf-8 -*-
"""逻辑荐票卡.py {d} —— ④产业逻辑页「Top5 荐票卡」组件(2026-09-11 用户拍板:五路统一卡片形态)。

读当日 _学习/逻辑荐票_{d}.json(荐票[{代码,名称,类型,链条,环节,理由}]);
无该文件时退到 _学习/五路判断_{d}/logic.json 的 荐票.标的 与前判 结论。
渲染与⑤涨停复盘同款的排序卡(表格): # / 标的 / 类型 / 链条·环节 / 判据(理由)。
★零编造: 空仓([])时如实显示空仓+当日结论/空仓理由原文, 不凑票、不造行。
★非买入指令: 类型∈{身位排序,未启动挖掘,埋伏观察,卡位兑现}为本路判断; 理由原文照录。
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


def render(d, j, alt, src):
    import html as H
    concl = str((j or {}).get('结论') or (j or {}).get('空仓理由') or
                ((alt or {}).get('荐票') or {}).get('结论') or
                (((alt or {}).get('判断') or {}).get('结论')) or '—')
    items = (j or {}).get('荐票') or []
    if not items and alt:
        items = ((alt.get('荐票') or {}).get('标的')) or []
    if items:
        rows = []
        for i, x in enumerate(items[:5], 1):
            chain = ' · '.join([v for v in [str(x.get('链条') or ''), str(x.get('环节') or '')] if v]) or '—'
            rows.append('<tr><td>%d</td>'
                        '<td style="white-space:nowrap"><b>%s</b><br><span class="mut">%s</span></td>'
                        '<td style="white-space:nowrap">%s</td>'
                        '<td style="word-break:break-word">%s</td>'
                        '<td style="word-break:break-word">%s</td></tr>' % (
                            i, H.escape(str(x.get('名称') or '—')), H.escape(str(x.get('代码') or '—')),
                            H.escape(str(x.get('类型') or '—')), H.escape(chain),
                            H.escape(str(x.get('理由') or '—'))))
        table = ('<div class="card"><table style="table-layout:fixed;width:100%">'
                 '<colgroup><col style="width:26px"><col style="width:104px"><col style="width:74px">'
                 '<col style="width:158px"><col></colgroup>'
                 '<tr><th>#</th><th>标的</th><th>类型</th><th>链条·环节</th><th>判据(原文照录)</th></tr>'
                 + ''.join(rows) + '</table></div>')
    else:
        table = ('<div class="card"><b>空仓: 本日不荐票</b><br><span class="mut">%s</span></div>'
                 % H.escape(concl[:300]))
    hint = ('<div class="hint">★本路口径: 产业链模板 × 业绩雷达 × 涨停承载(来源 %s); '
            '类型∈{身位排序,未启动挖掘,埋伏观察,卡位兑现}(埋伏/挖掘=等线不追); 空仓=无链内A档可参与, 不凑票。</div>'
            % H.escape(src))
    return '<!--LOGICTICKET-->' + table + hint + '<!--/LOGICTICKET-->'


def main(d):
    j = load('逻辑荐票_%s.json' % d)
    alt = load(os.path.join('五路判断_%s' % d, 'logic.json'))
    src = ('逻辑荐票_%s.json' % d) if j else (('五路判断_%s/logic.json' % d) if alt else '缺产物')
    html = render(d, j, alt, src)
    p = os.path.join(L, '逻辑荐票卡_%s.html' % d)
    open(p, 'w', encoding='utf-8').write(html)
    items = ((j or {}).get('荐票') or ((alt or {}).get('荐票') or {}).get('标的') or [])
    print('%s 逻辑荐票卡: %s (来源 %s)' % (d, ('%d只' % len(items)) if items else ('空仓' if (j or alt) else '无产出'), src))
    print('  写入: %s' % os.path.basename(p))
    return html


if __name__ == '__main__':
    import datetime
    main(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime('%Y%m%d'))
