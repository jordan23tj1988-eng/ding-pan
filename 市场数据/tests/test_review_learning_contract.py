"""公开契约与分母/闭环状态验收，使用真实五日样本。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_learning as learning
from tests.test_review_learning_predictions import BASE,SAMPLES,read

class ContractTest(unittest.TestCase):
    def test_versioned_contract_exists_with_required_nullable_fields(self):
        path=BASE/"root/_契约/学习契约.v1.json"
        self.assertTrue(path.is_file(),"必须交付学习契约 v1")
        contract=read(path)
        self.assertEqual(contract["schema_version"],1)
        pred=contract["$defs"]["prediction"]
        self.assertTrue({"id","d","due_d","source","field","op","threshold","condition","status","actual","evidence","schema_version"}<=set(pred["required"]))
        self.assertIn("null",pred["properties"]["actual"]["type"])
        self.assertEqual(set(pred["properties"]["event_type"]["enum"]),{"direction","attack_defense","numeric","stock","conditional"})

    def test_coverage_separates_forecasts_narratives_and_incomplete_learning(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=learning.audit_learning(SAMPLES,"20260904",Path(tmp))
            self.assertIn("prediction_coverage",result,"分母必须明确区分34条推演与25段叙事")
            coverage=result["prediction_coverage"]
            self.assertEqual(coverage["forecast_items"],34)
            self.assertEqual(coverage["narrative_items"],25)
            self.assertEqual(coverage["due_forecasts"],28)
            self.assertEqual(sum(coverage["forecast_status_counts"].values()),34)
            self.assertEqual(result["learning_closure"]["status"],"incomplete")
            self.assertGreater(result["learning_closure"]["unresolved_due_predictions"],0)
            self.assertTrue(all(x["status"] not in ("true","false") for x in result["predictions"] if x["id"].startswith("narrative:")))

    def test_no_due_items_do_not_claim_completed_learning(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=learning.audit_learning(SAMPLES,"20260831",Path(tmp))
            self.assertEqual(result["learning_closure"]["status"],"not_due")

    def test_future_legacy_refresh_is_not_historical_metadata(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=learning.audit_learning(SAMPLES,"20260831",Path(tmp))
            self.assertIsNone(result["cognition"]["stats"]["auction"]["legacy_updated"])
            self.assertTrue(result["cognition"]["stats"]["auction"]["legacy_snapshot_after_asof"])
