# -*- coding: utf-8 -*-
"""账本引擎回归：幂等、升版/替代、缺失行情不造数、统计口径。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _ops.ledger as ledger


def setup_env(tmp_path, monkeypatch):
    learn = tmp_path / "learn"
    bars = learn / "_bars_cache"
    bars.mkdir(parents=True)
    (bars / "000001.csv").write_text(
        "date,open,high,low,close,volume,turnover,circ_mv亿\n"
        "2026-01-05,9.5,10.0,9.4,9.9,1,,\n"
        "2026-01-06,10.0,11.2,9.9,11.0,1,,\n", encoding="utf-8")
    (bars / "000002.csv").write_text(
        "date,open,high,low,close,volume,turnover,circ_mv亿\n"
        "2026-01-06,10.0,10.1,8.9,9.0,1,,\n", encoding="utf-8")
    judgment = {"日期": "20260105", "路": "limitup", "荐票": {"标的": [
        {"代码": "000001", "名称": "票一", "类型": "荐票", "理由": "r1"},
        {"代码": "000002", "名称": "票二", "类型": "观察", "理由": "r2"},
    ]}}
    (learn / "limitup判断_20260105.json").write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(ledger, "LEARN", learn)
    monkeypatch.setattr(ledger, "BARS", bars)
    monkeypatch.setattr(ledger, "DB", tmp_path / "ledger.db")
    return learn, judgment


def test_ingest_idempotent_and_stats(tmp_path, monkeypatch):
    setup_env(tmp_path, monkeypatch)
    first = ledger.ingest("20260101", "20260131")
    assert first["recs"] == 2 and first["settled"] == 2 and first["unsettled"] == 0
    second = ledger.ingest("20260101", "20260131")
    assert second["inserted"] == 0 and second["superseded"] == 0 and second["unchanged"] == 2
    executed = ledger.stats("20260101", "20260131", kind="荐票")
    assert executed["n"] == 1
    assert executed["routes"]["limitup"]["mean_pct"] == 10.0
    assert executed["routes"]["limitup"]["n"] == 1
    all_kinds = ledger.stats("20260101", "20260131", kind="all")
    assert all_kinds["n"] == 2 and all_kinds["all"]["mean_pct"] == 0.0
    assert ledger.verify()["duplicate_current_rec"] == 0


def test_payload_change_supersedes(tmp_path, monkeypatch):
    learn, judgment = setup_env(tmp_path, monkeypatch)
    ledger.ingest("20260101", "20260131")
    judgment["荐票"]["标的"][0]["名称"] = "票一改名"
    (learn / "limitup判断_20260105.json").write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")
    result = ledger.ingest("20260101", "20260131")
    assert result["rec_superseded"] == 1
    import sqlite3
    con = sqlite3.connect(str(ledger.DB))
    rows = con.execute("SELECT name,is_current,version FROM rec WHERE code='000001' ORDER BY version").fetchall()
    assert rows == [("票一", 0, 1), ("票一改名", 1, 2)]


def test_missing_t1_is_unsettled_not_fabricated(tmp_path, monkeypatch):
    learn, judgment = setup_env(tmp_path, monkeypatch)
    (learn / "_bars_cache" / "000001.csv").write_text(
        "date,open,high,low,close,volume,turnover,circ_mv亿\n2026-01-05,9.5,10,9.4,9.9,1,,\n",
        encoding="utf-8")
    result = ledger.ingest("20260101", "20260131")
    assert result["unsettled"] == 1
    stats = ledger.stats("20260101", "20260131", kind="all")
    assert stats["n"] == 1  # 只剩 000002 有 T+1


def test_bootstrap_is_deterministic():
    a = ledger.bootstrap_ci([1.0, 2.0, 3.0, 4.0])
    b = ledger.bootstrap_ci([1.0, 2.0, 3.0, 4.0])
    assert a == b and a[0] <= a[1]


def test_kind_normalization_never_promotes_observation():
    assert ledger.normalize_kind("荐票") == "荐票"
    assert ledger.normalize_kind("荐(轻仓)") == "荐票"
    assert ledger.normalize_kind("观察(非荐)") == "观察"
    assert ledger.normalize_kind("涨停首板(1/1)") == "观察"
    assert ledger.normalize_kind(None) == "观察"
