"""R1: actual copied scripts, actual Chrome, actual P1 contract; no fake market data."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests.test_review_publish import TASK, CODE
sys.path.insert(0,str(CODE))
import review_publish as pub

INTEGRATION=TASK.parent/'integration'/'root'
P1=TASK/'evidence'/'r1'/'p1_code_snapshot'
P1_PREVIEW=TASK/'evidence'/'r1'/'p1_preview_20260902'

class R1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='r1-',dir=TASK/'evidence'/'r1')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.stage=self.root/'site';self.stage.mkdir()

    def test_cycle_current_p1_contract_and_anchor_negative(self):
        root=TASK/'evidence'/'r1'/'real_20260902'/'root'
        shutil.copytree(TASK/'evidence'/'r1'/'current_cycle',self.stage,dirs_exist_ok=True)
        good=pub._check_one(root,self.stage,'20260902','cycle')
        self.assertEqual(good['status'],'pass',good)
        self.assertEqual(sum(bool(c.get('replacement_contract')) for c in good['observed_checks'] if not c['negative_injection']),5)
        page=self.stage/'cycle.html'
        page.write_text(page.read_text(encoding='utf-8').replace('<!--LEADIND-->','<!--CONTROLLED_MISSING_ANCHOR-->'),encoding='utf-8')
        bad=pub._check_one(root,self.stage,'20260902','cycle')
        self.assertEqual(bad['status'],'fail',bad)

    def test_limitup_current_p1_recommendations_section_and_bad_rate(self):
        root=TASK/'evidence'/'r1'/'real_20260902'/'root'
        shutil.copytree(TASK/'evidence'/'r1'/'current_p1_routes',self.stage,dirs_exist_ok=True)
        good=pub._check_one(root,self.stage,'20260902','limitup')
        self.assertEqual(good['status'],'pass',good)
        page=self.stage/'limitup.html'
        page.write_text(page.read_text(encoding='utf-8').replace('19.9','99.9'),encoding='utf-8')
        self.assertEqual(pub._check_one(root,self.stage,'20260902','limitup')['status'],'fail')

    def test_lhb_source_card_is_compared_by_rendered_content(self):
        root=TASK/'evidence'/'r1'/'real_20260902'/'root'
        shutil.copytree(TASK/'evidence'/'r1'/'current_p1_routes',self.stage,dirs_exist_ok=True)
        result=pub._check_one(root,self.stage,'20260902','lhb')
        row=next(r for r in result['observed_checks'] if r['label']=='Top5卡在页面')
        self.assertTrue(row['ok'],row)
        # Missing grading-window/count remains a real failure, not waived.
        self.assertEqual(result['status'],'fail')
        page=self.stage/'lhb.html'
        page.write_text(page.read_text(encoding='utf-8').replace('component-SEATCARD','CONTROLLED_REMOVED_CARD'),encoding='utf-8')
        bad=pub._check_one(root,self.stage,'20260902','lhb')
        self.assertFalse(next(r for r in bad['observed_checks'] if r['label']=='Top5卡在页面')['ok'])

    def test_auction_uses_previous_pool_settled_today_and_rejects_bad_ratio(self):
        root=TASK/'evidence'/'r1'/'real_20260902'/'root'
        shutil.copytree(TASK/'evidence'/'r1'/'current_p1_routes',self.stage,dirs_exist_ok=True)
        good=pub._check_one(root,self.stage,'20260902','auction')
        self.assertEqual(good['settlement_validation']['status'],'pass',good)
        self.assertEqual(good['settlement_validation']['pool_date'],'20260901')
        self.assertTrue(all(r['ok'] for r in good['observed_checks'] if not r['negative_injection']))
        # Actual P1 omits MACHPOOL although its own contract requires it. Keep
        # this independent structural blocker; do not pretend whole-page PASS.
        self.assertEqual(good['status'],'fail')
        self.assertIn('machine anchor pair MACHPOOL',good['errors'])
        self.assertEqual(good['view_verification']['errors'],['machine anchor pair MACHPOOL'])
        page=self.stage/'auction.html'
        page.write_text(page.read_text(encoding='utf-8').replace('6/19','9/19'),encoding='utf-8')
        self.assertEqual(pub._check_one(root,self.stage,'20260902','auction')['status'],'fail')

    def test_machine_component_cannot_forge_model_and_dom_together(self):
        root=TASK/'evidence'/'r1'/'real_20260902'/'root'
        shutil.copytree(TASK/'evidence'/'r1'/'current_cycle',self.stage,dirs_exist_ok=True)
        self.assertEqual(pub.view_check(root,self.stage,'20260902','cycle')['status'],'pass')
        mp=self.stage/'models'/'cycle.json';model=pub.read_json(mp)
        comp=next(c for c in model['components'] if c['id']=='LEADIND')
        comp['html']+='<b>CONTROLLED UNSUPPORTED MACHINE VALUE</b>'
        mp.write_text(json.dumps(model,ensure_ascii=False),encoding='utf-8')
        page=self.stage/'cycle.html'
        page.write_text(page.read_text(encoding='utf-8').replace('<!--/LEADIND-->','<b>CONTROLLED UNSUPPORTED MACHINE VALUE</b><!--/LEADIND-->'),encoding='utf-8')
        self.assertEqual(pub.view_check(root,self.stage,'20260902','cycle')['status'],'fail')

    def test_consistency_exception_does_not_claim_unexecuted_rules(self):
        for name in ('复盘一致性哨兵.py','trading_calendar.py'):
            shutil.copy2(CODE/name,self.root/name)
        (self.root/'_学习').mkdir()
        path=self.root/'复盘一致性哨兵.py'
        source=path.read_text(encoding='utf-8')
        source=source.replace("bc=os.path.join(L,'_bars_cache')", "raise RuntimeError('CONTROLLED STOP AT C3')\nbc=os.path.join(L,'_bars_cache')")
        path.write_text(source,encoding='utf-8')
        result=pub.run_consistency(self.root,self.stage,'20260902')
        self.assertEqual(result['status'],'fail')
        self.assertNotIn('C4',result['executed_rules'])
        self.assertIn('C1',result['executed_rules'])

    def test_limitup_adapter_executes_real_script_without_live_root(self):
        for name in ('limitup数据核对.py','module_render_limitup.py','_认知库渲染.py'):
            shutil.copy2(CODE/name,self.root/name)
        # Real page with deliberately absent private input sources: must execute
        # and report source errors, rather than a permanent unaudited/not_run.
        shutil.copy2(INTEGRATION/'复盘'/'盯盘台'/'limitup.html',self.stage/'limitup.html')
        self.assertIn("limitup",pub.SAFE_SENTINELS)
        r=pub._check_one(self.root,self.stage,'20260902','limitup')
        self.assertEqual(r['name'],'limitup')
        self.assertEqual(r['status'],'fail')
        self.assertTrue(r.get('observed_checks'),r)
        self.assertIn('温度表',r['log'])

    def test_consistency_executes_all_original_c_rules_against_stage(self):
        for name in ('复盘一致性哨兵.py','trading_calendar.py'):
            shutil.copy2(CODE/name,self.root/name)
        (self.root/'_学习').mkdir()
        self.assertTrue(hasattr(pub,"run_consistency"))
        r=pub.run_consistency(self.root,self.stage,'20260902')
        self.assertEqual(r['status'],'fail')
        self.assertIn('C1',str(r))
        self.assertIn('C11',str(r))
        self.assertEqual(r['executed_rules'],['C'+str(i) for i in range(1,12)])
        self.assertEqual(r['path_bindings']['SITE'],str(self.stage))

    def test_p1_hashed_kpis_are_recomputed_and_corruption_is_rejected(self):
        model=pub.read_json(P1_PREVIEW/'models'/'cycle.json')
        p1=pub.load_module(P1/'review_pages.py')
        p1._route_kpis(model,INTEGRATION)
        self.assertEqual(pub.validate_model_sources(INTEGRATION,'20260902',{'cycle':model}),[])
        model['kpis'][0]['value']='CONTROLLED unsupported KPI'
        self.assertTrue(pub.validate_model_sources(INTEGRATION,'20260902',{'cycle':model}))

    def test_p1_contract_and_declared_input_inventory(self):
        shutil.copy2(P1/'review_pages.py',self.root/'review_pages.py')
        (self.root/'_契约').mkdir()
        shutil.copy2(P1/'_契约'/'页面契约.v1.json',self.root/'_契约'/'页面契约.v1.json')
        names=pub.input_files(self.root,'20260902')
        for name in ('_契约/页面契约.v1.json','_学习/页面判断_20260902.json','_学习/总审_20260902.json','limitup数据核对.py','复盘一致性哨兵.py','module_render_logic.py','logic_pool.py','_学习/链条纵深库.json','_学习/竞价评分卡_20260902.html'):
            self.assertIn(name,names)

    def test_structured_input_does_not_require_legacy_bodies(self):
        # Copy a genuine P1 model's facts/claims, never invent an investment claim.
        m=pub.load_module(P1/'review_pages.py')
        models={r:json.loads((P1_PREVIEW/'models'/(r+'.json')).read_text(encoding='utf-8')) for r in pub.ROUTES}
        self.assertTrue(hasattr(pub,"validate_model_sources"))
        result=pub.validate_model_sources(INTEGRATION,'20260902',models)
        self.assertEqual(result,[],result)

    def test_browser_executes_chrome_and_catches_overflow(self):
        # Geometry-only test fixture; contains no simulated financial values.
        for r in pub.ROUTES:
            (self.stage/(r+'.html')).write_text('<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><body><div style="width:2000px">CONTROLLED OVERFLOW TEST</div><details><summary>toggle test</summary>body</details></body></html>',encoding='utf-8')
        self.assertTrue(hasattr(pub,"browser_check"))
        result=pub.browser_check(self.root,self.stage,'20260902')
        self.assertEqual(result['status'],'fail',result)
        self.assertTrue(result.get('browser_version'),result)
        self.assertTrue(any('overflow' in e for e in result['errors']),result)

    def test_browser_positive_uses_real_navigation_and_interaction(self):
        for route in pub.ROUTES:
            (self.stage/(route+'.html')).write_text('<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><body><h1>Geometry test</h1><details><summary>Open</summary>Readable fixture</details></body></html>',encoding='utf-8')
        result=pub.browser_check(self.root,self.stage,'20260902')
        self.assertEqual(result['status'],'pass',result)
        self.assertEqual(len(result['pages']),14)
        self.assertTrue(all(row['toggles']==1 for row in result['pages']))
        originals={row['screenshot']:row['sha256'] for row in result['pages']}
        for route in pub.ROUTES:
            page=self.stage/(route+'.html')
            page.write_text(page.read_text(encoding='utf-8').replace('Geometry test','SECOND CONTROLLED GEOMETRY RUN'),encoding='utf-8')
        second=pub.browser_check(self.root,self.stage,'20260902')
        self.assertEqual(second['status'],'pass',second)
        self.assertTrue(all(pub.digest(Path(path))==sha for path,sha in originals.items()),'later run overwrote earlier browser evidence')

    def test_actual_p1_report_normalizes_and_allows_audited_history_assets(self):
        # Replay the report format over actual saved P1 output (content unchanged).
        shutil.copytree(P1_PREVIEW,self.stage,dirs_exist_ok=True)
        report={'status':'ok','d':'20260902','errors':[],'pages':{r:str(self.stage/(r+'.html')) for r in pub.ROUTES},'page_status':{r:'ok' for r in pub.ROUTES}}
        (self.root/'_契约').mkdir()
        shutil.copy2(P1/'_契约'/'页面契约.v1.json',self.root/'_契约'/'页面契约.v1.json')
        self.assertTrue(hasattr(pub,'adapt_p1_report'))
        with patch.object(pub,'page_contract',return_value=pub.page_contract(self.root)):
            normalized=pub.adapt_p1_report(INTEGRATION,self.stage,report,'20260902')
        self.assertEqual(normalized['status'],'pass',normalized)
        self.assertTrue(normalized['auxiliary_assets'])
        errors=pub.validate_pages(self.stage,normalized,'20260902')
        self.assertFalse(any('P1 pages must be list' in e or 'template_version unsupported' in e or 'unreported HTML' in e or 'metadata missing' in e for e in errors), errors[:15])

    def test_structured_schema_with_real_claims_accepted_without_legacy_file(self):
        m=pub.load_module(P1/'review_pages.py')
        doc={'schema_version':1,'d':'20260902','evidence':[],'pages':{}}
        for route in pub.ROUTES:
            model=json.loads((P1_PREVIEW/'models'/(route+'.json')).read_text(encoding='utf-8'))
            # Convert genuine imported source claims to the public new-schema shape.
            selected=[]
            for section in model['sections']:
                claims=[c for c in model['claims'] if c['id'] in section['claim_refs']]
                chosen=next((c for c in claims if c['role']=='cognition'),claims[0])
                selected.append(chosen)
            evidence=[];claims=[]
            for c in selected:
                src=c['source'];pointer=c['source_pointer']
                if pointer.startswith('/bodies/'):
                    pointer='/'.join(pointer.split('/')[:3])
                ref=route+'-'+c['id']
                evidence.append({'id':ref,'d':'20260902','source':src,'pointer':pointer,'quality':'source'})
                claims.append({k:c[k] for k in ('id','role','text','section')})
                claims[-1]['evidence_refs']=[ref]
            doc['evidence']+=evidence
            doc['pages'][route]={'hero':{'claim_ref':claims[0]['id']},'kpis':[{'id':k,'label':k,'value':None,'evidence_refs':[]} for k in ['zt','temp','high','volume']], 'claims':claims,'sections':[{'id':c['section'],'claim_refs':[c['id']]} for c in claims],'limitations':[]}
        (self.root/'_学习').mkdir()
        (self.root/'_契约').mkdir()
        shutil.copy2(P1/'_契约'/'页面契约.v1.json',self.root/'_契约'/'页面契约.v1.json')
        # Reference actual source JSON; legacy judgment renamed to an evidence-only
        # file so new input validation cannot accidentally fall back to bodies.
        for e in doc['evidence']:
            source=e['source']
            newname='evidence-'+source
            shutil.copy2(INTEGRATION/'_学习'/source,self.root/'_学习'/newname)
            e['source']=newname
        (self.root/'_学习'/'页面判断_20260902.json').write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
        errors=pub.validate_inputs(self.root,'20260902')
        self.assertEqual(errors,[],errors)
        doc['pages']['cycle']['bogus_field']='CONTROLLED UNKNOWN FIELD'
        (self.root/'_学习'/'页面判断_20260902.json').write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
        self.assertTrue(pub.validate_inputs(self.root,'20260902'))

    def test_logic_check_verifies_actual_saved_p1_dom_and_rejects_missing_claim(self):
        shutil.copytree(P1_PREVIEW,self.stage,dirs_exist_ok=True)
        self.assertTrue(hasattr(pub,'view_check'))
        with patch.object(pub,'page_contract',return_value=pub.page_contract(P1)):
            good=pub.view_check(INTEGRATION,self.stage,'20260902','logic')
            self.assertEqual(good['status'],'pass',good)
            page=self.stage/'logic.html'
            model=json.loads((self.stage/'models'/'logic.json').read_text(encoding='utf-8'))
            ident='claim-'+model['claims'][-1]['id']
            page.write_text(page.read_text(encoding='utf-8').replace('id="'+ident+'"','id="CONTROLLED_DELETED_ID"'),encoding='utf-8')
            bad=pub.view_check(INTEGRATION,self.stage,'20260902','logic')
        self.assertEqual(bad['status'],'fail')
        self.assertIn('claim',str(bad['errors']))

if __name__=='__main__':unittest.main(verbosity=2)
