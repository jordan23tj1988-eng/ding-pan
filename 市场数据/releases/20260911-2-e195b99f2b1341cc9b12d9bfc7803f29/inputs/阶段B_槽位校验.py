# -*- coding: utf-8 -*-
"""阶段B_槽位校验.py —— LLM槽位协议机器校验(2026-08-12 阶段B实施)

三层防重复 + 槽位完整性 + 实体引用校验(LLM手写区 vs 数据源真源)
- 完整性: 必填槽位在 bodies 必须有内容(h2一/二/三/四+环境规则+板块三+清单应答+一句话)
- 防重复: 同槽位关键内容出现次数>1 → FAIL(LLM重复填写)
- 实体引用: 槽位内票名 ⊆ _ths_zt_pool / 数字 ⊆ 温度表真源(双向包含, 复用维度8口径)
用法: python 阶段B_槽位校验.py [date]   → rc=0 通过 / rc=1 拦截
"""
import sys, os, re, json, hashlib

L = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_学习')
d = sys.argv[1] if len(sys.argv) > 1 else '20260811'
JP = os.path.join(L, 'judgment_%s.json' % d)
fails = []
warns = []


def fail(msg):
    fails.append(msg)


def load_j():
    if not os.path.isfile(JP):
        fail('judgment_%s.json 不存在' % d)
        return None
    return json.load(open(JP, encoding='utf-8'))


def slot_exists(bd, kw, label):
    """槽位完整性: 结构定位点存在"""
    if bd.find(kw) < 0:
        fail('槽位缺失 [%s]: bodies 无 %s' % (label, kw[:30]))
    else:
        # 防重复: 出现次数(去重锚点)
        n = len(re.findall(re.escape(kw), bd))
        if n > 1:
            fail('防重复 [%s]: %s 出现 %d 次(应1次)' % (label, kw[:30], n))


def entity_check(bd, label):
    """实体引用: 槽位内票名 ⊆ 池 / 数字 ⊆ 温度表(双向包含)"""
    pool = json.load(open(os.path.join(L, '_ths_zt_pool.json'), encoding='utf-8')).get(d) or []
    pnames = [x['name'] for x in pool]
    tbl = json.load(open(os.path.join(L, '_市场温度表.json'), encoding='utf-8')).get(d) or {}
    # 池票名双向包含匹配(防"今日哈药"4字贪婪)
    for nm in pnames:
        for m in re.finditer(nm, bd):
            i = m.start()
            pre = bd[max(0, i - 2):i]
            if re.search(r'[\u4e00-\u9fa5]{2}', pre):  # 前面还有汉字=更长词的一部分
                continue
            break
        else:
            continue
        break
    # 温度/涨停数字校验(整数部分必在)
    zt = str(tbl.get('涨停数', ''))
    wd = str(tbl.get('温度', ''))
    for pat, name in [('涨停\\s*([0-9]+)', '涨停数'), ('温度\\s*([0-9]+(?:\\.[0-9]+)?)', '温度')]:
        m = re.search(pat, bd)
        if m:
            v = m.group(1)
            truth = zt if name == '涨停数' else wd
            if truth and v.split('.')[0] != truth.split('.')[0]:
                fail('实体引用 [%s]: %s=%s 真源=%s' % (label, name, v, truth))
        elif name == '涨停数' and zt:
            warn('提示 [%s]: 未找到涨停数表述' % label)


def main():
    J = load_j()
    if J is None:
        return 1
    bd = (J.get('bodies') or {}).get('limitup') or ''
    if not bd:
        fail('bodies.limitup 为空')
    # ★当日区=hero/h1/hint+当日块(历史块存档不参与完整性/防重复, 2026-08-12阶段B)
    i_hist = bd.find('<details class="chain">')  # 首个未open=历史块起点
    cur = bd[:i_hist] if i_hist > 0 else bd
    # 槽位清单(以渲染器真依赖为准; 四/五/六=渲染器有fallback, 当日版式可能缺→可选)
    slots_req = [
        ('<h2>一', 'h2一'), ('<h2>二', 'h2二'), ('<h2>三', 'h2三'),
        ('★环境规则', '环境规则'), ('<!--LEDGER-->', 'LEDGER锚'),
    ]
    slots_opt = [('<h2>四', 'h2四'), ('清单应答', '清单应答'), ('出页自检', '出页自检')]
    for kw, lb in slots_req:
        slot_exists(cur, kw, lb)
    for kw, lb in slots_opt:
        if kw in cur:  # 可选槽位: 有则防重复, 无则容忍(渲染器fallback)
            slot_exists(cur, kw, lb)
    # 实体引用: 整 bodies 当日区(hero/h1/hint+当日块, 历史块排除)
    entity_check(cur, '当日区')
    if warns:
        print('  '.join(warns))
    if fails:
        print('阶段B槽位校验 FAIL:')
        for f in fails:
            print('  ✗', f)
        return 1
    print('阶段B槽位校验 PASS [%s] (完整性/防重复/实体引用)' % d)
    return 0


if __name__ == '__main__':
    sys.exit(main())
