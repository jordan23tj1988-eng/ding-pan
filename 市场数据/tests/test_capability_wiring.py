# -*- coding: utf-8 -*-
"""能力进化闭环回归：先验加载 → 消费回执 → T+1 验证 → 能力化 → 重建承接。"""
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


import sys
wiring = load("capability_wiring", "能力进化接线.py")
validator = load("capability_validator", "能力验证闭环.py")
# 兼容节点 认知验证闭环.py 内部按模块名引用实现，先注册同一实例再加载，
# 以断言"只有一份验证逻辑"，而不是在测试里制造第二份拷贝。
sys.modules.setdefault("能力验证闭环", validator)
legacy_verifier = load("capability_verifier_compat", "认知验证闭环.py")
evolution = load("capability_evolution", "自我进化闭环.py")

ROUTES = list(wiring.ROUTES)


class CapabilityWiringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_学习").mkdir()
        self._write("能力进化库_认知迭代.json", {"records": [
            {"id": "c-good", "route": "auction", "state": "capability", "validation": "validated",
             "capitalized": True, "capability_rule": "高开>=2%", "boundary": "fixture window",
             "validation_spec": {"evidence": [{"target_d": "20261001"}]}, "hit_count": 1, "reused_count": 0},
            {"id": "c-phantom", "route": "auction", "state": "capability", "validation": "unverifiable",
             "capitalized": None, "capability_rule": "不能进池"},
        ]})
        self._write("能力进化库_自主拓展.json", {"records": []})

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, obj):
        (self.root / "_学习" / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    def _read(self, name):
        return json.loads((self.root / "_学习" / name).read_text(encoding="utf-8-sig"))

    def test_prepare_excludes_unverified_capability(self):
        """只有 validated + capitalized + 有能力规则的记录可进入判断层。"""
        out = wiring.prepare(self.root, "20261002")
        self.assertEqual(out["eligible_total"], 1)
        self.assertEqual(out["routes"]["auction"]["records"][0]["id"], "c-good")
        self.assertEqual(out["routes"]["lhb"]["status"], "no_eligible_capabilities")

    def test_prepare_rejects_future_dated_records(self):
        """禁后视镜：日期晚于当日的能力不得进入当日判断层。"""
        self._write("能力进化库_自主拓展.json", {"records": [
            {"id": "future", "route": "lhb", "date": "20261003", "state": "capability",
             "validation": "validated", "capitalized": True, "capability_rule": "x>=1"}]})
        out = wiring.prepare(self.root, "20261002")
        self.assertEqual(out["routes"]["lhb"]["eligible_count"], 0)

    def _receipt(self, d, applied_routes):
        import hashlib
        pre = self._read(f"能力预加载_{d}.json")
        preload_path = self.root / "_学习" / f"能力预加载_{d}.json"
        routes = {}
        for route in ROUTES:
            records = pre["routes"][route]["records"]
            if not records:
                routes[route] = {"status": "no_eligible_capabilities", "considered_ids": [],
                                 "applied": [], "rejected": []}
            elif route in applied_routes:
                rid = records[0]["id"]
                routes[route] = {"status": "applied", "considered_ids": [rid], "rejected": [],
                                 "applied": [{"id": rid, "effect": "收紧候选过滤",
                                              "source_locator": f"{route}判断_{d}.json#五路裁决"}]}
            else:
                rid = records[0]["id"]
                routes[route] = {"status": "rejected_all", "considered_ids": [rid], "applied": [],
                                 "rejected": [{"id": rid, "reason": "本日样本不足，暂不启用"}]}
        return {"schema_version": 1, "as_of": d,
                "preload": {"path": f"_学习/能力预加载_{d}.json",
                            "sha256": hashlib.sha256(preload_path.read_bytes()).hexdigest()},
                "routes": routes}

    def test_consume_counts_only_explicit_applied(self):
        wiring.prepare(self.root, "20261002")
        self._write("能力使用回执_20261002.json", self._receipt("20261002", {"auction"}))
        audit = wiring.consume(self.root, "20261002")
        self.assertEqual(audit["applied_count"], 1)
        row = self._read("能力进化库_认知迭代.json")["records"][0]
        self.assertEqual(row["reused_count"], 1)
        self.assertEqual(row["feedback_routes"], ["auction"])
        self.assertEqual(len(row["reuse_log"]), 1)

    def test_consume_is_idempotent(self):
        wiring.prepare(self.root, "20261002")
        self._write("能力使用回执_20261002.json", self._receipt("20261002", {"auction"}))
        wiring.consume(self.root, "20261002")
        wiring.consume(self.root, "20261002")
        row = self._read("能力进化库_认知迭代.json")["records"][0]
        self.assertEqual(row["reused_count"], 1)

    def test_missing_receipt_fails_closed(self):
        wiring.prepare(self.root, "20261002")
        with self.assertRaises(ValueError):
            wiring.validate(self.root, "20261002")

    def test_receipt_must_cover_every_route(self):
        wiring.prepare(self.root, "20261002")
        receipt = self._receipt("20261002", {"auction"})
        receipt["routes"].pop("cycle")
        self._write("能力使用回执_20261002.json", receipt)
        with self.assertRaises(ValueError):
            wiring.validate(self.root, "20261002")

    def test_receipt_cannot_cite_unknown_capability(self):
        wiring.prepare(self.root, "20261002")
        receipt = self._receipt("20261002", {"auction"})
        receipt["routes"]["auction"]["applied"][0]["id"] = "not-in-pool"
        self._write("能力使用回执_20261002.json", receipt)
        with self.assertRaises(ValueError):
            wiring.validate(self.root, "20261002")

    def test_applied_requires_effect_and_locator(self):
        wiring.prepare(self.root, "20261002")
        receipt = self._receipt("20261002", {"auction"})
        receipt["routes"]["auction"]["applied"][0].pop("source_locator")
        self._write("能力使用回执_20261002.json", receipt)
        with self.assertRaises(ValueError):
            wiring.validate(self.root, "20261002")


class CapabilityValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_学习").mkdir()
        validator.ROOT = self.root

    def tearDown(self):
        validator.ROOT = ROOT
        self.tmp.cleanup()

    def _evidence(self, obj):
        (self.root / "_学习" / "结算.json").write_text(json.dumps(obj), encoding="utf-8")

    def test_promotes_only_when_bound_evidence_passes(self):
        self._evidence({"metric": 3})
        row = {"id": "x", "route": "lhb", "capability_rule": "metric>=2", "boundary": "样本期",
               "validation_spec": {"evidence": [{"path": "_学习/结算.json", "target_d": "20261002",
                                                 "field": "metric", "op": "ge", "value": 2}]}}
        event = validator.review_one(row, "20261002")
        self.assertEqual(event["status"], "validated")
        self.assertTrue(row["capitalized"])
        self.assertEqual(row["state"], "capability")
        self.assertEqual(row["validation_pass_count"], 1)
        self.assertEqual(row.get("hit_count", 0), 0)

    def test_no_spec_stays_unverifiable(self):
        row = {"id": "y", "route": "lhb", "falsifiable_rule": "封板率>=80%"}
        event = validator.review_one(row, "20261002")
        self.assertEqual(event["status"], "unverifiable")
        self.assertIsNone(row.get("capitalized"))
        self.assertIsNone(row.get("validation"))

    def test_failed_evidence_is_refuted_not_capability(self):
        self._evidence({"metric": 1})
        row = {"id": "z", "route": "lhb", "capability_rule": "metric>=2",
               "validation_spec": {"evidence": [{"path": "_学习/结算.json", "target_d": "20261002",
                                                 "field": "metric", "op": "ge", "value": 2}]}}
        event = validator.review_one(row, "20261002")
        self.assertEqual(event["status"], "falsified")
        self.assertEqual(row["state"], "refuted")
        self.assertFalse(row["capitalized"])

    def test_future_evidence_is_rejected(self):
        self._evidence({"metric": 9})
        row = {"id": "f", "route": "lhb",
               "validation_spec": {"evidence": [{"path": "_学习/结算.json", "target_d": "20261005",
                                                 "field": "metric", "op": "ge", "value": 2}]}}
        event = validator.review_one(row, "20261002")
        self.assertEqual(event["status"], "falsified")
        self.assertIn("晚于结算日", event["reason"])

    def test_out_of_root_evidence_is_rejected(self):
        row = {"id": "o", "route": "lhb",
               "validation_spec": {"evidence": [{"path": "../../secret.json", "target_d": "20261002",
                                                 "field": "x", "op": "ge", "value": 1}]}}
        event = validator.review_one(row, "20261002")
        self.assertEqual(event["status"], "falsified")

    def test_compat_entry_shares_single_implementation(self):
        """原节点名 认知验证闭环.py 必须与实现同源，不得出现第二份逻辑。"""
        self.assertIs(legacy_verifier.run, validator.run)
        self.assertIs(legacy_verifier.review_one, validator.review_one)


class EvolutionRebuildTests(unittest.TestCase):
    """重建必须承接验证/能力化证据，否则闭环在次日断裂。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_学习").mkdir()
        evolution.LEARN = self.root / "_学习"

    def tearDown(self):
        evolution.LEARN = ROOT / "_学习"
        self.tmp.cleanup()

    def _write(self, name, obj):
        (evolution.LEARN / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    def test_rebuild_preserves_promotion_and_is_idempotent(self):
        promoted = {
            "id": "extension:cap-a", "kind": "自主拓展", "route": "lhb", "title": "净买占比有效",
            "state": "capability", "validation": "validated", "capitalized": True,
            "capability_rule": "状态=有效即可用", "hit_count": 1, "reused_count": 0,
            "validation_spec": {"evidence": []},
            "review_log": [{"as_of": "20261001", "status": "validated"}],
        }
        self._write("能力进化库_自主拓展.json", {"version": 2, "records": [promoted]})
        self._write("能力进化库_认知迭代.json", {"version": 2, "records": []})
        self._write("孵化区.json", {})
        self._write("深挖专题台账.json", {})
        evolution.build("20261002")
        rows = json.loads((evolution.LEARN / "能力进化库_自主拓展.json").read_text(encoding="utf-8-sig"))["records"]
        saved = next(r for r in rows if r["id"] == "extension:cap-a")
        self.assertEqual(saved["state"], "capability")
        self.assertTrue(saved["capitalized"])
        self.assertEqual(saved["validation"], "validated")
        self.assertEqual(saved["hit_count"], 1)
        self.assertEqual(saved["capability_rule"], "状态=有效即可用")
        before = len(rows)
        evolution.build("20261003")
        rows2 = json.loads((evolution.LEARN / "能力进化库_自主拓展.json").read_text(encoding="utf-8-sig"))["records"]
        self.assertEqual(len(rows2), before, "重建不得重复堆积同一条记录")
        saved2 = next(r for r in rows2 if r["id"] == "extension:cap-a")
        self.assertEqual(saved2["state"], "capability")
        self.assertTrue(saved2["capitalized"])


if __name__ == "__main__":
    unittest.main()
