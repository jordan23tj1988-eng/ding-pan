# -*- coding: utf-8 -*-
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location("release_deploy_under_test", BASE / "release_deploy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_deploy_accepts_only_verified_release(monkeypatch, tmp_path):
    mod = load()
    src = tmp_path / "releases" / "x" / "site"
    src.mkdir(parents=True)
    (src / "cycle.html").write_text("NEW", encoding="utf-8")
    live = tmp_path / "复盘" / "盯盘台"
    live.mkdir(parents=True)
    (live / "cycle.html").write_text("OLD", encoding="utf-8")
    monkeypatch.setattr(mod, "verify_release", lambda root, d: {
        "status": "pass", "errors": [], "d": d, "build_id": "x", "revision": 1,
        "manifest_sha256": "m",
    })
    result = mod.deploy_release(tmp_path, "20260907", site=live)
    assert result["status"] == "pass"
    assert (live / "cycle.html").read_text(encoding="utf-8") == "NEW"
    assert json.loads((tmp_path / ".review_deploy/20260907.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_deploy_rejects_failed_release(monkeypatch, tmp_path):
    mod = load()
    monkeypatch.setattr(mod, "verify_release", lambda root, d: {"status": "fail", "errors": ["bad"]})
    result = mod.deploy_release(tmp_path, "20260907")
    assert result["status"] == "fail"
    assert "release not accepted" in result["errors"]
