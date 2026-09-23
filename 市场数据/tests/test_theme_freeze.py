import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATE = "20260910"


def load_generator(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("tested_theme_generator", ROOT / "生成盯盘台.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    site = tmp_path / "复盘" / "盯盘台"
    site.mkdir(parents=True)
    module.BASE = str(tmp_path)
    module.SITE = str(site)
    module.ARC = str(site / "archive")
    module.L = str(tmp_path / "_学习")
    return module, site


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_postprocess_rejects_live_theme(monkeypatch, tmp_path):
    module, site = load_generator(monkeypatch, tmp_path)
    (site / "theme.html").write_text("accepted", encoding="utf-8")
    with pytest.raises(RuntimeError, match="拒绝对现站 theme.html 后处理"):
        module._postprocess_site(site, DATE)


def test_same_day_deploy_skips_theme_copy(monkeypatch, tmp_path):
    module, site = load_generator(monkeypatch, tmp_path)
    accepted = site / "theme.html"
    accepted.write_text("accepted-theme", encoding="utf-8")
    freeze = {
        "schema_version": 1,
        "d": DATE,
        "build_id": "20260910-7-" + "a" * 32,
        "theme_sha256": sha(accepted),
        "policy": "same-day-theme-immutable",
    }
    (site / ".theme_page_freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    release = tmp_path / "release" / "site"
    release.mkdir(parents=True)
    for name in ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup"):
        (release / (name + ".html")).write_text("accepted-theme" if name == "theme" else name, encoding="utf-8")
    calls = []
    real_copy = shutil.copy2
    def record_copy(src, dst, *args, **kwargs):
        calls.append(Path(dst).name)
        return real_copy(src, dst, *args, **kwargs)
    result = {"release_dir": str(tmp_path / "release"), "build_id": freeze["build_id"],
              "stage_postprocess": {"ok": True}}
    with patch("shutil.copy2", side_effect=record_copy):
        module._deploy_site(DATE, result)
    assert accepted.read_text(encoding="utf-8") == "accepted-theme"
    assert "theme.html" not in calls
    assert set(calls) == {"index.html", "cycle.html", "auction.html", "lhb.html", "logic.html", "limitup.html"}


def test_same_day_tamper_blocks_deploy(monkeypatch, tmp_path):
    module, site = load_generator(monkeypatch, tmp_path)
    accepted = site / "theme.html"
    accepted.write_text("tampered", encoding="utf-8")
    freeze = {"schema_version": 1, "d": DATE, "theme_sha256": "0" * 64}
    (site / ".theme_page_freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    release = tmp_path / "release" / "site"
    release.mkdir(parents=True)
    for name in ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup"):
        (release / (name + ".html")).write_text(name, encoding="utf-8")
    with pytest.raises(RuntimeError, match="主题页冻结被破坏"):
        module._deploy_site(DATE, {"release_dir": str(tmp_path / "release"), "stage_postprocess": {"ok": True}})


def test_review_publish_freeze_rejects_changed_candidate(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT))
    import review_publish
    root = tmp_path / "root"
    stage = tmp_path / "stage"
    freeze_dir = root / "复盘" / "盯盘台"
    freeze_dir.mkdir(parents=True)
    stage.mkdir()
    (freeze_dir / ".theme_page_freeze.json").write_text(json.dumps({
        "schema_version": 1, "d": DATE, "theme_sha256": "0" * 64
    }), encoding="utf-8")
    (stage / "theme.html").write_text("changed", encoding="utf-8")
    errors = review_publish.validate_theme_freeze(root, stage, DATE)
    assert errors and "theme freeze violation" in errors[0]
