"""Build-discovered regressions on current P1.2, plus future/missing source negatives."""
import json
import re
from pathlib import Path
import pytest
import review_pages as pages
import review_publish as pub
ROOT=Path(__file__).resolve().parents[1]

def test_freeze_contains_dated_seat_snapshot():
 assert '_学习/_席位分档快照.jsonl' in pub.input_files(ROOT,'20260902')

@pytest.mark.parametrize('route',['cycle','lhb'])
def test_current_kpi_source_contract(route):
 m=pages.build_page_model(ROOT,'20260902',route)
 assert pub.validate_model_sources(ROOT,'20260902',{route:m})==[]
 m['kpis'][0]['value']='TEST_FORGED_VALUE'
 assert pub.validate_model_sources(ROOT,'20260902',{route:m})

def test_cycle_missing_judgment_remains_honest(tmp_path, monkeypatch):
 m=pages.build_page_model(ROOT,'20260904','cycle')
 assert m['judgment_complete'] is False
 assert m['hero']['text'] == '当日判断缺失'
 # Same-day vote and absent cycle prose are independent facts.
 rows=[json.loads(line) for line in (ROOT/'_学习/_周期投票台账.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
 vote=next(row for row in rows if row.get('d')=='20260904')
 assert m['kpis'][1]['value'] == vote['主判']['stage']
 (tmp_path/'models').mkdir()
 (tmp_path/'models/cycle.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
 (tmp_path/'cycle.html').write_text(pages._render(m,pages._contract()),encoding='utf-8')
 result=pub._check_one(ROOT,tmp_path,'20260904','cycle')
 assert result['status']=='pass',result['errors']
 original=pub.read_json
 # TEST ONLY: a newly present decision must invalidate a missing-decision waiver.
 def with_decision(path,*args,**kwargs):
  if Path(path).name=='judgment_20260904.json':return {'bodies':{'cycle':'TEST_ONLY_DECISION_PRESENT'}}
  return original(path,*args,**kwargs)
 monkeypatch.setattr(pub,'read_json',with_decision)
 assert pub._check_one(ROOT,tmp_path,'20260904','cycle')['status']=='fail'

def test_cycle_body_day_omits_machine_components_and_anchors(tmp_path):
 # Use the real dated judgment and data, then render through the production
 # P1 builder.  Body days must keep the golden seven-section shape; machine
 # cards belong only to the missing-body fallback track.
 model=pages.build_page_model(ROOT,'20260907','cycle')
 assert model['judgment_complete'] is True
 assert {c['id'] for c in model.get('components',[])}.isdisjoint({'VOLSTEP','LEADIND','VOTEBOARD','LADDER'})
 html=pages._render(model,pages._contract())
 for anchor in ('VOLSTEP','LEADIND','MACHVOTE','LADDER'):
  assert '<!--'+anchor+'-->' not in html
 assert not re.search(r'<details[^>]*class="chain"[^>]*>\s*<summary>\s*<b>机器数据源',html)
 (tmp_path/'models').mkdir()
 (tmp_path/'models/cycle.json').write_text(json.dumps(model,ensure_ascii=False),encoding='utf-8')
 (tmp_path/'cycle.html').write_text(html,encoding='utf-8')
 result=pub.scoped_p12_check(ROOT,tmp_path,'20260907','cycle')
 assert result['status']=='pass',result


def test_renderer_rejects_future_or_absent_snapshot(tmp_path):
 (tmp_path/'_学习').mkdir()
 original=pub.seat_snapshot(ROOT,'20260902')
 for row in [dict(original,窗口='20260401~20260903'),None]:
  path=tmp_path/'_学习/_席位分档快照.jsonl'
  path.write_text(json.dumps(row,ensure_ascii=False) if row else '',encoding='utf-8')
  calls=[]
  pages._seat_library({'d':'20260902'},tmp_path,lambda *args,**kw:calls.append((args,kw)))
  assert calls[0][0][4] is None
