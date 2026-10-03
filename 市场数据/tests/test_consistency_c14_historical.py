# -*- coding: utf-8 -*-
"""C14 历史日边界降级回归(2026-10-01 #219)。

动机: 每路能力块的"字节一致"基准由 能力进化模块.build(root,d,route) 从活账本现场重算,
账本一旦在页面发布之后被写(新增能力/写命中/重建), 历史日的基准就随之前移, 事后复核该历史日
必然失配——这不是回归。此处锁死两条:
  1) 账本 mtime 晚于页面 mtime ⇒ 该条降 WARN(历史日边界), 且 WARN 文本写明两个时间戳;
  2) 账本不晚于页面(正常发布顺序: 先写账本后出页) ⇒ 仍是 FAIL, 真回归不得被 WARN 掩盖;
  3) 结构性缺块(数量/锚/样式/旧标题/编号) 不受降级影响, 一律 FAIL。
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '复盘一致性哨兵.py'

STUB = '''# -*- coding: utf-8 -*-
ROUTES = ['lhb']
BYTE = '能力模块字节与当日唯一真源不一致'

def verify_page(html, route, root=None, d=None):
    probs = []
    if 'STRUCT_BROKEN' in html:
        probs.append('能力模块数量!=2 (1)')
    if 'MISMATCH' in html:
        probs.append(BYTE)
    return probs
'''


def run_c14(tmp_path, page_body, ledger_mtime, page_mtime):
    root = tmp_path
    site = tmp_path / 'site'
    site.mkdir()
    (root / '能力进化模块.py').write_text(STUB, encoding='utf-8')
    page = site / 'lhb.html'
    page.write_text(page_body, encoding='utf-8')
    learning = root / '_学习'
    learning.mkdir()
    led = learning / '能力进化库_自主拓展.json'
    led.write_text('{"records":[]}', encoding='utf-8')
    os.utime(led, (ledger_mtime, ledger_mtime))
    os.utime(page, (page_mtime, page_mtime))
    text = SOURCE.read_text(encoding='utf-8')
    block = text.split('# ---------- C14', 1)[1].split('# ---------- C15', 1)[0]
    block = '# ---------- C14' + block
    env = {'os': os, 'glob': __import__('glob'), 'json': __import__('json'),
           'datetime': __import__('datetime'), 'R': str(root), 'L': str(learning),
           'SITE': str(site), 'd': '20260930', 'FAIL': [], 'WARN': [],
           'REVIEW_STAGE': str(site)}
    # REVIEW_STAGE 由块内通过 os.environ 读取, 这里注入最小环境
    os.environ['REVIEW_STAGE'] = str(site)
    try:
        exec(compile(block, str(SOURCE), 'exec'), env)
    finally:
        os.environ.pop('REVIEW_STAGE', None)
    return env['FAIL'], env['WARN']


def test_ledger_newer_than_page_downgrades_to_warn(tmp_path):
    """账本晚于页面 ⇒ 降 WARN(历史日边界), 且带两个时间戳, FAIL 不增加。"""
    fail, warn = run_c14(tmp_path, '<html>MISMATCH</html>', ledger_mtime=2_000_000, page_mtime=1_999_000)
    assert fail == [], fail
    assert len(warn) == 1, warn
    assert '历史日边界' in warn[0]
    assert '能力账本晚于页面' in warn[0]
    assert warn[0].count(':') >= 4  # 两个 %H:%M:%S 时间戳
    assert 'lhb.html' in warn[0]


def test_page_newer_than_ledger_still_fails(tmp_path):
    """账本不晚于页面 ⇒ 仍是 FAIL(真回归不得被 WARN 掩盖)。"""
    fail, warn = run_c14(tmp_path, '<html>MISMATCH</html>', ledger_mtime=1_999_000, page_mtime=2_000_000)
    assert len(fail) == 1 and '能力模块字节与当日唯一真源不一致' in fail[0], (fail, warn)
    assert warn == [], warn


def test_structurally_broken_page_fails_regardless_of_mtime(tmp_path):
    """结构缺块(数量/锚/样式等)不受降级影响, 一律 FAIL。"""
    fail, warn = run_c14(tmp_path, '<html>STRUCT_BROKEN</html>', ledger_mtime=2_000_000, page_mtime=1_999_000)
    assert len(fail) == 1 and '数量!=2' in fail[0], (fail, warn)
    assert warn == [], warn
