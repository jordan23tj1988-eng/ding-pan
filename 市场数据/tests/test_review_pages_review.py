"""Parent R1 regressions using disk evidence and complete read-only integration data."""
import json,hashlib
from pathlib import Path
from tests.test_review_pages import Fixture,TASK
from tests import test_review_pages_structured as primary

class ReviewTests(Fixture):
 def test_evidence_cannot_self_attest_value_date_hash_or_escape_root(self):
  for mutation in ['value','date','hash','path','pointer']:
   with self.subTest(mutation=mutation):
    doc=primary.StructuredTests.document(self)
    ev=doc['evidence'][0]
    if mutation=='value':ev['value']='FORGED'
    if mutation=='date':ev['d']='20260903'
    if mutation=='hash':ev['sha256']='0'*64
    if mutation=='path':ev['source']='../escape.json'
    if mutation=='pointer':ev['pointer']='/missing'
    folder=self.root/'_学习';folder.mkdir(exist_ok=True)
    (folder/'页面判断_20260904.json').write_text(json.dumps(doc),encoding='utf-8')
    r=self.api().build_page_model(self.root,'20260904','theme')
    self.assertEqual(r['status'],'fail',mutation)
 def test_valid_disk_evidence_records_verified_hash_and_value(self):
  doc=primary.StructuredTests.document(self);primary.StructuredTests.put(self,doc)
  m=self.api().build_page_model(self.root,'20260904','theme')
  self.assertEqual(m['evidence'][0].get('sha256'),hashlib.sha256((self.root/'test_evidence.json').read_bytes()).hexdigest())
  self.assertTrue(m['evidence'][0].get('verified'))

 def test_golden_kpi_subcomponents_and_route_specific_fields(self):
  r=self.api().build_site(TASK.parent/'integration/root','20260902',self.out)
  labels={}
  for route,path in r['pages'].items():
   m=json.loads((self.out/'models'/(route+'.json')).read_text(encoding='utf-8'))
   labels[route]=[k['label'] for k in m['kpis']]
   tree=self.api()._Tree(Path(path).read_text(encoding='utf-8')).root
   def nodes(n):
    if isinstance(n,self.api()._Node):
     yield n
     for c in n.children:yield from nodes(c)
   for node in [n for n in nodes(tree) if 'kpi' in n.attrs.get('class','').split()]:
    classes=[c.attrs.get('class','').split() for c in nodes(node)]
    for required in ['top','chip2','lab','big','sub2']:
     self.assertTrue(any(required in c for c in classes),(route,required))
  self.assertNotEqual(labels['auction'],labels['cycle'])
  self.assertNotEqual(labels['lhb'],labels['limitup'])
 def test_machine_components_have_source_hashes_real_graphics_and_no_fake_anchors(self):
  r=self.api().build_site(TASK.parent/'integration/root','20260902',self.out)
  for route in ['cycle','lhb','logic','theme','limitup']:
   m=json.loads((self.out/'models'/(route+'.json')).read_text(encoding='utf-8'))
   self.assertTrue(m.get('components'),route)
   for c in m['components']:
    if c['status']=='ok':
     self.assertTrue(c['sources']);self.assertTrue(all(x['sha256'] for x in c['sources']))
   h=Path(r['pages'][route]).read_text(encoding='utf-8')
   self.assertIn('<svg',h,route)
  h=Path(r['pages']['logic']).read_text(encoding='utf-8');self.assertIn('class="hb"',h)
  h=Path(r['pages']['theme']).read_text(encoding='utf-8');self.assertIn('class="lifeaxis"',h);self.assertIn('核心标的',h)
  empty=self.api().build_site(self.root,'20260904',self.out/'empty')
  for route,path in empty['pages'].items():
   h=Path(path).read_text(encoding='utf-8')
   self.assertNotIn('<!--MACHCHAIN-->',h)
 def test_legacy_components_not_double_wrapped_and_history_has_single_fold(self):
  r=self.api().build_site(TASK.parent/'integration/root','20260902',self.out)
  h=Path(r['pages']['lhb']).read_text(encoding='utf-8')
  self.assertIn('foldarchive',h)
  self.assertNotIn('data-role="observation"><div class="obs">',h)

 def test_one_nine_column_matrix_has_all_judgment_names_and_unknowns(self):
  api=self.api();root=TASK.parent/'integration/root';d='20260904'
  mod=api._pure_renderer('theme',root,d);h=mod.r_chart_matrix(d)
  source=json.loads((root/'_学习'/('题材龙头判断_'+d+'.json')).read_text(encoding='utf-8-sig'))
  for name in source['判断']:
   self.assertIn('data-theme-name="'+name+'"',h)
  self.assertEqual(h.count('<th>'),9)
  tree=api._Tree(h).root
  def nodes(n):
   if isinstance(n,api._Node):
    yield n
    for c in n.children:yield from nodes(c)
  for row in [x for x in nodes(tree) if x.attrs.get('data-theme-name')=='农业']:
   self.assertNotIn('0/6',row.text());self.assertIn('—',row.text())
  life=mod.r_chart_lifeaxis(d)
  for name in source['判断']:self.assertIn(name,life)
  self.assertIsNone(mod._stage_by_line([{'线':'农业','阶段':'启动'}],'农业/养殖(猪周期)'))
 def test_fold_history_preserves_outside_daily_blocks(self):
  raw='<p>TEST_LEDGER_CONTEXT</p><details><summary>TEST_DAY_NEW</summary><p>NEW</p></details><details><summary>TEST_DAY_OLD</summary><p>OLD</p></details><p>TEST_TAIL_RISK</p>'
  folded=self.api()._fold_machine_history(raw)
  self.assertIn('TEST_LEDGER_CONTEXT',folded);self.assertIn('TEST_TAIL_RISK',folded)
  self.assertEqual(folded.count('foldarchive'),1)

 def test_pure_component_loading_has_no_global_import_side_effects(self):
  import sys
  before=list(sys.path)
  self.api()._pure_renderer('logic',self.root,'20260904')
  self.assertEqual(sys.path,before)
 def test_safe_components_keep_dom_identity_and_svg_viewbox(self):
  api=self.api();raw='<table id="theme-judgment-matrix"><tr data-theme-name="TEST_A"><td>A</td></tr></table><svg viewBox="0 0 100 50"><path d="M0 0L100 50"/></svg>'
  result=api._safe_html(api._Tree(raw).root)
  self.assertIn('id="theme-judgment-matrix"',result)
  self.assertIn('data-theme-name="TEST_A"',result)
  self.assertIn('viewBox="0 0 100 50"',result)
 def test_radar_never_truncates_evidence_conditions(self):
  mod=self.api()._pure_renderer('logic',self.root,'20260904')
  words='TEST_WORDS_'*20+'仅此条件';reason='TEST_REASON_'*40+'仍可能失败'
  mod.load_json=lambda *args:{'统计':{},'A共振池(重要度排序)':[{'名称':'TEST_CONTROLLED','成色依据':words,'原因':reason}]}
  html=mod.r_mach_radar('20260904')
  self.assertIn(words,html);self.assertIn(reason,html)

 def test_dated_seat_library_never_uses_future_window(self):
  api=self.api();root=TASK.parent/'integration/root'
  for d,window in [('20260902','20260401~20260901'),('20260904','20260401~20260903')]:
   m=api.build_page_model(root,d,'lhb')
   lib=next((c for c in m.get('components',[]) if c['id']=='SEATLIB'),None)
   self.assertIsNotNone(lib);self.assertIn(window,lib['html'])
   self.assertTrue(lib['sources'])
 def test_primary_observations_have_golden_structure_and_evidence_group(self):
  doc=primary.StructuredTests.document(self);page=doc['pages']['index']
  page['claims'][1]['role']='observation'
  primary.StructuredTests.put(self,doc)
  r=self.api().build_site(self.root,'20260904',self.out)
  h=Path(r['pages']['index']).read_text(encoding='utf-8')
  self.assertIn('class="obs-head"',h);self.assertIn('class="obs-watch"',h)
  self.assertNotIn('class="card" id="claim-index-verdict"',h)

 def test_shared_rule_keeps_each_stock_and_distinct_date_window(self):
  api=self.api()
  rule='TEST_RULE：低开才观察；高开超过阈值放弃；小样本不可外推'
  table='<table><tr><th>股票</th><th>次日买入/放弃条件</th></tr><tr><td>TEST_A</td><td>'+rule+'</td></tr><tr><td>TEST_B</td><td>'+rule+'</td></tr></table>'
  registry={}
  out=api._shared_cells(table,'20260904',registry)
  self.assertEqual(out.count(rule),1)
  self.assertIn('TEST_A',out);self.assertIn('TEST_B',out)
  self.assertIn('href="#shared-',out)
  out2=api._shared_cells(table,'20260903',registry)
  self.assertEqual(out2.count(rule),1)
  self.assertEqual(len(registry),2)
  unrelated='<p>'+rule+'</p><p>'+rule+'</p>'
  self.assertEqual(api._shared_cells(unrelated,'20260904',{}).count(rule),2)

 def test_visual_dates_and_missing_metrics_are_not_fabricated(self):
  api=self.api();mod=api._pure_renderer('cycle',self.root,'20260904')
  mod.load_json=lambda *args:{'20260904':{'成交额亿':40000,'温度':None,'涨停数':None}}
  h=mod.r_mach_volstep('20260904')
  self.assertIn('09-04',h);self.assertNotIn('涨停-1',h);self.assertNotIn('温度-1',h)
  folder=self.root/'_学习';folder.mkdir(exist_ok=True)
  (folder/'_市场温度表.json').write_text(json.dumps({'20260903':{'温度':77}}),encoding='utf-8')
  m=api.build_page_model(self.root,'20260904','index')
  self.assertEqual(next(c for c in m['components'] if c['id']=='IDXTEMP')['status'],'missing')

 def test_available_route_kpis_and_trend_are_rendered_with_units(self):
  api=self.api();root=TASK.parent/'integration/root'
  m=api.build_page_model(root,'20260904','index')
  self.assertEqual(m['kpis'][3].get('display'),'12.2%')
  self.assertTrue(m['kpis'][1].get('sparkline'))
  cycle=api.build_page_model(root,'20260904','cycle')
  self.assertEqual(cycle['kpis'][1]['value'],'冰点')
  self.assertFalse(cycle['complete'])
  seat=api.build_page_model(root,'20260904','lhb')
  self.assertEqual(seat['kpis'][2]['value'],'敦煌种业')
