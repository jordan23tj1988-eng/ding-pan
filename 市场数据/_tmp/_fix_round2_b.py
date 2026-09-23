# -*- coding: utf-8 -*-
"""2026-09-23 用户5点指正 —— review_pages.py 定点修复(只动概览路由)。"""
from pathlib import Path

root = Path('D:/股票数据/市场数据')
P = root / 'review_pages.py'
t = P.read_text(encoding='utf-8')
done = []

def rep(old, new, label, count=1):
    global t
    n = t.count(old)
    assert n == count, f'{label}: 期望{count} 实测{n}'
    t = t.replace(old, new)
    done.append(label)

# 1) 黄金索引模块导入(段二点评/走马灯同源)
rep('''    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)''',
'''    GOLDEN_INDEX_ON = (route in GOLDEN_INDEX_ROUTES
                       and tuple(x['id'] for x in model['sections']) == GOLDEN_INDEX_SECTIONS)
    # 概览黄金骨架的唯一真源: 段序/卡片形态/走马灯/段二点评都从这里出。
    import module_golden_index as _golden_index''', 'E1 导入')

# 2) 走马灯: 黄金版同款条带(当日真源读数; 取不到的项不出条)
rep('''    ticker=model.get('ticker','')''',
'''    if GOLDEN_INDEX_ON and not model.get('ticker'):
        # 2026-09-23 用户指正「界面和黄金版对比，少跑马灯」: 概览走马灯空条(judgment.ticker 无值)。
        # 概览改由 module_golden_index.ticker_html 按当日真源读数生成; 取不到的项不出条。
        model['ticker'] = _golden_index.ticker_html(model, d)
    ticker=model.get('ticker','')''', 'E2 走马灯')

# 3) h1 = 总审「一句话」(黄金版同形; 原机器串 index路·YYYYMMDD 不再上页)
rep('''    hero_title = model["hero"]["text"]''',
'''    hero_title = model["hero"]["text"]
    if GOLDEN_INDEX_ON and root:
        # 概览 h1 原为机器串「index路·20260922」。黄金版这里是当日判断标题,
        # 故取总审 JSON「一句话」做标题(真源字段, 不改 model/claim, 门禁仍读到原文)。
        _zj = _dated(root, '总审_' + d + '.json', d)
        _hl = str((_zj or {}).get('一句话') or '').strip()
        if _hl:
            hero_title = _hl''', 'E3 h1取总审一句话')

# 4) hero 情绪档 pill: 原取 hero 文本首段(机器串) -> 取温度档 chip
rep('''e(model["hero"]["text"].split('：',1)[0]) + ' · 温度' + e(temp)''',
'''e((model["kpis"][0].get("chip") or '—').split(' ')[0]) + ' · 温度' + e(temp)''', 'E10 情绪档pill')

# 5) 机器数据核对层: 概览不产(用户指正 图1)
rep('''    if mach_parts:''',
'''    if mach_parts and not GOLDEN_INDEX_ON:
        # 2026-09-23 用户拍板(图1): 「机器数据核对层」退出概览结果层。
        # 组件读数仍在 model/components 与模型 JSON 里(供门禁与页内锚点复核)。''', 'E4 机器核对层')

# 6) 来源审计折叠: 概览不产(用户指正 图4/图5); 隐藏证据锚点保留
rep('''    if IS_INDEX:
        body += ('<details class="chain audit-fold" id="audit-fold"><summary><b>来源审计 · 编辑说明与全部证据回链</b><span class="chip">'
                 + str(len(model["editorial_notes"])) + ' 条说明 · ' + str(len(model["evidence"])) + ' 条证据</span></summary><div class="inner">')
    elif route not in AUDIT_FOLD_HIDDEN_ROUTES:''',
'''    if route not in AUDIT_FOLD_HIDDEN_ROUTES and not GOLDEN_INDEX_ON:
        # 2026-09-23 用户拍板(图4/图5): 「来源审计」折叠退出概览结果层。
        # 证据一条不删 —— 编辑说明/全量证据仍在 audit/index.json, claim 原文进无痕原文库,
        # 不可见证据锚点(audit-anchor-bank)留在页内供门禁复核。''', 'E5 审计折叠开')

rep('''    if route in AUDIT_FOLD_HIDDEN_ROUTES:
        hidden_evidence_anchors''',
'''    if route in AUDIT_FOLD_HIDDEN_ROUTES or GOLDEN_INDEX_ON:
        hidden_evidence_anchors''', 'E6 证据锚点保留')

rep('''    if route not in AUDIT_FOLD_HIDDEN_ROUTES:
        if limits_html:''',
'''    if route not in AUDIT_FOLD_HIDDEN_ROUTES and not GOLDEN_INDEX_ON:
        if limits_html:''', 'E7 审计折叠体')

# 7) 本页阅读地图(JS 运行时注入): 概览不产(用户指正 图1)
rep('''' + VISUAL_JS + '</body></html>\\n\'''',
''' + ('' if GOLDEN_INDEX_ON else VISUAL_JS) + '</body></html>\\n\'''', 'E8 页内导航JS')

# 8) 段二点评真源(总审 环境加权依据)
rep('''        golden_bodies = _golden_index.build(model, d)''',
'''        _zj_env = _dated(root, '总审_' + d + '.json', d) if root else None
        golden_bodies = _golden_index.build(model, d,
                                           env_basis=str((_zj_env or {}).get('环境加权依据') or ''))''',
'E9 段二点评真源')

P.write_text(t, encoding='utf-8', newline='\n')
print('\n'.join('OK  ' + d for d in done))
