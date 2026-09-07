# -*- coding: utf-8 -*-
"""_认知库蒸馏_五路.py —— 六路认知迭代库蒸馏器(2026-08-16 重建+扩展)
从 judgment_*.json 各路 body 认知段提取历史认知迭代, 输出结构化认知库。
重建源: __pycache__/_认知库蒸馏_五路.cpython-311.pyc 反汇编(原 .py 丢失)。
修复(相对原版): ①ROUTES 补 cycle(原五路漏 cycle); ②兼容三种认知段结构——
   .tl/.tli(cycle/lhb/logic/theme) / .iter-card(auction) / .card(limitup);
   ③空壳条目(正文+标题双空)跳过。
输出: _学习/_认知库_{route}.json(主库) + _学习/子agent增强/认知库_{route}_{YYYYMMDD}.json(带日期)。
铁律: 零编造——只从 judgment body 原文提取, 数字/日期不改写。
"""
import re, os, json, glob
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')

ROUTES = ['auction', 'cycle', 'lhb', 'limitup', 'logic', 'theme']


def _clean(s):
    return re.sub(r'<[^>]+>', '', s or '').strip()


def _档位(b):
    m = re.search(r'\[([ABC])档\]', b or '')
    return m.group(1) if m else None


def _类型(h, b):
    t = (h or '') + (b or '')
    if re.search(r'修复|教训|错|败|被否|陷阱', t):
        return '教训'
    if re.search(r'信号|判定|判据|门禁|规则', t):
        return '信号'
    return '经验'


def _strip_serial(h):
    """去掉 iter-card 标题序号前缀 ①②③... 或 1. 2. 等"""
    return re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\d]+[\.、\s]*', '', (h or '').strip())


def _norm_date(s):
    """日期归一为 YYYY-MM-DD: 兼容 YYYYMMDD / MM-DD / YYYY-MM-DD"""
    s = (s or '').strip()
    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
    if m:
        return '%s-%s-%s' % m.groups()
    m = re.match(r'^(\d{2})-(\d{2})$', s)
    if m:
        return '%s-%s-%s' % (datetime.now().year, m.group(1), m.group(2))
    return s


def _cog_segment(v):
    """定位认知段: 找「六 认知/认知迭代/我的认知迭代」h2 之后的原文; 找不到=全段"""
    m = re.search(r'<h2[^>]*>(?:六\s*)?(?:我的)?认知(?:迭代)?', v)
    return v[m.start():] if m else v


def extract(v, fdate):
    """从单路 body html 提取认知条目 [(日期,标题,正文,支撑), ...]"""
    out = []
    if not isinstance(v, str) or not v.strip():
        return out
    seg = _cog_segment(v)
    # 结构1: .tl/.tli 时间线
    if 'class="tli"' in seg:
        for m in re.finditer(r'<div class="tli">(.*?)(?=<div class="tli">|</div></div></details>|$)', seg, re.S):
            s = m.group(1)
            d = re.search(r'<div class="d">\s*(?:<b>)?\s*([0-9-]{5,10})\s*(?:</b>)?\s*</div>', s)
            h = re.search(r'<div class="h">(.*?)</div>', s, re.S)
            b = re.search(r'<div class="b">(.*?)</div>', s, re.S)
            sup = re.search(r'<div class="sup">(.*?)</div>', s, re.S)
            bd_ = re.search(r'<b>(\d{2}-\d{2})</b>\s*([^<]*)', s)
            if d:
                out.append((_norm_date(d.group(1)), h.group(1) if h else '', b.group(1) if b else '', sup.group(1) if sup else ''))
            elif bd_:
                out.append(('%s-%s' % (datetime.now().year, bd_.group(1)), '', bd_.group(2) or s, ''))
        return out
    # 结构2: .iter-card (auction): <b>序号 标题</b><span>正文</span>, 日期=fdate
    if 'iter-card' in seg:
        for m in re.finditer(r'<div class="iter-card">(.*?)</div>', seg, re.S):
            bm = re.search(r'<b>(.*?)</b>\s*<span>(.*?)</span>', m.group(1), re.S)
            if not bm:
                continue
            out.append((fdate, _strip_serial(bm.group(1)), bm.group(2), ''))
        return out
    # 结构3: .card (limitup): <b>标题(日期)</b><p>正文</p>
    if 'class="card"' in seg:
        for m in re.finditer(r'<div class="card">\s*<b>(.*?)</b>\s*<p[^>]*>(.*?)</p>', seg, re.S):
            title = m.group(1)
            body = m.group(2)
            dm = re.search(r'\((\d{8})\)', title) or re.search(r'\((\d{4}-\d{2}-\d{2})\)', title)
            if dm:
                ds = dm.group(1)
                日期 = '%s-%s-%s' % (ds[:4], ds[4:6], ds[6:8]) if len(ds) == 8 else ds
                title = title[:dm.start()].strip()
            else:
                日期 = fdate
            out.append((日期, title, body, ''))
        return out
    return out


def distill(route):
    items = []
    seen = set()
    for p in sorted(glob.glob(os.path.join(L, 'judgment_*.json'))):
        mfn = re.match(r'judgment_(\d{8})', os.path.basename(p))
        if not mfn:
            continue
        fdate = '%s-%s-%s' % (mfn.group(1)[:4], mfn.group(1)[4:6], mfn.group(1)[6:8])
        try:
            j = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        v = (j.get('bodies') or {}).get(route) or ''
        for 日期, 标题, 正文, 支撑 in extract(v, fdate):
            key = (日期, (标题 or '')[:20])
            if key in seen:
                continue
            seen.add(key)
            正文 = _clean(正文)
            标题 = _clean(标题)
            if not 正文 and not 标题:
                continue
            items.append({
                '日期': 日期,
                '标题': 标题,
                '正文': 正文,
                '支撑': _clean(支撑),
                '档位': _档位(正文),
                '类型': _类型(标题, 正文),
            })
    items.sort(key=lambda x: x['日期'], reverse=True)
    return items


def main():
    total = 0
    now = datetime.now()
    for r in ROUTES:
        items = distill(r)
        out = {
            'route': r, 'version': 1, 'updated': now.strftime('%Y-%m-%d'),
            '源': 'judgment_*.json bodies.%s 认知段(蒸馏器重建)' % r,
            '条数': len(items), '条目': items,
        }
        json.dump(out, open(os.path.join(L, '_认知库_%s.json' % r), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        enh = os.path.join(L, '子agent增强')
        os.makedirs(enh, exist_ok=True)
        out2 = dict(out)
        out2['源'] = '认知库蒸馏器 输出至技能指定路径(复盘引用)'
        json.dump(out2, open(os.path.join(enh, '认知库_%s_%s.json' % (r, now.strftime('%Y%m%d'))), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('认知库_%s: %d 条 (→子agent增强/%s)' % (r, len(items), now.strftime('%Y%m%d')))
        total += len(items)
    print('合计 %d 条' % total)


if __name__ == '__main__':
    main()
