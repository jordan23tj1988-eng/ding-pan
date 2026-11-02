# -*- coding: utf-8 -*-
"""概览/周期 body 结构校验: div配平 / h2 / 裸null / class白名单 / 关键读数回源"""
import json, re, sys, os

BASE = r"D:\股票数据\市场数据"
CSS = json.load(open(os.path.join(BASE, '_契约', '页面契约.v1.json'), encoding='utf-8'))['visual']['css']
ALLOWED = set(re.findall(r'\.([A-Za-z][\w-]*)', CSS))

def check(path, need_tokens):
    s = open(path, encoding='utf-8').read()
    errs = []
    nd, ncd = len(re.findall(r'<div\b', s)), len(re.findall(r'</div>', s))
    if nd != ncd:
        errs.append('div 不配平 %d/%d' % (nd, ncd))
    h2 = re.findall(r'<h2[^>]*>(.*?)</h2>', s, re.S)
    if re.search(r'>\s*null\s*<|>\s*None\s*<|\bnull\b|\bNone\b', s):
        errs.append('出现裸 null/None')
    for kw in ('NaN', 'TODO', 'undefined', '{{'):
        if kw in s:
            errs.append('禁词 ' + kw)
    classes = set()
    for m in re.finditer(r'class="([^"]*)"', s):
        classes.update(m.group(1).split())
    bad = sorted(classes - ALLOWED)
    if bad:
        errs.append('越界 class: ' + ','.join(bad))
    txt = re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', s))
    missing = [t for t in need_tokens if t not in s]
    if missing:
        errs.append('缺关键读数: ' + ' | '.join(missing))
    print('=' * 78)
    print(os.path.basename(path), 'bytes=%d 纯文本=%d' % (len(s.encode('utf-8')), len(txt)))
    print('h2 数=%d' % len(h2))
    for i, t in enumerate(h2, 1):
        print('  h2#%d %s' % (i, re.sub(r'<[^>]+>', ' ', t).strip()[:60]))
    print('div: <div>=%d </div>=%d 差=%d' % (nd, ncd, nd - ncd))
    print('class 总数=%d 越界=%s' % (len(classes), bad or '无'))
    if errs:
        print('FAIL')
        for e in errs:
            print('  ✗', e)
        return False
    print('PASS')
    return True

cyc_need = ['截至 2026-11-02 收盘', '1.78 万亿', '弱修', '净涨停', '125', '触发器', '—（东财 push2 被阻断',
            'class="steps"', 'class="stages"', 'class="cols"', 'class="posmeter"', 'class="tl"', 'class="tli"',
            '最高 6 板', '青岛食品', '114', '主判=退潮·降', '投票断档', '10-30', '启动']
idx_need = ['截至 2026-11-02 收盘', '001219', '002275', '600299', '688518', '002172', 'class="obs"',
            'class="rail"', 'class="routes"', 'class="rt"', 'auction.html', 'lhb.html', 'theme.html',
            'logic.html', 'limitup.html', '总裁决', '63']

ok1 = check(os.path.join(BASE, '_学习', 'cycle_body_20261102.html'), cyc_need)
ok2 = True
p2 = os.path.join(BASE, '_学习', 'index_body_20261102.html')
if os.path.exists(p2):
    ok2 = check(p2, idx_need)
else:
    print('index_body 尚未生成, 跳过')
sys.exit(0 if (ok1 and ok2) else 1)
