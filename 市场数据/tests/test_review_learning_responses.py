"""真实五日应答；异常场景均为明确的受控测试注入。"""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_learning as learning
SAMPLES = Path(__file__).resolve().parents[2] / "evidence" / "real_samples" / "_学习"

class ResponsesTest(unittest.TestCase):
    def normalizer(self):
        self.assertTrue(callable(getattr(learning, "normalize_responses", None)), "必须实现应答归一 API")
        return learning.normalize_responses

    def test_all_three_real_shapes_cover_every_item(self):
        normalize = self.normalizer()
        for d, n in [("20260831",9),("20260901",8),("20260902",6),("20260903",5),("20260904",9)]:
            with self.subTest(d=d):
                raw=json.loads((SAMPLES/f"自主拓展应答_{d}.json").read_text(encoding="utf-8-sig"))
                items=json.loads((SAMPLES/f"自主拓展清单_{d}.json").read_text(encoding="utf-8-sig"))["items"]
                got=normalize(raw,items,d)
                self.assertEqual(len(got),n)
                self.assertEqual(set(got),{x["id"] for x in items})

    def test_injected_unknown_missing_duplicate_and_dates_rejected(self):
        normalize=self.normalizer()
        items=[{"id":"test_a"},{"id":"test_b"}]
        good={"test_a":{"决定":"支持"},"test_b":{"决定":"待验"}}
        cases=[({**good,"unknown":{}},items,"20260904"),({"test_a":{}},items,"20260904"),
               (good,items+[items[0]],"20260904"),
               ({"日期":"20260903","应答":good},items,"20260904"),
               ({"日期":"20260904","应答":[{"id":"test_a"},{"id":"test_a"}]},items,"20260904"),
               (good,items,"2026094"),(good,items,"20260230"),(good,items,"２０２６０９０４")]
        for raw, inv, d in cases:
            with self.subTest(raw=raw,d=d),self.assertRaises(ValueError): normalize(raw,inv,d)
        self.assertEqual(good["test_a"],{"决定":"支持"})
