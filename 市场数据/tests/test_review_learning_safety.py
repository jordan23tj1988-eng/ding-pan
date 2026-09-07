"""对边界与消费者完整性做受控故障注入，不制造金融观测。"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_learning as learning
from tests.test_review_learning_predictions import BASE,SAMPLES,read,write

class SafetyTest(unittest.TestCase):
    def test_embedded_response_id_cannot_disagree_with_mapping(self):
        with self.assertRaises(ValueError):
            learning.normalize_responses({"a":{"id":"b","决定":"支持"}},[{"id":"a"}],"20260904")

    def test_conflicting_explicit_legacy_operators_are_ambiguous(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260903","20260904"]: (root/d).mkdir(parents=True)
            write(root/"_学习/fact_20260904.json",read(SAMPLES/"_学习/fact_20260904.json"))
            raw=read(SAMPLES/"_学习/推演_20260903.json")
            row=copy.deepcopy(raw["次日可证伪预测"][1])
            row["预测"]="受控冲突注入：20260904温度低于13.2且温度>=13.2"
            write(root/"_学习/推演_20260903.json",{"日期":"20260903","次日可证伪预测":[row]})
            got=learning.settle_predictions(root,"20260903","20260904",out)
            self.assertEqual(got["predictions"][0]["status"],"ambiguous")

    def test_output_inside_input_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; (root/"20260904").mkdir(parents=True)
            write(root/"_学习/自主拓展清单_20260904.json",{"d":"20260904","items":[]})
            write(root/"_学习/自主拓展应答_20260904.json",{})
            before=set(root.rglob("*"))
            got=learning.audit_learning(root,"20260904",root/"_学习/new_runs")
            self.assertEqual(got["status"],"fail")
            self.assertEqual(set(root.rglob("*")),before)

    def test_master_missing_source_is_fail(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; root.mkdir()
            got=learning.settle_master(root,"20260904",Path(tmp)/"out")
            self.assertEqual(got["status"],"fail")

    def test_historical_prediction_missing_is_fail(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260903","20260904"]:
                (root/d).mkdir(parents=True)
                for prefix in ["自主拓展清单","自主拓展应答"]:
                    write(root/"_学习"/f"{prefix}_{d}.json",read(SAMPLES/"_学习"/f"{prefix}_{d}.json"))
            for prefix in ["推演","总审","auction判断","lhb判断","theme判断","logic判断","limitup判断"]:
                write(root/"_学习"/f"{prefix}_20260904.json",read(SAMPLES/"_学习"/f"{prefix}_20260904.json"))
            got=learning.audit_learning(root,"20260904",out)
            self.assertEqual(got["status"],"fail")
            self.assertTrue(any("20260903" in e and "推演" in e for e in got["errors"]))

    def test_explicit_v1_master_evidence_can_validate_original_condition(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260903","20260904"]: (root/d).mkdir(parents=True)
            path=root/"_学习/fact_20260904.json"
            write(path,read(SAMPLES/"_学习/fact_20260904.json"))
            task={"指派ID":"TEST-VALID","指派给":"lhb","截止":"20260904","condition":{"field":"最高连板","op":"ge","threshold":5}}
            write(root/"_学习/总审_20260903.json",{"日期":"20260903","指派清单":[task]})
            reference={"path":"_学习/fact_20260904.json","d":"20260904","field":"facts.最高连板","sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            response={"id":"TEST-VALID","conclusion":"受控测试：原条件满足","evidence":[reference]}
            write(root/"_学习/lhb判断_20260904.json",{"日期":"20260904","master_responses":[response]})
            got=learning.settle_master(root,"20260904",out)
            self.assertEqual(got["assignments"][0]["status"],"validated")
            task["condition"]["threshold"]=6
            write(root/"_学习/总审_20260903.json",{"日期":"20260903","指派清单":[task]})
            got=learning.settle_master(root,"20260904",out)
            self.assertEqual(got["assignments"][0]["status"],"refuted")

    def test_due_date_fact_not_later_fact_used(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260902","20260903","20260904"]: (root/d).mkdir(parents=True)
            for d in ["20260903","20260904"]:
                write(root/"_学习"/f"fact_{d}.json",read(SAMPLES/"_学习"/f"fact_{d}.json"))
            raw={"schema_version":1,"d":"20260902","predictions":[{"schema_version":1,"id":"test-date","d":"20260902","due_d":"20260903","source":"controlled-test","field":"温度","op":"lt","threshold":13.3,"condition":None}]}
            write(root/"_学习/推演_20260902.json",raw)
            got=learning.settle_predictions(root,"20260902","20260904",out)
            self.assertEqual(got["predictions"][0]["actual"],13.2)
            self.assertEqual(got["predictions"][0]["status"],"true")
            self.assertEqual(got["predictions"][0]["evidence"][0]["d"],"20260903")

    def test_malformed_new_contract_and_top_level_are_fail_results(self):
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260903","20260904"]: (root/d).mkdir(parents=True)
            valid={"schema_version":1,"id":"bad-input-test","d":"20260903","due_d":"20260904","source":"controlled-test","field":"温度","op":"lt","threshold":13.2,"condition":None}
            for key,value in [("event_type","unknown_type"),("unit","unknown_unit"),("condition",[]),("op","invalid")]:
                row={**valid,key:value}
                write(root/"_学习/推演_20260903.json",{"schema_version":1,"d":"20260903","predictions":[row]})
                with self.subTest(key=key):
                    got=learning.settle_predictions(root,"20260903","20260904",out)
                    self.assertEqual(got["status"],"fail")
                    self.assertTrue(got["errors"])
            write(root/"_学习/推演_20260903.json",[])
            try:
                got=learning.settle_predictions(root,"20260903","20260904",out)
            except Exception as exc:
                self.fail("非法顶层须返回统一失败，不抛出未处理异常: "+repr(exc))
            self.assertEqual(got["status"],"fail")
