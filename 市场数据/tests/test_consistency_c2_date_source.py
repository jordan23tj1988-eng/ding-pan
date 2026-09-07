"""TEST ONLY synthetic fixtures; run the original C2 block, never an engine."""
from pathlib import Path
import json,os,re
ROOT=Path(__file__).resolve().parents[1]
D='20260902'
ROUTES=('limitup','auction','lhb','theme','logic','master')

def setup_root(tmp_path):
    l=tmp_path/'_学习'; s=l/'_模拟盘';s.mkdir(parents=True)
    pages=tmp_path/'复盘/盯盘台';pages.mkdir(parents=True)
    for route in ROUTES:
        folder=s/route;folder.mkdir()
        pg='index' if route=='master' else route
        (pages/(pg+'.html')).write_text('<div>PAPER TRADING 累计 +1.00%</div>',encoding='utf-8')
        (folder/'净值.json').write_text(json.dumps({D:{'nav':1.01,'cash':101,'mv':0,'n':0},'20260904':{'nav':1.09,'cash':109,'mv':0,'n':0}}),encoding='utf-8')
        (folder/'状态.json').write_text(json.dumps({'date':'20260904','累计pct':9}),encoding='utf-8')
    return l,s,pages

def run_c2(root):
    text=(ROOT/'复盘一致性哨兵.py').read_text(encoding='utf-8')
    a=text.index('# ---------- C2');b=text.index('# ---------- C3',a)
    scope={'R':str(root),'L':str(root/'_学习'),'d':D,'SITE':str(root/'复盘/盯盘台'),'FAIL':[],'WARN':[], 'os':os,'re':re,'json':json}
    exec(compile(text[a:b],str(ROOT/'复盘一致性哨兵.py'),'exec'),scope)
    return scope['FAIL'],scope['WARN']

def test_target_date_nav_not_latest_state(tmp_path):
    setup_root(tmp_path)
    fail,warn=run_c2(tmp_path)
    assert fail==[],fail
    assert warn==[],warn


import pytest
@pytest.mark.parametrize('raw',[
    '{"20260902":{"nav":true}}', '{"20260902":{"nav":null}}', '{"20260902":{"nav":"1.0"}}',
    '{"20260902":{"nav":NaN}}', '{"20260902":{"nav":Infinity}}',
    '{"20260902":{"nav":99},"20260902":{"nav":1}}',
])
def test_ambiguous_or_nonnumeric_nav_fails_closed(tmp_path,raw):
    _,sim,pages=setup_root(tmp_path)
    (sim/'auction/净值.json').write_text(raw,encoding='utf-8')
    (pages/'auction.html').write_text('PAPER TRADING 累计 +0.00%',encoding='utf-8')
    fail,_=run_c2(tmp_path)
    assert any(x.startswith('C2 auction 目标日来源不可核验:') for x in fail),fail


def test_same_day_state_cannot_contradict_nav(tmp_path):
    _,sim,_=setup_root(tmp_path)
    (sim/'auction/状态.json').write_text(json.dumps({'date':D,'累计pct':9}),encoding='utf-8')
    fail,_=run_c2(tmp_path)
    assert any('同日' in x and '不一致' in x for x in fail),fail


@pytest.mark.parametrize('state_date,ok',[(D,True),('20260904',False),('2026-09-02',False)])
def test_state_fallback_requires_exact_date(tmp_path,state_date,ok):
    _,sim,_=setup_root(tmp_path)
    (sim/'auction/净值.json').unlink()
    (sim/'auction/状态.json').write_text(json.dumps({'date':state_date,'累计pct':1}),encoding='utf-8')
    fail,_=run_c2(tmp_path)
    assert (not fail)==ok,fail


def test_existing_nav_without_target_does_not_fall_back(tmp_path):
    _,sim,_=setup_root(tmp_path)
    (sim/'auction/净值.json').write_text(json.dumps({'20260904':1.09}),encoding='utf-8')
    (sim/'auction/状态.json').write_text(json.dumps({'date':D,'累计pct':1}),encoding='utf-8')
    fail,_=run_c2(tmp_path)
    assert any('净值缺目标日' in x for x in fail),fail


def test_corrupt_nav_is_not_decoded_with_ignore(tmp_path):
    _,sim,_=setup_root(tmp_path)
    (sim/'auction/净值.json').write_bytes(b'{"20260902":1.01}\xff')
    fail,_=run_c2(tmp_path)
    assert any(x.startswith('C2 auction 目标日来源不可核验:') for x in fail),fail


def test_changed_display_is_rejected(tmp_path):
    _,_,pages=setup_root(tmp_path)
    (pages/'auction.html').write_text('PAPER TRADING 累计 +1.02%',encoding='utf-8')
    fail,_=run_c2(tmp_path)
    assert any(x.startswith('C2 auction 页面累计') for x in fail),fail



