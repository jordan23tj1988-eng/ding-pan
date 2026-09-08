# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gate", BASE / "p1_p2_capability_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_gate_reports_missing_as_fail(tmp_path):
    (tmp_path / "review_learning.py").write_text("# alt", encoding="utf-8")
    result = gate.check(tmp_path, "20260907")
    assert result["status"] == "fail"
    assert "risk_calendar" in result["hard_missing"]
    assert any(r["key"] == "cognition_pack" and r["status"] == "available" for r in result["capabilities"])


def test_gate_passes_when_all_hard_inputs_exist(tmp_path):
    for name in ["风险日历.py", "竞价撤单差分.py", "开盘验证维.py", "日内温度曲线.py", "日内轮动图谱.py", "题材归位.py"]:
        (tmp_path / name).write_text("# test", encoding="utf-8")
    result = gate.check(tmp_path, "20260907")
    assert result["status"] == "pass"
    assert result["hard_missing"] == []
