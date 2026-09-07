"""Synthetic TEST ONLY fixtures; execute the real triggers/card function bodies."""
from pathlib import Path
import ast,json,os,copy
import pytest
SOURCE=Path(__file__).resolve().parents[1]/'情绪先行指标.py'
D='20260904'

def render(tmp_path,temps,rows):
    (tmp_path/'_市场温度表.json').write_text(json.dumps(temps,ensure_ascii=False),encoding='utf-8')
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
    tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['triggers','card']]
    env={'os':os,'json':json,'L':str(tmp_path)}
    exec(compile(tree,str(SOURCE),'exec'),env)
    before=copy.deepcopy(rows)
    env['card'](D,rows)
    assert rows==before
    strip=tmp_path/f'先行指标灯_{D}.html'
    return strip.read_text(encoding='utf-8') if strip.exists() else None

def row(prem=None,cached=None):
    return {'晋级':{'涨停数_净':1,'一进二率':0.1},'昨日涨停溢价':{'执行均收':prem},'触发器':cached or []}

def test_missing_metrics_are_unknown_not_off_or_null(tmp_path):
    html=render(tmp_path,{}, {D:row()})
    assert 'null' not in html and 'None' not in html
    assert '冰点进攻窗·—' in html and '过热禁追窗·—' in html and '洗出反弹窗·—' in html
    assert '温度 —' in html and '昨停溢价 —' in html

def test_fresh_frozen_metrics_override_stale_empty_trigger_cache(tmp_path):
    html=render(tmp_path,{D:{'温度':10,'温度档':'TEST'}},{D:row()})
    assert '冰点进攻窗·触发' in html
    assert '温度 10.0·TEST' in html

def test_known_non_trigger_is_still_off(tmp_path):
    rows={d:row(1) for d in ['20260902','20260903',D]}
    html=render(tmp_path,{D:{'温度':50,'温度档':'TEST'}},rows)
    assert '冰点进攻窗·灭' in html and '过热禁追窗·灭' in html and '洗出反弹窗·灭' in html

def test_future_metrics_cannot_complete_today_window(tmp_path):
    rows={D:row(-1,cached=['TEST过热禁追窗']), '20260907':row(-1),'20260908':row(-1)}
    html=render(tmp_path,{'20260907':{'温度':99,'温度档':'FUTURE_TEST'}},rows)
    assert 'FUTURE_TEST' not in html and '·触发' not in html
    assert '过热禁追窗·—' in html and '洗出反弹窗·—' in html

def test_missing_today_does_not_render_prior_day_as_today(tmp_path):
    assert render(tmp_path,{}, {'20260903':row()}) is None
