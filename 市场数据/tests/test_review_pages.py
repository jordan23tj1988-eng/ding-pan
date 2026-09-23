"""P1 contract tests. Temporary files stay under this isolated task directory."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

TASK = Path(os.environ.get("SENTIMENT_P1_TASK", str(Path(__file__).resolve().parents[2]/"codex_workspace"/"stability-20260906"/"p1")))
ROOT = TASK / "root"
sys.path.insert(0, str(ROOT))
ROUTES = ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup")
EXPECTED = {
 "index": ["recommendations", "observations", "routes", "turning", "verdict", "master"],
 "cycle": ["volume", "leading", "stages", "ladder", "position", "research", "cognition"],
 "auction": ["pool", "settlement", "temperature", "winrate", "research", "cognition"],
 "lhb": ["seats", "temperature", "ledger", "tiers", "research", "cognition"],
 "theme": ["recommendations", "matrix", "lifecycle", "research", "cognition"],
 "logic": ["recommendations", "chains", "hardness", "forward", "earnings", "research", "cognition"],
 "limitup": ["recommendations", "temperature", "ledger", "training", "research", "cognition"],
}

class Fixture(unittest.TestCase):
 def setUp(self):
  self.tmp = tempfile.TemporaryDirectory(prefix="p1-test-", dir=TASK / "evidence")
  self.addCleanup(self.tmp.cleanup)
  self.root = Path(self.tmp.name) / "input"
  self.root.mkdir()
  (self.root/"test_evidence.json").write_text('{"d":"20260904","value":null}',encoding="utf-8")
  self.out = Path(self.tmp.name) / "output"
 def api(self):
  self.assertIsNotNone(importlib.util.find_spec("review_pages"), "P1 review_pages API is not implemented")
  import review_pages
  return review_pages

class PagesTest(Fixture):
 def test_seven_stable_skeletons_with_four_kpis_and_nulls(self):
  api = self.api()
  for route in ROUTES:
   with self.subTest(route=route):
    m=api.build_page_model(self.root,"20260904",route)
    self.assertEqual([s["id"] for s in m["sections"]], EXPECTED[route])
    self.assertEqual(len(m["kpis"]),4)
    self.assertTrue(all(k["value"] is None for k in m["kpis"]))
    self.assertFalse(m["complete"])
    self.assertEqual(m["status"],"degraded")
 def test_site_paths_models_and_unique_numbering(self):
  result=self.api().build_site(self.root,"20260904",self.out)
  self.assertEqual(set(result["pages"]),set(ROUTES))
  for route,p in result["pages"].items():
   self.assertTrue(Path(p).is_absolute())
   h=Path(p).read_text(encoding="utf-8")
   self.assertEqual(h.count('class="kpi"'),4)
   expected_h2=len(EXPECTED[route]) - (2 if route == 'theme' else 0)
   self.assertEqual(h.count('<h2>'),expected_h2)
   self.assertEqual(h.count('class="rowA"'),1)
   model=json.loads((self.out/"models"/(route+".json")).read_text(encoding="utf-8"))
   self.assertEqual(model["schema_version"],1)
   self.assertEqual(model["d"],"20260904")
 def test_same_input_is_byte_deterministic(self):
  api=self.api();api.build_site(self.root,"20260904",self.out)
  first={str(p.relative_to(self.out)):p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
  api.build_site(self.root,"20260904",self.out)
  self.assertEqual(first,{str(p.relative_to(self.out)):p.read_bytes() for p in self.out.rglob("*") if p.is_file()})
 def test_invalid_date_or_route_returns_failure_without_output(self):
  api=self.api()
  for d in ["2026-09-04","20260230","2026094","２０２６０９０４","../../bad"]:
   r=api.build_site(self.root,d,self.out)
   self.assertEqual(r["status"],"fail")
   self.assertTrue(r["errors"])
   self.assertFalse(self.out.exists())
  self.assertEqual(api.build_page_model(self.root,"20260904","bad")["status"],"fail")

if __name__ == "__main__": unittest.main()
