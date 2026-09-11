"""Whole-page imported content regression checks, not tag-hash snapshots."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from tests.test_review_pages import Fixture, TASK, ROUTES, EXPECTED

ANCHORS={
 'index': ['CROSSPICK','IDXTEMP','IDXLEAD','IDXVOTE'],
 'cycle': ['VOLSTEP','LEADIND','LADDER','MACHVOTE','VOTEBOARD'],
 'auction': ['SCORECARD','POOLLEDGER','MACHSIG'],
 'lhb': ['FUNDTEMP','LHBLEDGER','SEATCARD'],
 'theme': ['THEMEBATTLE','6YOU','FOURDIM','LIFECYCLE'],
 'logic': ['MACHCHAIN','MACHRADAR','MACHHIST'],
 'limitup': ['LEDGER','TEMPCARD','SCORECARD'],
}
class LayoutTests(Fixture):
 def sample(self,d='20260904'):
  shutil.copytree(TASK/'evidence'/'samples'/d,self.root,dirs_exist_ok=True)
 def test_real_pages_have_only_four_kpis_fixed_headings_and_balanced_machine_anchors(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  for route,path in r['pages'].items():
   with self.subTest(route=route):
    h=Path(path).read_text(encoding='utf-8')
    self.assertEqual(len(re.findall(r'class="kpi"',h)),4)
    self.assertEqual(len(re.findall(r'<h2>',h)),len(EXPECTED[route]))
    m=json.loads((self.out/'models'/(route+'.json')).read_text(encoding='utf-8'))
    for anchor in ANCHORS[route]:
     expected=1 if anchor in m['machine_anchors'] else 0
     self.assertEqual(h.count('<!--'+anchor+'-->'),expected,anchor)
     self.assertEqual(h.count('<!--/'+anchor+'-->'),expected,anchor)
 def test_old_day_tables_are_linked_once_not_copied_into_current_sections(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  for route in ['auction','lhb','limitup']:
   m=json.loads((self.out/'models'/(route+'.json')).read_text(encoding='utf-8'))
   histories=[c for c in m['claims'] if c.get('history_ref')]
   self.assertGreater(len(histories),0)
   h=Path(r['pages'][route]).read_text(encoding='utf-8')
   for c in histories:
    self.assertNotIn(c.get('legacy_html','NO_HTML_EXPECTED'),h)
    link=c['history_ref']
    if c.get('component_ref'):
     self.assertIn('href="#component-'+c['component_ref']+'"',h)
     self.assertIn('foldarchive',h)
    else:self.assertIn('href="'+link+'"',h)
    self.assertTrue((self.out/link.split('#')[0]).is_file())
 def test_theme_matrix_is_real_table_with_all_source_names_and_explicit_scope(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  h=Path(r['pages']['theme']).read_text(encoding='utf-8')
  self.assertIn('id="theme-judgment-matrix"',h)
  self.assertIn('判断范围',h);self.assertIn('数据口径',h)
  self.assertEqual(h.count('data-theme-name='),12)
 def test_each_body_atom_has_coverage_and_audit_raw_is_reachable(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  m=json.loads((self.out/'models/theme.json').read_text(encoding='utf-8'))
  coverage=m['content_coverage']
  self.assertIn('source_items',coverage)
  self.assertEqual(coverage['source_total'],len(coverage['source_items']))
  for item in coverage['source_items']:
   self.assertTrue(item['claim_id']);self.assertIn(item['status'],['displayed','referenced'])
  h=Path(r['pages']['theme']).read_text(encoding='utf-8')
  self.assertIn('audit/theme.json',h)
  audit=json.loads((self.out/'audit/theme.json').read_text(encoding='utf-8'))
  source=json.loads((self.root/'_学习/judgment_20260904.json').read_text(encoding='utf-8-sig'))
  self.assertEqual(audit['legacy_bodies'][0]['raw'],source['bodies']['theme'])
 def test_source_input_directory_cannot_be_output(self):
  self.sample();before=(self.root/'_学习/judgment_20260904.json').read_bytes()
  r=self.api().build_site(self.root,'20260904',self.root/'_学习')
  self.assertEqual(r['status'],'fail')
  self.assertEqual(before,(self.root/'_学习/judgment_20260904.json').read_bytes())

 def test_legacy_hero_is_source_excerpt_and_full_conditions_stay_visible(self):
  self.sample();m=self.api().build_page_model(self.root,'20260904','theme')
  self.assertIn('summary_of',m['hero'])
  key=m['hero']['summary_of'];c=next(c for c in m['claims'] if c['id']==key)
  self.assertTrue(c['text'].startswith(m['hero']['text']))
  self.assertNotEqual(m['hero']['text'],c['text'])
  r=self.api().build_site(self.root,'20260904',self.out)
  from html import escape
  h=Path(r['pages']['theme']).read_text(encoding='utf-8')
  self.assertIn(escape(c['text']),h)
  hero=h.split('<div class="hero">',1)[1].split('</div> <div class="kpi">',1)[0]
  self.assertNotIn('href="#claim-'+key+'"',hero)
  self.assertNotIn('回看完整判断与证据',hero)

 def test_identical_nested_data_table_rendered_once_with_accessible_reference(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  import collections
  api=self.api();h=Path(r['pages']['lhb']).read_text(encoding='utf-8');tree=api._Tree(h).root
  tables=[]
  def visit(n):
   if not isinstance(n,api._Node):return
   if n.tag=='table':tables.append(api._safe_html(n));return
   for child in n.children:visit(child)
  visit(tree)
  self.assertEqual(max(collections.Counter(tables).values()),1)
  self.assertTrue('href="#table-' in h or 'href="#component-' in h)
 def test_legacy_ticker_retained_with_today_values(self):
  self.sample();r=self.api().build_site(self.root,'20260904',self.out)
  h=Path(r['pages']['limitup']).read_text(encoding='utf-8')
  self.assertIn('<div class="ticker">',h)
  block=h.split('<div class="ticker">',1)[1].split('</div>',1)[0]
  for value in ['39','13.4','龙版传媒','5板1']:self.assertIn(value,block)
