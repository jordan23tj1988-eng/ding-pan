import json
import tempfile
import unittest
from pathlib import Path

import 能力进化接线 as wiring


class EvolutionFullLoopTest(unittest.TestCase):
    def fixture_root(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        learn = root / "_学习"
        learn.mkdir()
        record = {
            "id": "cap1",
            "kind": "自主拓展",
            "route": "auction",
            "title": "fixture capability",
            "date": "20261001",
            "validation": "validated",
            "capitalized": True,
            "capability_rule": "fixture rule",
            "boundary": "fixture boundary",
            "validation_spec": {"evidence": [{"target_d": "20261001", "path": "fixture.json", "field": "ok", "op": "eq", "value": True}]},
            "reused_count": 0,
            "hit_count": 0,
        }
        (learn / "能力进化库_自主拓展.json").write_text(json.dumps({"version": 2, "records": [record]}, ensure_ascii=False), encoding="utf-8")
        (learn / "能力进化库_认知迭代.json").write_text(json.dumps({"version": 2, "records": []}, ensure_ascii=False), encoding="utf-8")
        return tmp, root, learn

    def receipt(self, root, d):
        preload = wiring.prepare(root, d)
        path = root / "_学习" / wiring.PRELOAD_NAME.format(d=d)
        routes = {}
        for route in wiring.ROUTES:
            if route == "auction":
                routes[route] = {
                    "status": "applied",
                    "considered_ids": ["cap1"],
                    "applied": [{"id": "cap1", "effect": "used fixture", "source_locator": "judgment.json#auction"}],
                    "rejected": [],
                }
            else:
                routes[route] = {"status": "no_eligible_capabilities", "considered_ids": [], "applied": [], "rejected": []}
        receipt = {"schema_version": 1, "as_of": d, "preload": {"sha256": wiring._sha256(path)}, "routes": routes}
        (root / "_学习" / wiring.RECEIPT_NAME.format(d=d)).write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        return preload

    def test_validation_and_hit_are_separate(self):
        import 能力验证闭环 as verifier
        row = {
            "id": "r1", "route": "auction", "capability_rule": "x",
            "validation_spec": {"evidence": []}, "boundary": "b",
            "review_log": [], "hit_count": 0,
        }
        event = verifier.review_one(row, "20261002")
        self.assertIsNotNone(event)
        self.assertEqual(row.get("validation_pass_count", 0), 0)  # 空证据不可验证
        self.assertEqual(row.get("hit_count", 0), 0)

    def test_reuse_then_hit_is_idempotent(self):
        tmp, root, learn = self.fixture_root()
        try:
            self.receipt(root, "20261003")
            audit = wiring.consume(root, "20261003")
            self.assertEqual(audit["applied_count"], 1)
            events = {"schema_version": 1, "as_of": "20261004", "events": [{
                "id": "cap1", "route": "auction", "object_date": "20261004",
                "object_id": "600000", "result": {"return_pct": 1.2},
                "source_locator": "settlement.json#rows.0",
            }]}
            path = learn / "能力命中候选_20261004.json"
            path.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
            first = wiring.record_hits(root, "20261004", path)
            second = wiring.record_hits(root, "20261004", path)
            self.assertEqual(first["applied_count"], 1)
            self.assertEqual(second["applied_count"], 0)
            ledger = json.loads((learn / "能力进化库_自主拓展.json").read_text(encoding="utf-8"))
            row = ledger["records"][0]
            self.assertEqual(row["reused_count"], 1)
            self.assertEqual(row["hit_count"], 1)
            self.assertEqual(len(row["hit_log"]), 1)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
