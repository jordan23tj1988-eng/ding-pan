# -*- coding: utf-8 -*-
"""跨路共票告警.py <推荐日R> <告警日D>
承接 Master 指派 MA-20261015-03 交付②: 把「源1当日榜净买为负」的负面过滤从本路(lhb)单路扩展为跨路共票告警。

口径(零后视镜/零编造):
  ①采集 推荐日R 五路判断文件(_学习/{auction|lhb|limitup|logic|theme}判断_{R}.json) 的 荐票.标的(荐票+观察) 并集;
    另采集 发出版 _学习/席位荐票_{R}.json Top5 作对照段; 同票被>=2路选中 => 共票(记路数)。
  ②告警源 = 告警日D 的双源校验 _学习/龙虎榜双源校验_{D}.json#/全量 (源1=当日榜净买, 源2=东财买入前五买侧净额)。
  ③告警等级(机械):
     S1 强矛盾   判定==强矛盾                       -> 卖压污染嫌疑, 禁入荐票/已有持仓降级
     S2 源1净卖  源1净买亿 < 0                      -> 资金腿直接否决
     W1 打折     判定==打折(源2/源1>=3倍)            -> 净买打折读, 只可观察
     W2 无当日榜 判定==无源1 或 源1口径含累计/区间    -> 证据不足, 不得作为荐票唯一依据
     W3 无席位证据 不在全量且不在D日 lhb.csv          -> 无席位证据
     OK          源1>0 且 判定==一致                 -> 通过
  ④共票(路数>=2)且带S1/S2 => 严重度升级为 S1+/S2+ 并在路由说明里点名冲突路。
★输出: _学习/跨路共票告警_{D}.json (可审计逐票) —— 本脚本只读不写其他产物, 不改生产脚本。
"""
import os, sys, json, io, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == '_学习' else os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
ROUTES = ['auction', 'lhb', 'limitup', 'logic', 'theme']

def rd(p):
    try:
        return json.load(io.open(p, encoding='utf-8-sig'))
    except Exception:
        return None

def norm(c):
    c = str(c or '').strip()
    return c.zfill(6) if c else ''

def picks_of(R):
    """返回 {代码: {'名称','路':[..],'类型':[..]}}"""
    bag = {}
    for rt in ROUTES:
        d = rd(os.path.join(L, '%s判断_%s.json' % (rt, R)))
        if not d:
            continue
        for it in (d.get('荐票') or {}).get('标的', []) or []:
            c = norm(it.get('代码'))
            if not c:
                continue
            b = bag.setdefault(c, {'代码': c, '名称': it.get('名称', ''), '路': [], '类型': []})
            b['路'].append(rt)
            b['类型'].append(it.get('类型', ''))
            if not b['名称']:
                b['名称'] = it.get('名称', '')
    return bag

def picks_publish(D):
    d = rd(os.path.join(L, '席位荐票_%s.json' % D))
    out = {}
    if not d:
        return out
    for it in (d.get('top5') or d.get('Top5') or d.get('标的') or d.get('荐票') or []):
        if not isinstance(it, dict):
            continue
        c = norm(it.get('代码'))
        if c:
            out[c] = it.get('名称', '')
    return out

def main():
    R = sys.argv[1] if len(sys.argv) > 1 else '20261015'
    D = sys.argv[2] if len(sys.argv) > 2 else '20261016'
    ds = rd(os.path.join(L, '龙虎榜双源校验_%s.json' % D)) or {}
    fw = {r['代码']: r for r in ds.get('全量', [])}
    lhb_rows = {}
    import csv
    p = os.path.join(BASE, D, 'lhb.csv')
    if os.path.isfile(p):
        for r in csv.DictReader(io.open(p, encoding='utf-8-sig')):
            lhb_rows.setdefault(r['代码'], r)

    def judge(code):
        r = fw.get(code)
        if not r:
            if code in lhb_rows:
                return ('W2', '当日榜缺失(仅出现在%s/lhb.csv, 上榜原因=%s)' % (D, lhb_rows[code].get('上榜原因', '')), None, None, None)
            return ('W3', '不在%s双源全量、也不在%s/lhb.csv' % (D, D), None, None, None)
        s1 = r.get('源1净买亿')
        s2 = r.get('源2买侧净额亿')
        v = r.get('判定')
        kj = str(r.get('源1口径') or '')
        if v == '强矛盾':
            return ('S1', '判定=强矛盾(源1=%s亿 源2买侧=%s亿, 方向相反且|任一|>1亿)=卖压污染嫌疑, 禁入荐票' % (s1, s2), s1, s2, v)
        if s1 is not None and s1 < 0:
            return ('S2', '源1当日榜净买为负(%s亿), 双源判定=%s -> 资金腿否决' % (s1, v), s1, s2, v)
        if v == '打折':
            return ('W1', '判定=打折(源1=%s亿 源2买侧=%s亿, 源2/源1>=3倍)=净买打折读, 只可观察' % (s1, s2), s1, s2, v)
        if v == '无源1' or ('累计' in kj) or ('区间' in kj):
            return ('W2', '无当日榜: 判定=%s 源1口径=%s -> 证据不足' % (v, kj), s1, s2, v)
        if s1 is not None and s1 > 0 and v == '一致':
            return ('OK', '源1当日榜正净买(%s亿) 且 双源判定=一致' % s1, s1, s2, v)
        if s1 is not None and s1 > 0:
            return ('W1', '源1正(%s亿)但判定=%s(未达一致)' % (s1, v), s1, s2, v)
        return ('W2', '判定=%s 源1口径=%s' % (v, kj), s1, s2, v)

    SEV = {'S1+': 0, 'S2+': 1, 'S1': 0, 'S2': 1, 'W1': 2, 'W2': 3, 'W3': 4, 'OK': 5}
    out = {'日期': D, '推荐日': R, '告警口径': __doc__.split('\n')[2].strip(), '来源': {
        '数据源': '_学习/龙虎榜双源校验_%s.json#/全量' % D, '推荐来源': ['_学习/%s判断_%s.json' % (rt, R) for rt in ROUTES]},
        'A_跨路共票告警': [], 'B_发出版自检': [], '汇总': {}}
    bag = picks_of(R)
    for c, b in sorted(bag.items(), key=lambda kv: (-len(kv[1]['路']), kv[0])):
        lvl, why, s1, s2, v = judge(c)
        nroutes = len(b['路'])
        lvl2 = lvl + ('+' if (nroutes >= 2 and lvl in ('S1', 'S2')) else '')
        out['A_跨路共票告警'].append({'代码': c, '名称': b['名称'], '告警等级': lvl2, '基本等级': lvl, '共票路数': nroutes,
                                    '入选路': sorted(b['路']), '入选类型': b['类型'], '源1净买亿': s1, '源2买侧净额亿': s2,
                                    '双源判定': v, '处置': why})
    pub = picks_publish(D)
    for c, nm in sorted(pub.items()):
        lvl, why, s1, s2, v = judge(c)
        out['B_发出版自检'].append({'代码': c, '名称': nm, '告警等级': lvl, '源1净买亿': s1, '源2买侧净额亿': s2,
                                   '双源判定': v, '处置': why})
    def tally(rows):
        t = {}
        for r in rows:
            t[r['告警等级']] = t.get(r['告警等级'], 0) + 1
        return dict(sorted(t.items(), key=lambda kv: SEV.get(kv[0].rstrip('+'), 9)))
    out['汇总'] = {'A_跨路共票': tally(out['A_跨路共票告警']), 'A_条目数': len(out['A_跨路共票告警']),
                   'B_发出版': tally(out['B_发出版自检']), 'B_条目数': len(out['B_发出版自检'])}
    out['A_跨路共票告警'].sort(key=lambda r: (SEV.get(r['基本等级'], 9), -r['共票路数'], r['代码']))
    out['B_发出版自检'].sort(key=lambda r: (SEV.get(r['告警等级'], 9), r['代码']))
    p_out = os.path.join(L, '跨路共票告警_%s.json' % D)
    json.dump(out, io.open(p_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('OK ->', p_out)
    print('A汇总', json.dumps(out['汇总']['A_跨路共票'], ensure_ascii=False), 'n=', len(out['A_跨路共票告警']))
    print('B汇总', json.dumps(out['汇总']['B_发出版'], ensure_ascii=False), 'n=', len(out['B_发出版自检']))
    for r in out['A_跨路共票告警']:
        if r['基本等级'] in ('S1', 'S2'):
            print('  ', r['告警等级'], r['代码'], r['名称'], '共票路', r['共票路数'], '->', r['处置'][:80])

if __name__ == '__main__':
    main()
