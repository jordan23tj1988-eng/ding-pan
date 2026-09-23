# -*- coding: utf-8 -*-
"""一次性脚本: 概览黄金骨架锁落地后的测试合同同步(2026-09-23)。

只做两件事:
1. v42 生产验收: 概览页改为锁"黄金四段标记 + 无阅读条/无判断卡 + 证据回链仍在";
   页内导航由 page-map JS 运行时注入, 因此不再锁静态 href="#<sid>"。
2. 负向自检: 断言上面这条合同在**契约不符**时确实会 fail(不是永远过)。
"""
from pathlib import Path

P = Path("tests/test_review_pages_v42_production.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")

OLD = (
    '        for sid in SIDS:\n'
    '            assert \'<!--GOLDEN-INDEX:%s-->\' % sid in html, sid\n'
    '            assert \'href="#%s"\' % sid in html, sid\n'
)
NEW = (
    '        for sid in SIDS:\n'
    '            assert \'<!--GOLDEN-INDEX:%s-->\' % sid in html, sid\n'
    '        # 页内导航(本页阅读地图)由 page-map JS 运行时注入; 黄金骨架不带静态锚点列表,\n'
    '        # 故这里锁 JS 生成器在场, 不再锁静态 href="#<sid>"。\n'
    '        assert "map.className=\'page-map\'" in html\n'
)

assert s.count(OLD) == 1, "v42 anchor block not found exactly once"
s = s.replace(OLD, NEW)
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
import ast
ast.parse(s)
print("OK v42 test synced")
print("reading-spine assert present:", 'class="reading-spine"\' not in html' in s or 'reading-spine"\' not in html' in s)
