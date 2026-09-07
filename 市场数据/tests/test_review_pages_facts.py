"""Fact-source and strict safety checks; values copied from real frozen samples."""
import json
from pathlib import Path
import shutil
from tests.test_review_pages import Fixture,TASK
from tests import test_review_pages_structured as structured

class FactsTests(Fixture):
 def sample(self):shutil.copytree(TASK/'evidence/samples/20260904',self.root,dirs_exist_ok=True)
 def test_cycle_gap_has_fact_evidence_in_volume_leading_and_ladder_sections(self):
  self.sample();m=self.api().build_page_model(self.root,'20260904','cycle')
  self.assertFalse(m['complete'])
  for sid in ['volume','leading','ladder']:
   s=next(s for s in m['sections'] if s['id']==sid)
   self.assertTrue(s['claim_refs'],sid)
  self.assertFalse(any(c['role']=='verdict' for c in m['claims']))
  refs=[c['source_pointer'] for c in m['claims']]
  self.assertTrue(any('20260904' in p for p in refs))
 def test_six_you_exact_name_match_only_with_source_and_unknown_null(self):
  self.sample();m=self.api().build_page_model(self.root,'20260904','theme')
  rows={r['name']:r for r in m['theme_matrix']}
  self.assertEqual(rows['农业/养殖(猪周期)']['six_you'],2)
  self.assertIsNone(rows['农业']['six_you'])
  self.assertTrue(rows['农业/养殖(猪周期)']['evidence_refs'])
 def test_kpi_value_must_equal_referenced_evidence(self):
  # Controlled invalid KPI: string differs from TEST_CONTROLLED evidence null.
  doc=structured.StructuredTests.document(self)
  doc['pages']['theme']['kpis'][0]['value']='TEST_INJECTED_WRONG_VALUE'
  doc['pages']['theme']['kpis'][0]['evidence_refs']=['ev-test']
  (self.root/'_学习').mkdir();(self.root/'_学习/页面判断_20260904.json').write_text(json.dumps(doc),encoding='utf-8')
  result=self.api().build_site(self.root,'20260904',self.out)
  self.assertEqual(result['status'],'fail')
 def test_malformed_collection_returns_fail_not_exception(self):
  for value in [None,True,[],5]:
   doc=structured.StructuredTests.document(self);doc['pages']['theme']['claims']=value
   folder=self.root/'_学习';folder.mkdir(exist_ok=True)
   (folder/'页面判断_20260904.json').write_text(json.dumps(doc),encoding='utf-8')
   result=self.api().build_site(self.root,'20260904',self.out)
   self.assertEqual(result['status'],'fail')
 def test_engine_artifact_active_content_fails_without_rewriting_artifact(self):
  self.sample();p=self.root/'_学习/_模拟盘/theme/看板_20260904.html'
  p.write_text('<script>TEST_ERROR_INJECTION</script>',encoding='utf-8')
  m=self.api().build_page_model(self.root,'20260904','theme')
  self.assertEqual(m['status'],'fail')
  self.assertEqual(p.read_text(encoding='utf-8'),'<script>TEST_ERROR_INJECTION</script>')

 def test_json_source_pointers_resolve_to_exact_original_values(self):
  self.sample();api=self.api()
  for route in ['index','cycle','auction','lhb','theme','logic','limitup']:
   m=api.build_page_model(self.root,'20260904',route)
   for c in m['claims']:
    if c['source'].startswith('judgment_'):continue
    src=json.loads((self.root/'_学习'/c['source']).read_text(encoding='utf-8-sig'))
    for part in c['source_pointer'].split('/')[1:]:
     key=part.replace('~1','/').replace('~0','~')
     self.assertTrue(isinstance(src,(dict,list)),c['source_pointer'])
     if isinstance(src,dict):self.assertIn(key,src,c['source_pointer'])
     src=src[int(key)] if isinstance(src,list) else src[key]
    if c['source'].endswith('判断_20260904.json') or c['source'].startswith('总审_'):
     expected=src if isinstance(src,str) else json.dumps(src,ensure_ascii=False,indent=2)
     self.assertEqual(c['text'],expected)
