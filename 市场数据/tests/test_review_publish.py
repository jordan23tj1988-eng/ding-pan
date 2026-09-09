"""P0 tests: copied real judgment; mock checks are CONTROLLED TEST INJECTION only."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TASK = Path(os.environ.get("SENTIMENT_P2_TASK", str(Path(__file__).resolve().parents[2] / "codex_workspace" / "stability-20260906" / "p2")))
CODE = TASK / "root"
sys.path.insert(0, str(CODE))
PROD = Path("D:/股票数据/市场数据")
D = "20260902"
ROUTES = ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup")

# A real temporary Python module implements the independent P1 interface.
# Content is copied from real judgment, never invented market values.
BUILDER = r'''import json
from pathlib import Path

def build_site(root, d, stage_dir):
    j = json.loads((root / "_学习" / ("judgment_" + d + ".json")).read_text(encoding="utf-8"))
    stage_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for route, body in j["bodies"].items():
        p = stage_dir / (route + ".html")
        p.write_text('<html data-d="' + d + '" data-schema-version="1"><head><title>' + route + '</title></head><body>' + body + '</body></html>', encoding="utf-8")
        pages.append({"route": route, "path": str(p), "status": "pass", "errors": []})
    return {"status": "pass", "d": d, "pages": pages, "errors": [], "template_version": "1"}
'''

class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import review_publish
        cls.api = review_publish

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p0-", dir=TASK / "evidence")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "_学习").mkdir()
        self.jpath = self.root / "_学习" / f"judgment_{D}.json"
        shutil.copy2(PROD / "_学习" / f"judgment_{D}.json", self.jpath)
        (self.root / "review_pages.py").write_text(BUILDER, encoding="utf-8")
        self.checks = patch.object(self.api, "run_checks", side_effect=lambda *a: [
            {"name": n, "status": "pass", "errors": [], "test_injection": True}
            for n in self.api.REQUIRED_CHECKS])
        self.checks.start()
        self.addCleanup(self.checks.stop)

    def edit(self, fn):
        j = json.loads(self.jpath.read_text(encoding="utf-8"))
        fn(j)
        self.jpath.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")

    def build(self, **kw):
        return self.api.build_release(self.root, D, **kw)

    def assertBlocked(self, result, text):
        self.assertEqual(result.get("status"), "fail", result)
        self.assertIn(text, " ".join(result.get("errors", [])), result)

    def test_missing_cycle_does_not_change_current(self):
        current = self.root / "CURRENT.json"
        current.write_text('{"old": "unaccepted fixture"}', encoding="utf-8")
        self.edit(lambda j: j["bodies"].pop("cycle"))
        self.assertBlocked(self.build(publish=True), "cycle")
        self.assertEqual(current.read_text(), '{"old": "unaccepted fixture"}')

    def test_builder_exception_is_failure(self):
        (self.root / "review_pages.py").write_text('def build_site(root,d,stage_dir): raise RuntimeError("P1 injected failure")')
        self.assertBlocked(self.build(publish=True), "P1 injected failure")
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_forged_pass_missing_page(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('return {"status":', '(stage_dir / "cycle.html").unlink()\n    return {"status":'), encoding="utf-8")
        self.assertBlocked(self.build(publish=True), "cycle")

    def test_invalid_date_and_schema(self):
        for bad in ("../evil", "2026-09-02", "20260230", "２０２６０９０２", "20260902/../../x"):
            self.assertEqual(self.api.build_release(self.root, bad, publish=True)["status"], "fail")
        self.edit(lambda j: j.update(schema_version=2))
        self.assertBlocked(self.build(), "schema")

    def test_wrong_input_date(self):
        self.edit(lambda j: j.update(date="20260903"))
        self.assertBlocked(self.build(publish=True), "date")

    def test_invalid_body_type(self):
        self.edit(lambda j: j["bodies"].update(cycle={"bad": "test injection"}))
        self.assertBlocked(self.build(), "cycle")

    def test_report_errors_cannot_be_swallowed(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('"errors": [], "template_version"', '"errors": ["injected error"], "template_version"'), encoding="utf-8")
        self.assertBlocked(self.build(), "injected error")

    def test_page_failure_cannot_be_swallowed(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('"path": str(p), "status": "pass"', '"path": str(p), "status": "fail"'), encoding="utf-8")
        self.assertBlocked(self.build(), "page")

    def test_check_failure_and_not_run_block(self):
        for status in ("fail", "not_run"):
            with patch.object(self.api, "run_checks", return_value=[{"name": "cycle", "status": status, "errors": ["injected sentinel"]}]):
                self.assertBlocked(self.build(publish=True), "check")
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_source_mutation_is_blocked(self):
        original = self.api.run_checks
        def mutate(*args):
            result = original(*args)
            self.jpath.write_bytes(self.jpath.read_bytes() + b" ")
            return result
        with patch.object(self.api, "run_checks", side_effect=mutate):
            self.assertBlocked(self.build(publish=True), "source changed")

    def test_frozen_input_mutation_is_blocked(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('stage_dir.mkdir(parents=True, exist_ok=True)', 'stage_dir.mkdir(parents=True, exist_ok=True)\n    (root / "_学习" / ("judgment_" + d + ".json")).write_text("{}")'), encoding="utf-8")
        self.assertBlocked(self.build(), "frozen")

    def test_lock_blocks_concurrent_build(self):
        (self.root / ".review_publish.lock").mkdir()
        self.assertBlocked(self.build(), "lock")

    def test_reference_escape_is_blocked(self):
        self.edit(lambda j: j["bodies"].update(cycle=j["bodies"]["cycle"] + '<a href="../../outside.html">test injected link</a>'))
        self.assertBlocked(self.build(), "reference")

    def test_revision_and_immutable_release(self):
        # Real bodies contain references to unprovided historical assets. For this
        # atomicity-only test, isolate the reference-check seam explicitly.
        with patch.object(self.api, "validate_references", return_value=[]):
            first = self.build(publish=True)
            self.assertEqual(first["status"], "pass", first)
            directory = Path(first["release_dir"])
            old = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
            self.edit(lambda j: j.update(更新label=j.get("更新label", "") + " [CONTROLLED REVISION TEST]"))
            second = self.build(publish=True)
            self.assertEqual(second["status"], "pass", second)
            self.assertGreater(second["revision"], first["revision"])
            self.assertNotEqual(first["build_id"], second["build_id"])
            self.assertEqual(old, {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()})
            current = json.loads((self.root / "CURRENT.json").read_text())
            self.assertEqual(current["build_id"], second["build_id"])
            self.assertTrue(self.api.verify_release(self.root, D)["status"] == "pass")
            (Path(second["release_dir"]) / "site" / "cycle.html").write_text("TAMPER TEST")
            self.assertEqual(self.api.verify_release(self.root, D)["status"], "fail")

    def test_preview_never_changes_current(self):
        with patch.object(self.api, "validate_references", return_value=[]):
            result = self.build()
        self.assertEqual(result["status"], "pass", result)
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_degraded_never_publishes_even_with_flag(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('return {"status": "pass"', 'return {"status": "degraded"'), encoding="utf-8")
        with patch.object(self.api, "validate_references", return_value=[]):
            result = self.build(publish=True, allow_degraded=True)
        self.assertEqual(result["status"], "fail", result)
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_cli_failure_is_nonzero(self):
        r = subprocess.run([sys.executable, "-B", str(CODE / "review_publish.py"), "build", "../bad", "--root", str(self.root), "--publish"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_unknown_report_schema_is_blocked(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('return {"status":', 'return {"schema_version": 99, "status":'), encoding="utf-8")
        with patch.object(self.api, "validate_references", return_value=[]):
            self.assertBlocked(self.build(publish=True), "schema")

    def test_failed_check_row_cannot_hide_behind_zero_exit(self):
        p = self.root / "cycle数据核对.py"
        p.write_text('def chk(issues,ok,label,detail=""): issues.append((ok,label,detail))\ndef main():\n    issues=[]\n    chk(issues,False,"CONTROLLED FALSE ROW")\n    return 0\n',encoding="utf-8")
        result = self.api._check_one(self.root, self.root, D, "cycle")
        self.assertEqual(result["status"], "fail", result)

    def test_freeze_lhb_actual_consumed_inputs(self):
        names = self.api.input_files(self.root, D)
        self.assertIn(f"_学习/龙虎榜复盘存档/{D}.json", names)
        self.assertIn(f"_学习/席位荐票卡_{D}.html", names)

    def test_renderer_unreported_html_must_not_publish(self):
        p = self.root / "review_pages.py"
        p.write_text(BUILDER.replace('return {"status":', '(stage_dir / "unreported.html").write_text("CONTROLLED UNCHECKED PAGE")\n    return {"status":'), encoding="utf-8")
        with patch.object(self.api, "validate_references", return_value=[]):
            self.assertBlocked(self.build(publish=True), "unreported")

    def test_page_mutation_after_validation_blocks_publish(self):
        original = self.api.run_checks
        def mutate(frozen, stage, d):
            checks = original(frozen, stage, d)
            (stage / "cycle.html").write_text("CONTROLLED POST-CHECK CHANGE")
            return checks
        with patch.object(self.api, "run_checks", side_effect=mutate), patch.object(self.api, "validate_references", return_value=[]):
            self.assertBlocked(self.build(publish=True), "page changed")

    def test_future_dated_frozen_facts_rejected(self):
        # Real table copied byte-for-byte. 9/4 rows may not certify a 9/2 replay.
        shutil.copy2(PROD / "_学习" / "_市场温度表.json", self.root / "_学习" / "_市场温度表.json")
        with patch.object(self.api, "validate_references", return_value=[]):
            self.assertBlocked(self.build(publish=True), "future")

    def test_declared_local_module_import_uses_frozen_copy(self):
        helper = self.root / "p0_fixture_helper.py"
        helper.write_text('from pathlib import Path\ndef check(root):\n    assert Path(__file__).parent == root, "module escaped frozen root"\n',encoding="utf-8")
        p = self.root / "review_pages.py"
        extra = '\ndef input_files(root,d): return ["p0_fixture_helper.py"]\n'
        code = BUILDER.replace('import json', 'import json\nimport p0_fixture_helper').replace('    j = json.loads', '    p0_fixture_helper.check(root)\n    j = json.loads') + extra
        p.write_text(code, encoding="utf-8")
        with patch.object(self.api, "validate_references", return_value=[]):
            result = self.build(publish=True)
        self.assertEqual(result["status"], "pass", result)
        self.assertNotIn("p0_fixture_helper", sys.modules)

if __name__ == "__main__":
    unittest.main(verbosity=2)
