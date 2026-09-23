# -*- coding: utf-8 -*-
"""2026-09-23 第2轮: 同步 v42 测试断言 + 哨兵 C15 新不变量。"""
from pathlib import Path

root = Path('D:/股票数据/市场数据')
done = []

# ---- 1) tests/test_review_pages_v42_production.py ----
p = root / 'tests/test_review_pages_v42_production.py'
t = p.read_text(encoding='utf-8')
old = """        # 页内导航(本页阅读地图)由 page-map JS 运行时注入; 黄金骨架不带静态锚点列表,
        # 故这里锁 JS 生成器在场, 不再锁静态 href="#<sid>"。
        assert "map.className='page-map'" in html
        assert 'class="reading-spine"' not in html, '概览阅读条已撤(2026-09-23)'
        assert 'class="citem"' not in html, '概览结果层不再铺判断卡'
        # 证据不删(用户口径: 页面不展示, 体系内部保留): 判断卡退场后,
        # claim 原文进页尾无痕原文库, 隐藏证据锚点与来源审计折叠仍在, 门禁可复核。
        assert 'claim-anchor-bank' in html, 'claim 原文必须留痕(无痕原文库)'
        assert 'id="evidence-' in html, '隐藏证据锚点必须保留'
        assert 'id="audit-fold"' in html, '来源审计折叠仍在'
        for label in ("结论", "来源审计"):
            assert label in html"""
new = """        # 2026-09-23 用户指正(图1): 概览页内导航(page-map JS 运行时注入)与
        # 机器数据核对层折叠一并退出结果层; 黄金版本来就没有这两样。
        assert "map.className='page-map'" not in html, '概览页内导航已撤(2026-09-23)'
        assert '机器数据核对层' not in html, '机器数据核对层退出概览结果层(2026-09-23)'
        assert 'class="reading-spine"' not in html, '概览阅读条已撤(2026-09-23)'
        assert 'class="citem"' not in html, '概览结果层不再铺判断卡'
        # 证据不删(用户口径: 页面不展示, 体系内部保留): claim 原文进页尾无痕原文库,
        # 隐藏证据锚点仍在; 来源审计折叠本身退出概览结果层(图4/图5)。
        assert 'claim-anchor-bank' in html, 'claim 原文必须留痕(无痕原文库)'
        assert 'id="evidence-' in html, '隐藏证据锚点必须保留'
        assert 'id="audit-fold"' not in html, '来源审计折叠退出概览结果层(2026-09-23)'
        assert '结论' in html
        # 用户指正: 概览走马灯此前是空条; obs 卡此前不显示票名与身位(被 v4.4 去噪规则吃掉)。
        assert 'class="obs-nm"' in html, '概览 obs 卡必须带票名(黄金版形态)'
        assert '.obs-head .obs-nm,.obs-watch>.obs-lab{display:none}' not in html, \\
            '概览页不得再隐藏票名/身位'
        assert 'class="ticker"' in html"""
assert t.count(old) == 1, 'v42 断言块未匹配'
p.write_text(t.replace(old, new), encoding='utf-8', newline='\n')
done.append('tests/test_review_pages_v42_production.py 断言同步')

# ---- 2) 复盘一致性哨兵.py C15 追加不变量 ----
p = root / '复盘一致性哨兵.py'
t = p.read_text(encoding='utf-8')
old = """        if _oh.count('class="obs"') > 5:
            FAIL.append('C15 概览 .obs 卡 %d 张 > 5(Top5 上限)' % _oh.count('class="obs"'))"""
new = """        if _oh.count('class="obs"') > 5:
            FAIL.append('C15 概览 .obs 卡 %d 张 > 5(Top5 上限)' % _oh.count('class="obs"'))
        # 2026-09-23 用户指正(图1/图4/图5): 机器数据核对层/来源审计折叠/页内导航退出概览结果层;
        # 走马灯必须有当日读数(此前空条); obs 卡必须带票名与身位(此前被去噪规则隐藏)。
        for _bad, _why in (('机器数据核对层', '机器数据核对层折叠'),
                           ('id="audit-fold"', '来源审计折叠'),
                           ("map.className='page-map'", '页内导航(本页阅读)')):
            if _bad in _oh:
                FAIL.append('C15 概览页又出现%s(2026-09-23 已退出结果层)' % _why)
        _tk = ''
        if '<div class="ticker">' in _oh:
            _tk = _oh.split('<div class="ticker">', 1)[1].split('</div></div></div>', 1)[0]
        if len(_tk) < 60:
            FAIL.append('C15 概览走马灯为空或过短(%d 字符)——黄金版是当日读数条带' % len(_tk))
        if 'class="obs-nm"' not in _oh:
            FAIL.append('C15 概览 .obs 卡缺票名(.obs-nm)——黄金版卡头是「名称+代码」')
        if '.obs-head .obs-nm,.obs-watch>.obs-lab{display:none}' in _oh:
            FAIL.append('C15 概览页内又写入隐藏票名/身位的去噪规则')"""
assert t.count(old) == 1, 'C15 obs 上限块未匹配'
p.write_text(t.replace(old, new), encoding='utf-8', newline='\n')
done.append('复盘一致性哨兵.py C15 追加5项不变量')

print('\n'.join('OK  ' + d for d in done))
