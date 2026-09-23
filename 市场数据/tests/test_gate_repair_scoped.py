"""Current private P1.2; controlled corruption is TEST ONLY, never financial inputs."""
import json, re, shutil
import os
from pathlib import Path
import pytest
import review_pages as pages
import review_publish as pub
_TASK=Path(os.environ.get("SENTIMENT_P1_TASK", str(Path(__file__).resolve().parents[2]/"codex_workspace"/"stability-20260906"/"p1")))
ROOT=Path(os.environ.get("SENTIMENT_P12_ROOT", str(_TASK.parent/"integration"/"root")))
@pytest.fixture(scope="module")
def stage(tmp_path_factory):
 out=tmp_path_factory.mktemp("current-p12")
 result=pages.build_site(ROOT,"20260902",out)
 assert result["status"] != "fail",result
 return out

def test_cycle_p12_real_and_negative(stage):
 raw=(stage/"cycle.html").read_text(encoding="utf-8")
 assert pub.scoped_p12_check(ROOT,stage,"20260902","cycle")["status"]=="pass"
 for bad in [raw.replace('<section id="volume">','<section id="TEST_MISSING">',1),raw.replace('<section id="leading">','<section id="TEST_MISSING">',1),raw.replace('<section id="stages">','<section id="TEST_MISSING">',1),raw.replace('<section id="ladder">','<section id="TEST_MISSING">',1)]:
  assert pub.scoped_p12_check(ROOT,stage,"20260902","cycle",raw=bad)["status"]=="fail"

def test_auction_alias_and_true_settlement_date(stage):
 raw=(stage/"auction.html").read_text(encoding="utf-8")
 assert raw.count("<!--MACHPOOL-->")==1
 assert pub.scoped_p12_check(ROOT,stage,"20260902","auction")["status"]=="pass"
 source=json.loads((ROOT/"_学习/竞价池结算_20260902.json").read_text(encoding="utf-8"))
 assert source["结算日"]=="20260903" and source["汇总"]["次日封板"]=="2/11"
 assert pub.previous_pool_check(ROOT,stage,"20260902")["pool_date"]=="20260901"
 assert pub.previous_pool_check(ROOT,stage,"20260902")["status"]=="pass"

def test_lhb_dated_counts_and_future_negative(stage,monkeypatch):
 good=pub.scoped_p12_check(ROOT,stage,"20260902","lhb")
 assert good["status"]=="pass",good
 original=pub.seat_snapshot
 monkeypatch.setattr(pub,"seat_snapshot",lambda root,d:dict(original(root,d),窗口="20260401~20260903"))
 assert pub.scoped_p12_check(ROOT,stage,"20260902","lhb")["status"]=="fail"

def test_lhb_missing_and_corrupt_counts(stage,monkeypatch):
 raw=(stage/"lhb.html").read_text(encoding="utf-8")
 assert pub.scoped_p12_check(ROOT,stage,"20260902","lhb",raw=raw.replace("S22/A43","S99/A43"))["status"]=="fail"
 monkeypatch.setattr(pub,"seat_snapshot",lambda root,d:None)
 assert pub.scoped_p12_check(ROOT,stage,"20260902","lhb")["status"]=="fail"

def walk(node):
 if isinstance(node,pages._Node):
  yield node
  for child in node.children:yield from walk(child)

def test_cognition_one_visible_and_unique_fold_all_routes(stage):
 for route in ("cycle","lhb","logic","auction","limitup"):
  raw=(stage/(route+".html")).read_text(encoding="utf-8")
  nodes=list(walk(pages._Tree(raw).root));section=next(n for n in nodes if n.attrs.get("id")=="cognition")
  folds=[n for n in walk(section) if "tlfold" in n.attrs.get("class","").split()]
  model=json.loads((stage/"models"/(route+".json")).read_text(encoding="utf-8"))
  cognition=[c for c in model["claims"] if c["section"]=="cognition" and c["role"]=="cognition"]
  if len(cognition)>1:
   assert len(folds)==1,(route,len(folds))
   folded={n.attrs.get("id") for n in walk(folds[0])}
   assert sum("claim-"+c["id"] not in folded for c in cognition)==1,route
  for c in cognition:assert c["text"] in section.text(),(route,c["id"])
