"""Real frozen September samples; mutations are explicitly labelled error injections."""
import hashlib
from html import escape
import json
from pathlib import Path
import shutil
from tests.test_review_pages import Fixture, TASK, ROUTES, EXPECTED

class LegacyTests(Fixture):
 def sample(self,d="20260904"):
  shutil.copytree(TASK/"evidence"/"samples"/d,self.root,dirs_exist_ok=True)
 def test_real_today_cognition_all_entries_visible_for_three_loss_paths(self):
  self.sample();r=self.api().build_site(self.root,"20260904",self.out)
  self.assertIn("pages",r,r)
  for route in ['lhb','theme','logic']:
   src=json.loads((self.root/'_学习'/f'{route}判断_20260904.json').read_text(encoding='utf-8-sig'))
   h=Path(r['pages'][route]).read_text(encoding='utf-8')
   for entry in src['认知迭代']:
    self.assertIn(escape(entry),h)
   m=self.api().build_page_model(self.root,'20260904',route)
   self.assertGreaterEqual(len([c for c in m['claims'] if c['role']=='cognition']),len(src['认知迭代']))
 def test_theme_all_twelve_named_judgments_reachable_without_name_merging(self):
  self.sample();m=self.api().build_page_model(self.root,'20260904','theme')
  src=json.loads((self.root/'_学习'/'题材龙头判断_20260904.json').read_text(encoding='utf-8-sig'))
  self.assertEqual(len(src['判断']),12)
  self.assertEqual({row['name'] for row in m.get('theme_matrix',[])},set(src['判断']))
  self.assertEqual(m['content_coverage']['unmapped'],[])
  for name,text in src['判断'].items():
   matches=[c for c in m['claims'] if c['text']==text]
   self.assertTrue(matches,name)
   self.assertTrue(any(name.replace('~','~0').replace('/','~1') in c['source_pointer'] for c in matches))
 def test_missing_cycle_is_degraded_with_same_day_facts_no_future_substitution(self):
  self.sample();api=self.api();m=api.build_page_model(self.root,'20260904','cycle')
  self.assertFalse(m['complete']);self.assertEqual(m['status'],'degraded')
  # Fixture contains an independent same-day vote even though cycle prose is absent.
  vote_path=self.root/'_学习'/'_周期投票台账.jsonl'
  votes=[json.loads(line) for line in vote_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
  today=next(row for row in votes if row.get('d')=='20260904')
  self.assertEqual(today['主判']['stage'],'冰点')
  self.assertEqual([k['value'] for k in m['kpis']],[20307.0,today['主判']['stage'],13.4,None])
  self.assertEqual([s['id'] for s in m['sections']],EXPECTED['cycle'])
  p=self.root/'_学习'/'fact_20260904.json';p.unlink()
  table=self.root/'_学习'/'_市场温度表.json';data=json.loads(table.read_text(encoding='utf-8-sig'));data.pop('20260904',None);table.write_text(json.dumps(data),encoding='utf-8')
  m=api.build_page_model(self.root,'20260904','cycle')
  self.assertEqual([k['value'] for k in m['kpis']],[None,today['主判']['stage'],None,None])
  # Explicit error injection: remove today's vote; a future vote must not fill it.
  votes=[row for row in votes if row.get('d')!='20260904']
  votes.append({'d':'20260907','主判':{'stage':'ERROR_INJECTION_FUTURE'}})
  vote_path.write_text('\n'.join(json.dumps(row,ensure_ascii=False) for row in votes),encoding='utf-8')
  m=api.build_page_model(self.root,'20260904','cycle')
  self.assertTrue(all(k['value'] is None for k in m['kpis']))
 def test_actual_paper_dashboard_retained_and_source_files_unchanged(self):
  self.sample('20260902');before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
  r=self.api().build_site(self.root,'20260902',self.out)
  self.assertIn('pages',r,r)
  checked=0
  for route in ROUTES:
   src=self.root/'_学习/_模拟盘'/('master' if route=='index' else route)/'看板_20260902.html'
   if src.exists():
    h=Path(r['pages'][route]).read_text(encoding='utf-8')
    self.assertIn(src.read_text(encoding='utf-8-sig'),h)
    self.assertEqual(h.count('<!--PAPERTRADE-->'),1)
    checked+=1
  self.assertGreater(checked,0)
  self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()})
 def test_unknown_legacy_heading_or_json_field_fails_instead_of_discarding(self):
  self.sample();p=self.root/'_学习'/'judgment_20260904.json';x=json.loads(p.read_text(encoding='utf-8-sig'))
  x['bodies']['theme']+='<h2>测试错误注入：未知栏目</h2><p>TEST_UNMAPPED</p>'
  p.write_text(json.dumps(x),encoding='utf-8')
  m=self.api().build_page_model(self.root,'20260904','theme')
  self.assertEqual(m['status'],'fail');self.assertIn('未归位',' '.join(m['errors']))
 def test_body_only_cognition_variants_remain_visible(self):
  self.sample();p=self.root/'_学习'/'judgment_20260904.json';x=json.loads(p.read_text(encoding='utf-8-sig'))
  cases={'lhb':'<h2>六 认知迭代</h2><div class="tli"><p>TEST_BODY_LHB</p></div>',
         'theme':'<h2>六 认知迭代</h2><div class="grp"><ul><li>TEST_BODY_THEME</li></ul></div>',
         'logic':'<h2>六 认知迭代</h2><div class="tli"><div class="h">2026-09-04 · TEST_BODY_LOGIC</div><div class="d">TEST_CONDITION</div></div>'}
  for route,body in cases.items():
   (self.root/'_学习'/f'{route}判断_20260904.json').unlink();x['bodies'][route]=body
  p.write_text(json.dumps(x),encoding='utf-8');r=self.api().build_site(self.root,'20260904',self.out)
  self.assertIn('pages',r,r)
  for route in cases:
   h=Path(r['pages'][route]).read_text(encoding='utf-8');self.assertIn('TEST_BODY_'+route.upper(),h)
 def test_real_legacy_second_render_identical_and_claim_coverage_exhaustive(self):
  self.sample('20260902');api=self.api();r=api.build_site(self.root,'20260902',self.out)
  self.assertIn('pages',r,r)
  before={str(p.relative_to(self.out)):p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
  api.build_site(self.root,'20260902',self.out)
  self.assertEqual(before,{str(p.relative_to(self.out)):p.read_bytes() for p in self.out.rglob('*') if p.is_file()})
  for route in ROUTES:
   m=json.loads((self.out/'models'/(route+'.json')).read_text(encoding='utf-8'))
   self.assertGreater(m['content_coverage']['total'],0)
   self.assertEqual(m['content_coverage']['total'],m['content_coverage']['covered'])
   self.assertEqual(m['content_coverage']['unmapped'],[])
