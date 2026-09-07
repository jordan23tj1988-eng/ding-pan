"""真实消费者 subprocess 回归；缺应答和状态分支为受控错误注入。"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_learning as learning
from tests.test_review_learning_predictions import BASE,SAMPLES,read,write

class ConsumerTest(unittest.TestCase):
    def api(self):
        self.assertTrue(callable(getattr(learning,"audit_learning",None)),"必须实现生产 audit 消费接线")
        return learning.audit_learning

    def run_cli(self,script,args):
        return subprocess.run([sys.executable,"-B",str(BASE/"root"/script),*args],cwd=BASE,env=dict(os.environ,PYTHONUTF8="1",PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,encoding="utf-8")

    def test_real_scanner_audit_reads_all_decisions_and_predicts(self):
        self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            out=Path(tmp)/"runs"
            proc=self.run_cli("自主拓展扫描.py",["audit","20260904","--root",str(SAMPLES),"--out",str(out)])
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            result=json.loads(proc.stdout)
            self.assertEqual(result["coverage"]["total_items"],37)
            self.assertEqual(result["coverage"]["responses_read"],37)
            self.assertEqual(len(result["items"]),37)
            self.assertTrue(all(x["status"] for x in result["items"]))
            self.assertTrue(any(x["response"]["决定"]!="不深挖" for x in result["items"]))
            self.assertTrue(result["predictions"])
            self.assertTrue(result["cognition"]["records"])
            self.assertTrue(result["master"]["assignments"])

    def test_missing_response_fails_denominator_never_shrinks(self):
        audit=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"; (root/"20260904").mkdir(parents=True)
            inv=read(SAMPLES/"_学习/自主拓展清单_20260904.json")
            resp=read(SAMPLES/"_学习/自主拓展应答_20260904.json")
            resp.pop(inv["items"][0]["id"])  # 受控删除一项应答
            write(root/"_学习/自主拓展清单_20260904.json",inv)
            write(root/"_学习/自主拓展应答_20260904.json",resp)
            result=audit(root,"20260904",out)
            self.assertEqual(result["status"],"fail")
            self.assertEqual(result["coverage"]["total_items"],9)
            self.assertTrue(result["errors"])
            self.assertEqual(len(result["items"]),9)
            self.assertTrue(any(x["status"]=="missing" for x in result["items"]))
            proc=self.run_cli("review_learning.py",["coverage","20260904","--root",str(root),"--out",str(out)])
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(json.loads(proc.stdout)["status"],"fail")

    def test_support_reject_wait_all_settle_at_real_archive_due_day(self):
        audit=self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            root=Path(tmp)/"input"; out=Path(tmp)/"out"
            for d in ["20260902","20260903","20260904"]: (root/d).mkdir(parents=True)
            # 受控工作流清单/应答；判定使用9/4真实最高连板。
            items=[{"id":"test_"+str(i),"route":"theme","signal":"controlled predicate","condition":{"field":"最高连板","op":"ge","threshold":5}} for i in range(3)]
            write(root/"_学习/自主拓展清单_20260902.json",{"d":"20260902","items":items})
            write(root/"_学习/自主拓展应答_20260902.json",{"日期":"20260902","应答":{x["id"]:{"决定":v} for x,v in zip(items,["不深挖","支持","待验"])}})
            write(root/"_学习/自主拓展清单_20260904.json",{"d":"20260904","items":[]})
            write(root/"_学习/自主拓展应答_20260904.json",{})
            write(root/"_学习/fact_20260904.json",read(SAMPLES/"_学习/fact_20260904.json"))
            result=audit(root,"20260904",out)
            self.assertEqual([x["status"] for x in result["items"]],["true"]*3)
            self.assertTrue(all(x["due_d"]=="20260904" for x in result["items"]))

    def test_old_master_and_distiller_clis_write_only_new_runs(self):
        self.api()
        with tempfile.TemporaryDirectory(dir=BASE/"evidence") as tmp:
            before={p:p.read_bytes() for p in (SAMPLES/"_学习").glob("*.json")}
            for script in ["master结算.py","_认知库蒸馏_五路.py"]:
                proc=self.run_cli(script,["20260904","--root",str(SAMPLES),"--out",str(Path(tmp)/script)])
                self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
                result=json.loads(proc.stdout)
                self.assertEqual(result["status"],"pass")
                self.assertTrue(Path(result["artifact"]).is_file())
            self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
