# -*- coding: utf-8 -*-
"""C3/C12 历史日边界回归(2026-10-20, 用户批准 A+B)。

动机: 收口链(22:45 closeout)连续 4 次(10/14、10/16、10/18、10/20)因**历史日**复核失败而中断:
  - C3 判据是"看板mtime >= 活bars_cache最新mtime", 而缓存每日盘后前移 ⇒ 任何非当日复核必然 FAIL;
  - C12 拿**活站页面** + **活分档库**去比历史日 ⇒ 页面本身正确也必 FAIL(分档库口径本来就是 d 日窗口止 d-1、每晚重算净化)。

修正后必须锁死三条, 防"降级"变"放水":
  1) 历史日 + 看板mtime日 < 目标日 ⇒ 仍是 FAIL(旧价看板被重跑/inject = 07-15 事故形态);
  2) 出页当日(d==今天) + 页面早于当日取数 ⇒ 仍是 FAIL;
  3) 历史日 + 看板不早于目标日 + 缓存已前移 ⇒ 降 WARN, 文本含"历史日边界";
  4) 分档库基准: 活库已前移且有目标日快照 ⇒ 用快照; 活库==d 或 d>=今天 ⇒ 用活库(强校验); 无快照 ⇒ 用活库(仍严格)。
"""
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '复盘一致性哨兵.py'


def _ts(*args):
    """(y, m, d, H, M) -> epoch 秒, 便于构造受控 mtime。"""
    return datetime.datetime(*args).timestamp()


def run_c3(tmp_path, d, page_mtime_date, cache_delta_s=0):
    """执行哨兵 C3 代码块(受控 mtime), 返回 (FAIL, WARN)。"""
    learning = tmp_path / '_学习'
    cache = learning / '_bars_cache'
    cache.mkdir(parents=True)
    now = datetime.datetime.now()
    csvp = cache / '000001.csv'
    csvp.write_text('d,c\n', encoding='utf-8')
    os.utime(csvp, (now.timestamp() + cache_delta_s, now.timestamp() + cache_delta_s))
    route = 'lhb'
    kbd = learning / '_模拟盘' / route
    kbd.mkdir(parents=True)
    kb = kbd / f'看板_{d}.html'
    kb.write_text('<html></html>', encoding='utf-8')
    os.utime(kb, (page_mtime_date, page_mtime_date))

    text = SOURCE.read_text(encoding='utf-8')
    block = text.split('# ---------- C3', 1)[1].split('# ---------- C4', 1)[0]
    block = '# ---------- C3' + block
    env = {'os': os, 'datetime': datetime, 'L': str(learning), 'd': d,
           'PAGE': [route], 'FAIL': [], 'WARN': []}
    exec(compile(block, str(SOURCE), 'exec'), env)
    return env['FAIL'], env['WARN']


def test_old_page_before_target_day_still_fails(tmp_path):
    """看板mtime日 < 目标日 ⇒ 真旧页, 仍 FAIL(不得被历史日边界降级掩盖)。"""
    fail, warn = run_c3(tmp_path, '20260105', _ts(2025, 12, 20, 9, 30))
    assert len(fail) == 1 and '早于目标日' in fail[0], (fail, warn)
    assert warn == [], warn


def test_historical_day_cache_ahead_downgrades_to_warn(tmp_path):
    """历史日 + 看板不早于目标日 + 缓存已前移 ⇒ WARN(历史日边界), FAIL 不增加。"""
    d = '20260105'
    fail, warn = run_c3(tmp_path, d, _ts(2026, 1, 6, 19, 45))
    assert fail == [], fail
    assert len(warn) == 1 and '历史日边界' in warn[0], warn
    assert f'看板_{d}.html' in warn[0]


def test_same_day_page_older_than_cache_still_fails(tmp_path):
    """出页当日(d==今天) 页面早于当日取数 ⇒ 仍 FAIL。"""
    today = datetime.date.today().strftime('%Y%m%d')
    now = datetime.datetime.now()
    fail, warn = run_c3(tmp_path, today, (now - datetime.timedelta(hours=3)).timestamp(), cache_delta_s=0)
    assert len(fail) == 1 and '出页当日' in fail[0], (fail, warn)
    assert warn == [], warn


def test_page_newer_than_cache_no_issue(tmp_path):
    """看板晚于缓存(正常出页) ⇒ 无 FAIL 无 WARN。"""
    d = '20260105'
    now = datetime.datetime.now()
    fail, warn = run_c3(tmp_path, d, (now + datetime.timedelta(minutes=30)).timestamp())
    assert fail == [] and warn == [], (fail, warn)


# ---------------- C12 分档库基准 ----------------


def _load_checker():
    sys.path.insert(0, str(ROOT))
    import importlib
    return importlib.import_module('lhb数据核对')


def test_load_snapshot_picks_target_day(tmp_path, monkeypatch):
    """快照 jsonl 多行时, 必须精确取目标日那一行(零后视镜)。"""
    m = _load_checker()
    p = tmp_path / '_席位分档快照.jsonl'
    rows = [
        {'日': '20261016', '窗口': '20260401~20261015', '笔数': 18601, '档分布': {'P': 167, 'S': 18}},
        {'日': '20261019', '窗口': '20260401~20261016', '笔数': 18698, '档分布': {'P': 165, 'S': 18}},
        {'日': '20261020', '窗口': '20260401~20261019', '笔数': 18815, '档分布': {'P': 165, 'S': 19}},
    ]
    p.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')
    monkeypatch.setattr(m, 'L', str(tmp_path))
    snap = m.load_snapshot('20261019')
    assert snap and snap['笔数'] == 18698 and snap['窗口'] == '20260401~20261016', snap
    assert m.load_snapshot('20260930') is None


def test_baseline_uses_live_when_same_day():
    """活库更新==d(当期) ⇒ 用活库, 强校验不放水。"""
    m = _load_checker()
    lib = {'更新': '20261020', '窗口': 'a~b', '笔数': 1, '席位': {}}
    base, note = m.pick_lib_baseline(lib, {'窗口': 'x~y', '笔数': 9}, '20261020', today='20261020')
    assert base is lib and note == '活库', (base, note)


def test_baseline_uses_snapshot_when_live_ahead():
    """活库已前移 + 有目标日快照 ⇒ 用目标日快照(页面当日正确性由快照判定)。"""
    m = _load_checker()
    lib = {'更新': '20261020', '窗口': '20260401~20261019', '笔数': 18815, '席位': {}}
    snap = {'日': '20261019', '窗口': '20260401~20261016', '笔数': 18698,
            '档分布': {'P': 165, 'S': 18, 'A': 44, 'B': 135, 'C': 88}}
    base, note = m.pick_lib_baseline(lib, snap, '20261019', today='20261020')
    assert base['笔数'] == 18698 and base['窗口'] == '20260401~20261016', base
    assert base['档分布']['B'] == 135, base
    assert '目标日快照20261019' == note, note


def test_baseline_falls_back_to_live_without_snapshot():
    """无目标日快照 ⇒ 退回活库(仍严格, 该 FAIL 的照样 FAIL, 不静默放过)。"""
    m = _load_checker()
    lib = {'更新': '20261020', '窗口': '20260401~20261019', '笔数': 18815, '席位': {}}
    base, note = m.pick_lib_baseline(lib, None, '20261019', today='20261020')
    assert base is lib, base
    assert '降级严格' in note, note
