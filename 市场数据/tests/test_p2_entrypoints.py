# -*- coding: utf-8 -*-
import importlib.util
import json
from pathlib import Path
import pytest

BASE = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_playbook_aggregates_current_plans_without_old_watch(tmp_path):
    root = tmp_path
    learn = root / "_学习"
    learn.mkdir()
    (learn / "交易计划_master_20260907.json").write_text(json.dumps({
        "日期": "20260907", "路": "master", "buys": [], "sells": [], "notes": "当前 master"
    }, ensure_ascii=False), encoding="utf-8")
    (learn / "交易计划_logic_20260907.json").write_text(json.dumps({
        "日期": "20260907", "路": "logic", "buys": [{"代码": "002463"}], "sells": [], "notes": "logic only"
    }, ensure_ascii=False), encoding="utf-8")
    old = root / "盘中" / "20260907" / "playbook.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps({"date": "20260907", "watch": [{"code": "OLD"}], "notes": "0904残留"}), encoding="utf-8")
    mod = load("playbook生成")
    result = mod.build(root, "20260907", old)
    assert result["watch"] == []
    assert result["buys"] == []
    assert result["route_plans"][0]["route"] == "logic"
    assert "0904残留" not in old.read_text(encoding="utf-8")


def test_settlement_entrypoints_require_explicit_arguments():
    pred = load("预判结算")
    audit = load("盘中账本结算")
    with pytest.raises(SystemExit):
        pred.main(["20260907", "--root", str(BASE)])
    with pytest.raises(SystemExit):
        audit.main(["20260907", "--root", str(BASE)])
