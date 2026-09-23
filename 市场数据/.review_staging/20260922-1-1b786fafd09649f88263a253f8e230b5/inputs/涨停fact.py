# -*- coding: utf-8 -*-
"""涨停fact.py — 涨停路事实层(fact)构建器 v1.0

作用: 把涨停复盘页面的关键数字从多源(raw层: zt_pool/summary/温度表/对链条/题材归位)
     收敛为「单一权威值 + 来源 + 质量枚举」, 写入 _学习/fact_{d}.json。
     五路agent/页面渲染引用 fact 而非各自读全套原始文件(省重复上下文token),
     出页哨兵可对照 fact 做数字一致性校验(同源公理红线机制化)。

用法: python 涨停fact.py 20260811
输出: _学习/fact_{d}.json + 控制台摘要(quality=conflicted/missing 会点名)

权威值优先级(生产口径):
  涨停/炸板/跌停/炸板率/温度/最高板/回封/二板加/成交额/封板总额 → 温度表
    (市场温度.py 汇总口径已剔 ST/退/N/C, 与 THS 三池对齐)
  题材线数 → 涨停对链条
  归位A/B/C计数 → 题材归位(全系统题材唯一真源, 来源档A/B/C即质量枚举)

质量枚举: ok(单源或多源一致) / conflicted(多源值不同) / partial(部分源缺失) / missing(全部缺失)
"""
import json, os, sys, csv
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
LEARN = os.path.join(BASE, '_学习')


def load_json(path):
    if not os.path.exists(path):
        return None
    for enc in ('utf-8-sig', 'utf-8', 'utf-16', 'gbk'):
        try:
            with open(path, encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def field(value, source, sources=None):
    """sources: {源名: 值}; value 必须等于权威源的值。"""
    src = sources or {source: value}
    vals = set()
    missing_src = []
    for k, v in src.items():
        if v is None:
            missing_src.append(k)
        else:
            vals.add(str(v))
    if not vals:
        q = 'missing'
    elif len(vals) == 1:
        q = 'partial' if missing_src else 'ok'
    else:
        q = 'conflicted'
    return {'value': value, 'source': source, 'quality': q, 'sources': src}


def zt_pool_rows(d):
    p = os.path.join(BASE, d, 'zt_pool.csv')
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8-sig') as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return None


def build(d):
    summary = load_json(os.path.join(BASE, d, 'summary.json')) or {}
    temp = load_json(os.path.join(LEARN, '_市场温度表.json')) or {}
    guiwei = load_json(os.path.join(LEARN, f'题材归位_{d}.json')) or {}
    chain = load_json(os.path.join(LEARN, f'涨停对链条_{d}.json')) or {}

    t = temp.get(d, {})
    s = summary
    g = guiwei.get('映射', {}) if isinstance(guiwei, dict) else {}
    c = chain

    guiwei_n = len(g)
    abcc = Counter((v.get('来源档') or '?')[:1] for v in g.values())

    facts = {}
    facts['涨停数'] = field(t.get('涨停数'), '温度表', {
        '温度表': t.get('涨停数'), 'summary': s.get('涨停家数'),
        '对链条': c.get('涨停总数'), '归位': guiwei_n if guiwei_n else None,
        'zt_pool原始行数': zt_pool_rows(d)})
    facts['炸板数'] = field(t.get('炸板数'), '温度表', {
        '温度表': t.get('炸板数'), 'summary': s.get('炸板家数')})
    facts['跌停数'] = field(t.get('跌停数'), '温度表', {
        '温度表': t.get('跌停数'), 'summary': s.get('跌停家数')})
    facts['炸板率'] = field(t.get('炸板率'), '温度表', {
        '温度表': t.get('炸板率'), 'summary': s.get('炸板率')})
    zt = t.get('涨停数'); zb = t.get('炸板数')
    facts['封板率'] = field(round(zt / (zt + zb), 4) if zt is not None and zb is not None else None,
                            '温度表自算(涨停/(涨停+炸板))')
    facts['温度'] = field(t.get('温度'), '温度表', {'温度表': t.get('温度')})
    facts['温度档'] = field(t.get('温度档'), '温度表', {'温度表': t.get('温度档')})
    facts['最高连板'] = field(t.get('最高板'), '温度表', {
        '温度表': t.get('最高板'), 'summary': s.get('最高连板')})
    facts['题材线数'] = field(c.get('题材线数'), '涨停对链条', {'涨停对链条': c.get('题材线数')})
    facts['归位数量'] = field(guiwei_n, '题材归位', {'题材归位': guiwei_n, '涨停数': t.get('涨停数')})
    facts['归位A档数'] = field(abcc.get('A', 0), '题材归位(来源档计数)')
    facts['归位B档数'] = field(abcc.get('B', 0), '题材归位(来源档计数)')
    facts['归位C档数'] = field(abcc.get('C', 0), '题材归位(来源档计数)')
    facts['回封数'] = field(t.get('回封数'), '温度表', {'温度表': t.get('回封数')})
    facts['二板加'] = field(t.get('二板加'), '温度表', {'温度表': t.get('二板加')})
    facts['成交额亿'] = field(t.get('成交额亿'), '温度表', {
        '温度表': t.get('成交额亿'), 'summary': s.get('两市成交额_亿')})
    facts['封板总额亿'] = field(t.get('封板总额亿'), '温度表', {'温度表': t.get('封板总额亿')})

    out = {
        'schema': 'fact-v1',
        'date': d,
        'route': 'limitup',
        'build_time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '权威值口径': '涨停/炸板/跌停/炸板率/温度/最高板/回封/二板加/成交额/封板总额=温度表(剔ST对齐THS); '
                     '题材线数=涨停对链条; 归位A/B/C=题材归位(题材唯一真源, 来源档即质量枚举)',
        'facts': facts,
    }

    os.makedirs(LEARN, exist_ok=True)
    out_path = os.path.join(LEARN, f'fact_{d}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out, out_path


def main():
    if len(sys.argv) < 2:
        print('用法: python 涨停fact.py YYYYMMDD')
        sys.exit(2)
    d = sys.argv[1]
    out, out_path = build(d)
    bad = [k for k, v in out['facts'].items() if v['quality'] not in ('ok', 'partial')]
    print(f"fact_{d}.json 已写入: {out_path}")
    for k, v in out['facts'].items():
        mark = '✓' if v['quality'] in ('ok', 'partial') else '✗'
        print(f"  {mark} {k}={v['value']} ({v['quality']}) 源={v['source']}")
    if bad:
        print(f"⚠ conflicted/missing 字段: {bad}")
        sys.exit(1)
    print('ALL OK')


if __name__ == '__main__':
    main()
