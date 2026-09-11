import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "认知迭代全量更新.py"
PYTHON = sys.executable


class CognitionFullUpdateTest(unittest.TestCase):
    @contextmanager
    def fixture(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name) / "input"
        out = Path(tmp.name) / "runs"
        learn = root / "_学习"
        learn.mkdir(parents=True)
        bodies = {"cycle": '<h2>六 我的认知迭代</h2><div class="tli"><div class="d">2026-09-10</div><div class="h">周期观察</div><div class="b">仅测试条目</div></div>'}
        judgment = {"date": "20260910", "bodies": bodies}
        (learn / "judgment_20260910.json").write_text(
            json.dumps(judgment, ensure_ascii=False), encoding="utf-8"
        )
        routes = ["auction", "lhb", "theme", "logic", "limitup"]
        for route in routes:
            payload = {
                "日期": "20260910",
                "路": route,
                "认知迭代": [{
                    "id": f"cognition:{route}:20260910:0",
                    "d": "20260910",
                    "claim": f"{route} test cognition",
                    "falsifier": {"field": "温度", "op": "ge", "threshold": 99},
                    "evidence": {"source": "controlled fixture"},
                }],
            }
            (learn / f"{route}判断_20260910.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
        master = {
            "日期": "20260910",
            "认知迭代": [{"认知点": "master test cognition", "可证伪条件": {"指标": "温度", ">=": 99}}],
            "指派清单": [],
        }
        (learn / "总审_20260910.json").write_text(
            json.dumps(master, ensure_ascii=False), encoding="utf-8"
        )
        yield tmp, root, out
        tmp.cleanup()

    def run_cli(self, root, out, *extra):
        return subprocess.run(
            [PYTHON, "-B", str(SCRIPT), "20260910", "--root", str(root), "--out", str(out), *extra],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_entrypoint_rebuilds_target_dated_snapshots_without_future_data(self):
        with self.fixture() as (tmp, root, out):
            proc = self.run_cli(root, out)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["d"], "20260910")
            for route in ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]:
                if route == "master":
                    path = root / "_学习" / "_认知库_master.json"
                else:
                    path = root / "_学习" / f"_认知库_{route}.json"
                self.assertTrue(path.is_file(), path)
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["updated"].replace("-", ""), "20260910")
                self.assertTrue(all(str(x.get("日期", x.get("d", ""))).replace("-", "") <= "20260910" for x in data["条目"]), route)
                self.assertTrue(all(re.match(r"\d{4}-\d{2}-\d{2}$", str(x.get("日期"))) for x in data["条目"]), route)
            enhanced = root / "_学习" / "子agent增强" / "认知库_auction_20260910.json"
            self.assertTrue(enhanced.is_file())
            self.assertFalse((root / "_学习" / "子agent增强" / "认知库_auction_20260911.json").exists())

    def test_renderer_history_fold_is_restored_from_merged_library(self):
        """回归：日期化快照若只剩当日条目，_认知库渲染 的"更早的认知迭代"折叠区会消失。"""
        with self.fixture() as (tmp, root, out):
            enh = root / "_学习" / "子agent增强"
            enh.mkdir(parents=True, exist_ok=True)
            prior_items = [{"日期": f"2026-08-{d:02d}", "标题": f"历史{ d}", "正文": "x"} for d in range(1, 12)]
            (enh / "认知库_auction_20260903.json").write_text(
                json.dumps({"route": "auction", "updated": "2026-09-03", "条数": len(prior_items),
                            "条目": prior_items}, ensure_ascii=False), encoding="utf-8")
            proc = self.run_cli(root, out)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            sys.path.insert(0, str(ROOT))
            import importlib
            renderer = importlib.import_module("_认知库渲染")
            html = renderer.r_cog_lib("auction", "20260910", L=str(root / "_学习"))
            self.assertIn("更早的认知迭代", html)
            self.assertIn("11条", html)

    def test_preserves_prior_history_and_ignores_future_snapshots(self):
        with self.fixture() as (tmp, root, out):
            enh = root / "_学习" / "子agent增强"
            enh.mkdir(parents=True, exist_ok=True)
            prior_items = [{"日期": f"2026-08-{d:02d}", "标题": f"历史{ d}", "正文": "x"} for d in range(1, 12)]
            (enh / "认知库_auction_20260903.json").write_text(
                json.dumps({"route": "auction", "updated": "2026-09-03", "条数": len(prior_items),
                            "条目": prior_items}, ensure_ascii=False), encoding="utf-8")
            future_items = [{"日期": "2026-09-11", "标题": "未来条目", "正文": "x"}]
            (enh / "认知库_auction_20260911.json").write_text(
                json.dumps({"route": "auction", "updated": "2026-09-11", "条数": 1,
                            "条目": future_items}, ensure_ascii=False), encoding="utf-8")
            proc = self.run_cli(root, out)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads((root / "_学习" / "_认知库_auction.json").read_text(encoding="utf-8"))
            titles = [x["标题"] for x in data["条目"]]
            self.assertIn("历史1", titles)
            self.assertNotIn("未来条目", titles)
            self.assertGreaterEqual(data["条数"], 12)

    def test_invalid_date_fails_closed(self):
        with self.fixture() as (tmp, root, out):
            proc = subprocess.run(
                [PYTHON, "-B", str(SCRIPT), "2026091", "--root", str(root), "--out", str(out)],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse((root / "_学习" / "_认知库_auction.json").exists())


if __name__ == "__main__":
    unittest.main()
