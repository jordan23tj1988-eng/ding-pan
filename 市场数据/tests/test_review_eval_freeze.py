"""真实档案复制 + 明确的受控元数据错误注入；不伪造行情。"""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import pytest

BASE = Path(__file__).resolve().parents[2]

@pytest.fixture
def api():
    spec = importlib.util.find_spec("review_eval")
    if spec is None:
        class MissingAPI:
            def __getattr__(self, name):
                def missing(*args, **kwargs):
                    pytest.fail("P3 implementation is missing: " + name)
                return missing
        return MissingAPI()
    import review_eval
    return review_eval

@pytest.fixture
def sandbox():
    with tempfile.TemporaryDirectory(prefix="p3-", dir=BASE / "evidence" / "tmp") as path:
        root = Path(path) / "input"
        shutil.copytree(BASE / "evidence" / "real_samples", root)
        yield root, Path(path) / "out"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

def test_real_freeze_is_engineering_only_with_six_sources(api, sandbox):
    root, out = sandbox
    result = api.freeze_case(root, "20260904", out)
    assert result["status"] == "ok", result
    case = read(out / "case.json")
    assert case["schema_version"] == 1
    assert case["meta"]["d"] == "20260904"
    assert case["meta"]["replay_status"] == "engineering_only"
    assert case["meta"]["missing_as_of"] == [s["source_id"] for s in case["sources"]]
    assert len(case["sources"]) == 6
    assert case["sources"][0]["data"]["facts"]["温度"]["value"] == 13.4
    prompt = (out / "prompt.txt").read_text(encoding="utf-8")
    assert "相反证据" in prompt and "source_id" in prompt
    assert all("总审_" not in s["source_path"] for s in case["sources"])
    for source in case["sources"][1:]:
        assert set(source["data"]) == {"判断"}
        assert set(source["data"]["判断"]) == {"结论", "证据", "档位", "独立盲区声明"}
    assert api.verify_case(out / "case.json")["status"] == "ok"

@pytest.mark.parametrize("d", ["2026-09-04", "2026094", "20260230", "２０２６０９０４"])
def test_strict_date(api, sandbox, d):
    root, out = sandbox
    assert api.freeze_case(root, d, out)["status"] == "fail"
    assert not (out / "case.json").exists()

@pytest.mark.parametrize("change", ["date", "as_of", "nested_as_of", "build_time"])
def test_reject_future_source_metadata(api, sandbox, change):
    root, out = sandbox
    path = root / "_学习" / "fact_20260904.json"
    data = read(path)
    if change == "nested_as_of":
        data["facts"]["温度"]["as_of"] = "2026-09-07T15:00:00+08:00"
    else:
        data[change] = "20260907" if change == "date" else "2026-09-07T15:00:00+08:00"
    write(path, data)
    result = api.freeze_case(root, "20260904", out)
    assert result["status"] == "fail", result
    assert "future" in str(result["errors"]) or "date" in str(result["errors"])

def test_ignores_future_files_and_keeps_null(api, sandbox):
    root, out = sandbox
    path = root / "_学习" / "fact_20260904.json"
    data = read(path); data["facts"]["温度"]["value"] = None
    write(path, data)
    (root / "_学习" / "fact_20260907.json").write_text("invalid_future_sentinel", encoding="utf-8")
    assert api.freeze_case(root, "20260904", out)["status"] == "ok"
    assert read(out / "case.json")["sources"][0]["data"]["facts"]["温度"]["value"] is None

def test_missing_route_fails(api, sandbox):
    root, out = sandbox
    (root / "_学习" / "theme判断_20260904.json").unlink()
    assert api.freeze_case(root, "20260904", out)["status"] == "fail"

def test_freeze_does_not_overwrite(api, sandbox):
    root, out = sandbox
    assert api.freeze_case(root, "20260904", out)["status"] == "ok"
    before = (out / "case.json").read_bytes()
    assert api.freeze_case(root, "20260904", out)["status"] == "fail"
    assert before == (out / "case.json").read_bytes()

@pytest.mark.parametrize("target", ["case", "snapshot", "prompt"])
def test_reject_tampering(api, sandbox, target):
    root, out = sandbox
    assert api.freeze_case(root, "20260904", out)["status"] == "ok"
    case = read(out / "case.json")
    path = {"case": out/"case.json", "snapshot": out/case["sources"][0]["snapshot"], "prompt": out/"prompt.txt"}[target]
    path.write_bytes(path.read_bytes() + b" ")
    result = api.verify_case(out / "case.json")
    assert result["status"] == "fail", result
    assert "hash" in str(result["errors"])
