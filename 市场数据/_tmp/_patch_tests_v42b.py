# -*- coding: utf-8 -*-
"""v42 生产验收测试: 概览断言改为"量与实测一致"版本(2026-09-23)。

实测基线(20260904 样本 / 黄金骨架):
  h2=4, GOLDEN-INDEX 标记=4, class="citem"=0, class="reading-spine"=0,
  claim-anchor-bank=2, id="evidence-*"=166, id="audit-fold"=1, page-map JS=1
判断卡退场 ⇒ class="claim-proof" 与 href="#evidence-*" 不再出现(证据改由隐藏锚点+无痕原文库承接),
故不再断言这两项。
"""
from pathlib import Path

T = Path("D:/股票数据/市场数据/tests/test_review_pages_v42_production.py")
s = T.read_bytes().decode("utf-8").replace("\r\n", "\n")

old = """        # 页内导航(本页阅读地图)由 page-map JS 运行时注入; 黄金骨架不带静态锚点列表,
        # 故这里锁 JS 生成器在场, 不再锁静态 href="#<sid>"。
        assert "map.className='page-map'" in html
        assert 'class="reading-spine"' not in html, '概览阅读条已撤(2026-09-23)'
        assert 'class="citem"' not in html, '概览结果层不再铺判断卡'
        assert 'claim-anchor-bank' in html, 'claim 原文必须留痕(无痕原文库, 一条不删)'
        assert 'class="claim-proof"' in html, '证据回链仍在'
        for label in ("结论", "来源审计"):
            assert label in html
        assert 'href="#audit-fold"' in html"""

new = """        # 页内导航(本页阅读地图)由 page-map JS 运行时注入; 黄金骨架不带静态锚点列表,
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

assert s.count(old) == 1, "anchor not unique"
T.write_bytes(s.replace(old, new).encode("utf-8"))
print("OK v42 index assertions synced to measured reality")
