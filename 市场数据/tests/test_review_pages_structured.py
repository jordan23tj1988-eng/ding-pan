"""Controlled non-financial input and explicit error injections for schema-v1."""
import json
from html import escape
from pathlib import Path
from tests.test_review_pages import Fixture, EXPECTED, ROUTES

class StructuredTests(Fixture):
 def document(self):
  pages={}
  for route in ROUTES:
   claims=[{"id":route+"-"+s,"section":s,"role":"cognition" if s=="cognition" else "evidence",
            "text":"测试控制文本："+route+"/"+s,"evidence_refs":["ev-test"]} for s in EXPECTED[route]]
   pages[route]={"hero":{"claim_ref":claims[0]["id"],"change_ref":None},
     "kpis":[{"id":str(i),"label":"测试空值槽"+str(i),"value":None,"evidence_refs":[]} for i in range(4)],
     "claims":claims,"sections":[{"id":s,"claim_refs":[route+"-"+s]} for s in EXPECTED[route]],"limitations":[]}
  return {"schema_version":1,"d":"20260904","evidence":[{"id":"ev-test","d":"20260904","source":"test_evidence.json", "pointer":"/value", "value":None}],"pages":pages}
 def put(self,doc):
  folder=self.root/"_学习";folder.mkdir(exist_ok=True)
  (folder/"页面判断_20260904.json").write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
 def test_structured_primary_complete_and_source_claims_reachable(self):
  doc=self.document();self.put(doc)
  result=self.api().build_site(self.root,"20260904",self.out)
  self.assertEqual(result["status"],"degraded",result) # judgment complete, producer artifacts intentionally absent
  for route in ROUTES:
   m=json.loads((self.out/"models"/(route+".json")).read_text(encoding="utf-8"))
   self.assertEqual(m["content_coverage"]["total"],len(doc["pages"][route]["claims"]))
   self.assertEqual(m["content_coverage"]["covered"],m["content_coverage"]["total"])
   self.assertTrue(m["judgment_complete"])
   self.assertFalse(m["complete"])
   self.assertFalse(m["machine_complete"])
   self.assertGreaterEqual(len(m["editorial_notes"]),3)
   self.assertLessEqual(len(m["editorial_notes"]),5)
   h=Path(result["pages"][route]).read_text(encoding="utf-8")
   for c in doc["pages"][route]["claims"]:
    if route == 'theme' and c['section'] in ('matrix','lifecycle','research','cognition'):
     self.assertNotIn('id="claim-'+c["id"]+'"',h)
     continue
    self.assertIn('id="claim-'+c["id"]+'"',h)
    self.assertIn(escape(c["text"]),h)
 def test_exact_claim_reuse_uses_accessible_reference_not_repetition(self):
  doc=self.document();p=doc["pages"]["logic"]
  p["sections"][-1]["claim_refs"].append(p["claims"][1]["id"])
  self.put(doc);r=self.api().build_site(self.root,"20260904",self.out)
  h=Path(r["pages"]["logic"]).read_text(encoding="utf-8")
  self.assertEqual(h.count(p["claims"][1]["text"]),1)
  self.assertIn('href="#claim-logic-chains"',h)
  m=self.api().build_page_model(self.root,"20260904","logic")
  self.assertTrue(m["role_overlap"])
 def test_negation_condition_and_date_are_never_similarity_deleted(self):
  doc=self.document();p=doc["pages"]["logic"]
  texts=["测试控制：条件甲成立", "测试控制：条件甲不成立", "测试控制：仅在20260904条件甲成立", "测试控制：仅在20260907条件甲成立"]
  for i,t in enumerate(texts):
   c={"id":"case-"+str(i),"text":t,"role":"counterevidence" if i==1 else "condition","section":"hardness","evidence_refs":["ev-test"]}
   p["claims"].append(c);p["sections"][2]["claim_refs"].append(c["id"])
  self.put(doc);r=self.api().build_site(self.root,"20260904",self.out)
  h=Path(r["pages"]["logic"]).read_text(encoding="utf-8")
  for t in texts:self.assertIn(t,h)
 def test_html_text_and_attribute_injection_are_escaped(self):
  doc=self.document();p=doc["pages"]["theme"]
  p["claims"][1]["text"]='<script>alert("TEST")</script><img src=x onerror=alert(1)> & 条件 < 阈值'
  p["kpis"][0]["label"]='"><img src=x onerror=alert(1)>'
  self.put(doc);r=self.api().build_site(self.root,"20260904",self.out)
  h=Path(r["pages"]["theme"]).read_text(encoding="utf-8")
  self.assertNotIn(escape(p["claims"][1]["text"]),h)
  self.assertNotIn('<script>alert',h)
  self.assertNotIn('<img src=x',h)
 def test_unknown_mapping_missing_reference_and_future_evidence_fail(self):
  for mutation in ['section','ref','future','schema','date','unknown','duplicate','missing']:
   with self.subTest(mutation=mutation):
    doc=self.document();p=doc["pages"]["theme"]
    if mutation=='section':p["claims"][0]["section"]='unmapped'
    if mutation=='ref':p["claims"][0]["evidence_refs"]=['missing']
    if mutation=='future':doc["evidence"][0]["d"]='20260907'
    if mutation=='schema':doc["schema_version"]=2
    if mutation=='date':doc["d"]='20260903'
    if mutation=='unknown':p['unknown_judgment']="不得静默删除"
    if mutation=='duplicate':p['claims'][1]['id']=p['claims'][0]['id']
    if mutation=='missing':p['sections'][1]['claim_refs']=[]
    self.put(doc);r=self.api().build_site(self.root,"20260904",self.out)
    self.assertEqual(r['status'],'fail',r)
    self.assertTrue(r['errors'])
    self.assertFalse(self.out.exists())
 def test_structured_cognition_takes_priority_over_broken_legacy_html(self):
  doc=self.document();self.put(doc)
  (self.root/'_学习'/'judgment_20260904.json').write_text('{bad legacy JSON',encoding='utf-8')
  m=self.api().build_page_model(self.root,'20260904','lhb')
  self.assertEqual(m['status'],'degraded',m)
  self.assertTrue(m['judgment_complete'])
  self.assertIn('lhb-cognition',[c['id'] for c in m['claims'] if c['role']=='cognition'])

 def test_structured_theme_matrix_keeps_named_rows_and_empty_template(self):
  doc=self.document();doc['pages']['theme']['matrix']=[{'name':'TEST_SCOPE_A','claim_refs':['theme-matrix'],'six_you':None,'evidence_refs':[]}]
  self.put(doc);r=self.api().build_site(self.root,'20260904',self.out)
  self.assertIn('pages',r,r)
  h=Path(r['pages']['theme']).read_text(encoding='utf-8')
  self.assertIn('data-theme-name="TEST_SCOPE_A"',h)
  doc['pages']['theme'].pop('matrix');self.put(doc)
  r=self.api().build_site(self.root,'20260904',self.out)
  h=Path(r['pages']['theme']).read_text(encoding='utf-8')
  self.assertIn('id="theme-judgment-matrix"',h)
 def test_role_overlap_warns_on_misplaced_cognition_without_deleting_it(self):
  doc=self.document();doc['pages']['logic']['claims'][1]['role']='cognition'
  self.put(doc);m=self.api().build_page_model(self.root,'20260904','logic')
  self.assertTrue(m['role_overlap'])
  self.assertEqual(m['content_coverage']['total'],m['content_coverage']['covered'])
