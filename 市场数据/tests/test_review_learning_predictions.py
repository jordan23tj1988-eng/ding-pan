"""真实 fact/推演回放；边界与坏输入通过明确标注的受控注入构造。"""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_learning as learning
P2_ROOT=Path(os.environ.get("SENTIMENT_P2_TASK", str(Path(__file__).resolve().parents[2]/"codex_workspace"/"stability-20260906"/"p2")))
BASE=P2_ROOT
SAMPLES=P2_ROOT/"evidence"/"real_samples"

def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False),encoding="utf-8")

class PredictionTest(unittest.TestCase):
    def api(self):
        self.assertTrue(callable(getattr(learning,"settle_predictions",None)),"必须实现逐项结算 API")
        return learning.settle_predictions

    def test_real_september_three_four_thresholds_false(self):
        settle=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=settle(SAMPLES,"20260903","20260904",Path(tmp))
            self.assertEqual(result["status"],"pass")
            rows={x["field"]:x for x in result["predictions"] if x["event_type"]=="numeric"}
            for field, actual in [("温度",13.4),("成交额亿",20307.0),("最高连板",5),("一进二率",0.122)]:
                with self.subTest(field=field):
                    self.assertEqual(rows[field]["status"],"false")
                    self.assertEqual(rows[field]["actual"],actual)
                    self.assertEqual(rows[field]["op"],"lt")
                    self.assertTrue(rows[field]["evidence"])
            stocks=[x for x in result["predictions"] if x["event_type"]=="stock"]
            self.assertTrue(all(x["status"]=="unverifiable" for x in stocks))
            before=Path(result["artifact"]).read_bytes()
            again=settle(SAMPLES,"20260903","20260904",Path(tmp))
            self.assertNotEqual(again["artifact"],result["artifact"])
            self.assertEqual(Path(result["artifact"]).read_bytes(),before)

    def test_controlled_predicate_edges_use_real_facts(self):
        settle=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ("20260903","20260904"): (root/d).mkdir(parents=True)
            write(root/"_学习/fact_20260904.json",read(SAMPLES/"_学习/fact_20260904.json"))
            def pred(id,**kw):
                return dict(schema_version=1,id=id,d="20260903",due_d="20260904",source="controlled_test_predicate_not_market_forecast",field="最高连板",op="lt",threshold=5,condition=None,**kw)
            rows=[pred("eq_lt"),{**pred("eq_le"),"op":"le"},{**pred("pct"),"field":"炸板率","op":"ge","threshold":55.2,"unit":"pct"},
                  {**pred("null"),"threshold":None},{**pred("unknown"),"field":"缺失字段"},
                  {**pred("not_triggered"),"condition":{"field":"最高连板","op":"gt","threshold":5}},
                  {**pred("trigger_missing"),"condition":{"field":"缺失字段","op":"ge","threshold":1}},
                  {**pred("future"),"due_d":"20260907"}]
            write(root/"_学习/推演_20260903.json",{"schema_version":1,"d":"20260903","predictions":rows})
            result=settle(root,"20260903","20260904",out)
            self.assertEqual(result["status"],"pass")
            got={x["id"]:x for x in result["predictions"]}
            for key,status in [("eq_lt","false"),("eq_le","true"),("pct","true"),("null","unverifiable"),("unknown","unverifiable"),("not_triggered","not_triggered"),("trigger_missing","unverifiable"),("future","pending")]:
                self.assertEqual(got[key]["status"],status,key)
            self.assertIsNone(got["unknown"]["actual"])
            self.assertIsNone(got["future"]["actual"])
            self.assertEqual(settle(root,"20260904","20260903",out)["status"],"fail")

    def test_legacy_conflicts_and_missing_sources_explicit(self):
        settle=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ("20260903","20260904"): (root/d).mkdir(parents=True)
            legacy=read(SAMPLES/"_学习/推演_20260903.json")
            row=copy.deepcopy(legacy["次日可证伪预测"][1]); row["预测"]="受控测试注入：温度可能降，但仍>=13.2";
            write(root/"_学习/推演_20260903.json",{"日期":"20260903","次日可证伪预测":[row]})
            result=settle(root,"20260903","20260904",out)
            self.assertEqual(result["predictions"][0]["status"],"ambiguous")
            self.assertEqual(settle(root,"20260902","20260904",out)["status"],"fail")
            write(root/"_学习/推演_20260903.json",legacy)
            result=settle(root,"20260903","20260904",out)
            self.assertEqual(result["predictions"][1]["status"],"unverifiable")

    def test_archive_calendar_does_not_guess_weekdays(self):
        settle=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=settle(SAMPLES,"20260904","20260904",Path(tmp))
            self.assertTrue(all(x["status"]=="pending" for x in result["predictions"]))
            self.assertTrue(all(x["actual"] is None for x in result["predictions"]))
