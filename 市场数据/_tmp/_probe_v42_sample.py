# -*- coding: utf-8 -*-
"""量测 v42 测试样本页(P1 evidence samples/20260904)在黄金骨架下的证据留痕形态。

只为把测试断言写成"真实现状", 而不是写理想值。
"""
import importlib.util, re, sys, tempfile
from pathlib import Path

P = Path("D:/股票数据/市场数据/tests/test_review_pages_v42_production.py").read_text(encoding="utf-8")
m = re.search(r"SAMPLE\s*=\s*(.+)", P)
print("SAMPLE 定义:", m.group(1) if m else "未找到")

PROD = Path("D:/股票数据/市场数据/review_pages.py")
spec = importlib.util.spec_from_file_location("prod", PROD)
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)

SAMPLE = eval(m.group(1).replace("PROD.parent", str(PROD.parent))) if m else None
print("SAMPLE =", SAMPLE)
with tempfile.TemporaryDirectory(prefix="v42-probe-") as td:
    r = api.build_site(SAMPLE, "20260904", Path(td))
    print("status:", r["status"], r.get("errors"))
    h = Path(r["pages"]["index"]).read_text(encoding="utf-8")
    for k in ('class="claim-proof"', 'claim-anchor-bank', 'href="#evidence-', 'audit-fold',
              'class="citem"', 'reading-spine', '<!--GOLDEN-INDEX:', 'class="obs"', '<h2>',
              'class="routes"', 'class="hb"', '结论', '来源审计'):
        print("  %-22s %d" % (k, h.count(k)))
