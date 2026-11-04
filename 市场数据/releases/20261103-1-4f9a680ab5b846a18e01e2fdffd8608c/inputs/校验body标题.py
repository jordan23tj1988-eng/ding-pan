#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""body 标题归位自检器（只读）：复刻 review_pages._body_import 的 label 口径。

用法:
  python 校验body标题.py {d}                   # 全路批量（出页前必跑）
  python 校验body标题.py <route> <body.html>   # 单路

口径: 匹配标签 = <h2> 的**直文本子节点**（<span class="hint"> 等子标签内的字不参与）。

批量模式读 _学习/judgment_{d}.json 的 bodies（缺则回退 _学习/{route}_body_{d}.html /
master_body_{d}.html），一次列出**所有路**的未归位 h2、未覆盖 section 和重复映射 ——
因为 生成盯盘台.py 是遇到第一个不合规标题就 raise，逐条修会浪费 N 次整链重渲染。

额外检查：
· 「重复映射」两个 h2 命中同一个 section 时, 另一个段会零 claim -> 整页 degraded
  (不报错, 比 raise 更难查), 所以这里显式告警。
· 「深挖/认知段措辞」_sync_capability_blocks 靠字面「自主深挖」「认知迭代」识别并摘除
  旧模块段；只写「深挖」不会被摘 -> 业务段数超契约 -> 整块注入拒绝（2026-11-03 lhb 事故）。
"""
import sys, re, json
from pathlib import Path

ROOT = Path(r'D:\股票数据\市场数据')
LEARN = ROOT / '_学习'
EXTRA_OPTIONAL = {('cycle', 'research'), ('logic', 'forward'), ('index', 'recommendations')}


def load_review_pages():
    sys.path.insert(0, str(ROOT))
    import review_pages as R
    return R


def scan(R, route, html):
    need = [s['id'] for s in R._contract()['routes'][route]['sections']]
    optional = EXTRA_OPTIONAL | R.MACHINE_ONLY_SECTIONS
    have, bad, labels = [], [], []
    print('route=%s 字节=%d' % (route, len(html)))
    for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.S):
        root = R._Tree('<div>' + m.group(1) + '</div>').root
        label = ''.join(x for x in root.children[0].children if isinstance(x, str)).strip()
        labels.append(label)
        hit = next((sid for kw, sid in R.HEADING_MAP[route] if kw in label), None)
        print('  h2=%-44r -> %s' % (label, hit or '未归位(会 raise)'))
        if hit:
            have.append(hit)
        else:
            bad.append(label)

    # 末两段措辞：能力模块接管段必须用固定字面（仅对含 research/cognition 栏目的路）
    cap_bad = []
    if ('research' in need or 'cognition' in need) and len(labels) >= 2:
        if '自主深挖' not in labels[-2]:
            cap_bad.append('倒数第二段须含「自主深挖」: %r' % labels[-2][:40])
        if '认知迭代' not in labels[-1]:
            cap_bad.append('最后一段须含「认知迭代」: %r' % labels[-1][:40])

    missing = [s for s in need if s not in have and (route, s) not in optional]
    dup = sorted({s for s in have if have.count(s) > 1})
    print('  必需:', need)
    print('  覆盖:', sorted(set(have)))
    if missing:
        print('  !! 缺栏(WARN, 可能由机器卡填充, 需人工确认):', missing)
    if dup:
        print('  !! 重复映射(WARN, 会挤空别的段->degraded):', dup)
    for x in cap_bad:
        print('  !! 能力模块段措辞不合格(会拒注入):', x)
    # 硬 FAIL 只留两类确定阻断：h2 未归位(渲染 raise) / 能力段措辞(注入拒绝)
    ok = not bad and not cap_bad
    print('  结论:', 'PASS' if ok else 'FAIL')
    return ok


def batch(R, d):
    jp = LEARN / ('judgment_%s.json' % d)
    bodies = {}
    if jp.exists():
        bodies = json.load(open(jp, encoding='utf-8')).get('bodies') or {}
    else:
        print('WARN %s 不存在, 回退按 body 文件扫描' % jp.name)
    allok = True
    for route in R.HEADING_MAP:
        html = bodies.get(route)
        if not html:
            fp = LEARN / ('master_body_%s.html' % d if route == 'index'
                          else '%s_body_%s.html' % (route, d))
            if not fp.exists():
                print('route=%s 无 body（judgment 与 %s 均缺）' % (route, fp.name))
                allok = False
                continue
            html = fp.read_text(encoding='utf-8')
        if not scan(R, route, html):
            allok = False
    print('批量结论:', 'ALL PASS' if allok else 'FAIL')
    return allok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    R = load_review_pages()
    arg0 = sys.argv[1]
    if len(sys.argv) == 2 and re.fullmatch(r'[0-9]{8}', arg0):
        return 0 if batch(R, arg0) else 1
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    html = Path(sys.argv[2]).read_text(encoding='utf-8')
    return 0 if scan(R, arg0, html) else 1


if __name__ == '__main__':
    sys.exit(main())
