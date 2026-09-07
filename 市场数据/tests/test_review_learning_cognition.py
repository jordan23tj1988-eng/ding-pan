"""认知真实样本及受控旧 HTML/缺字段/承接注入。"""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_learning as learning
from tests.test_review_learning_predictions import BASE,SAMPLES,read,write

class CognitionTest(unittest.TestCase):
    def api(self):
        self.assertTrue(callable(getattr(learning,"collect_cognition",None)),"必须实现结构化认知消费 API")
        return learning.collect_cognition

    def test_real_structured_fields_preserved_and_refresh_not_growth(self):
        collect=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            result=collect(SAMPLES,"20260904",Path(tmp))
            self.assertEqual(result["status"],"pass")
            for route in ["auction","lhb","theme","logic","limitup","master"]:
                file=f"{route}判断_20260904.json" if route!="master" else "总审_20260904.json"
                expected=read(SAMPLES/"_学习"/file)["认知迭代"]
                actual=[x for x in result["records"] if x["route"]==route and x["d"]=="20260904"]
                self.assertEqual(len(actual),len(expected),route)
                for row in actual:
                    self.assertTrue({"id","d","source","claim","evidence","falsifier","status"}<=row.keys())
                    self.assertIsNotNone(row["claim"])
                    self.assertEqual(row["status"],"unverified")
            stats=result["stats"]["auction"]
            self.assertEqual(stats["legacy_updated"],"2026-09-04")
            self.assertEqual(stats["legacy_latest_entry_d"],"20260819")
            self.assertEqual(stats["latest_entry_d"],"20260904")
            again=collect(SAMPLES,"20260904",Path(tmp))
            self.assertEqual(again["new_count"],0)
            self.assertEqual([x["id"] for x in again["records"]],[x["id"] for x in result["records"]])

    def test_legacy_body_import_once_keeps_variant_layouts_and_unknown(self):
        collect=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"; (root/"20260904").mkdir(parents=True)
            j=read(SAMPLES/"_学习/judgment_20260904.json")
            write(root/"_学习/judgment_20260904.json",j)
            # 真实三页 body 作为只读兼容输入；其余结构化字段复制。
            for route in ["auction","limitup"]:
                write(root/"_学习"/f"{route}判断_20260904.json",read(SAMPLES/"_学习"/f"{route}判断_20260904.json"))
            write(root/"_学习/总审_20260904.json",read(SAMPLES/"_学习/总审_20260904.json"))
            first=collect(root,"20260904",out)
            self.assertEqual(first["status"],"pass")
            for route in ["lhb","theme","logic"]:
                records=[x for x in first["records"] if x["route"]==route]
                self.assertEqual(len(records), {"lhb":4,"theme":4,"logic":5}[route], route)
                self.assertTrue(any(x["d"]=="20260904" for x in records),route)
                self.assertTrue(all(x["origin"]=="legacy_body_import" for x in records))
            second=collect(root,"20260904",out)
            self.assertEqual(second["legacy_import_count"],0)
            self.assertEqual(second["new_count"],0)
            # 受控注入：结构化未知条目必须保留；禁止 fallback 掩盖坏字段。
            write(root/"_学习/theme判断_20260904.json",{"日期":"20260904","认知迭代":[None]})
            bad=collect(root,"20260904",Path(tmp)/"bad")
            self.assertEqual(bad["status"],"fail")
            self.assertTrue(any(x["route"]=="theme" and x["status"]=="unknown" for x in bad["records"]))

    def test_missing_route_is_fail_not_skip(self):
        collect=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; root.mkdir()
            result=collect(root,"20260904",Path(tmp)/"out")
            self.assertEqual(result["status"],"fail")
            self.assertTrue(result["errors"])

    def test_master_id_is_only_acknowledged(self):
        self.api()
        self.assertTrue(callable(getattr(learning,"settle_master",None)),"必须实现 Master 证据结算")
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260903","20260904"]: (root/d).mkdir(parents=True)
            # 受控任务元数据；数值仍取真实 fact。
            task={"指派ID":"CONTROLLED-ID","指派给":"lhb","截止":"20260904","condition":{"field":"最高连板","op":"ge","threshold":5}}
            write(root/"_学习/总审_20260903.json",{"日期":"20260903","指派清单":[task]})
            write(root/"_学习/judgment_20260904.json",{"date":"20260904","bodies":{"lhb":"承接 Master 指派 CONTROLLED-ID，done"}})
            write(root/"_学习/fact_20260904.json",read(SAMPLES/"_学习/fact_20260904.json"))
            got=learning.settle_master(root,"20260904",out)
            self.assertEqual(got["assignments"][0]["status"],"acknowledged")
            # 单独宣称 evidence/fulfilled 不够；必须能核查事实引用和原判据。
            write(root/"_学习/lhb判断_20260904.json",{"日期":"20260904","master_responses":[{"id":"CONTROLLED-ID","conclusion":"满足","evidence":[{"path":"missing.json","d":"20260904"}],"fulfilled":True}]})
            got=learning.settle_master(root,"20260904",out)
            self.assertEqual(got["assignments"][0]["status"],"acknowledged")

    def test_all_five_days_legacy_structured_string_is_lossless(self):
        collect=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            for d in ["20260831","20260901","20260902","20260903","20260904"]:
                result=collect(SAMPLES,d,Path(tmp))
                self.assertEqual(result["status"],"pass",str(result.get("errors")))
                if d=="20260831":
                    for route in ["auction","lhb","theme","logic","limitup"]:
                        original=read(SAMPLES/"_学习"/f"{route}判断_{d}.json")["认知迭代"]
                        rows=[x for x in result["records"] if x["route"]==route and x["d"]==d]
                        self.assertEqual(len(rows),1)
                        self.assertEqual(rows[0]["claim"],original)
