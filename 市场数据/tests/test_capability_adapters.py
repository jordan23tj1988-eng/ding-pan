# -*- coding: utf-8 -*-
import importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    p = ROOT / name
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_capabilities_fail_closed_without_real_intraday_data(tmp_path):
    for name, key in [('竞价撤单差分.py','auction_cancel_diff'), ('开盘验证维.py','open_verification'),
                      ('日内温度曲线.py','intraday_temperature_curve'), ('日内轮动图谱.py','intraday_rotation_graph')]:
        r = load(name).build(tmp_path, '20260908')
        assert r['status'] == 'unavailable'
        assert r['capability'] == key

def test_capabilities_accept_dated_two_point_fixture(tmp_path):
    learn = tmp_path / '_学习'; learn.mkdir()
    (learn / '题材归位_20260907.json').write_text(json.dumps({'映射': {
        '000001': {'大方向': 'A'}, '000002': {'大方向': 'B'}}}, ensure_ascii=False), encoding='utf-8')
    d = tmp_path / '盘中' / '20260907'; d.mkdir(parents=True)
    rows = [
        {'ts':'2026-09-07T09:30:00+08:00','phase':'continuous','rows':[{'code':'000001','pct':1.0},{'code':'000002','pct':-1.0}]},
        {'ts':'2026-09-07T09:34:00+08:00','phase':'continuous','rows':[{'code':'000001','pct':2.0},{'code':'000002','pct':-2.0}]},
    ]
    (d/'realtime_ticks.jsonl').write_text('\n'.join(json.dumps(x) for x in rows)+'\n', encoding='utf-8')
    a = load('开盘验证维.py').build(tmp_path, '20260907')
    t = load('日内温度曲线.py').build(tmp_path, '20260907')
    g = load('日内轮动图谱.py').build(tmp_path, '20260907')
    assert a['status'] == 'pass' and a['metrics']['verified_codes'] == 2
    assert t['status'] == 'pass' and t['metrics']['time_points'] == 2
    assert g['status'] == 'pass' and g['metrics']['themes'] == 2

def test_auction_requires_pre_and_post_920_points(tmp_path):
    d = tmp_path / '盘中' / '20260907'; d.mkdir(parents=True)
    p = d/'auction_traj.jsonl'
    p.write_text('\n'.join([
        json.dumps({'ts':'2026-09-07T09:19:00+08:00','rows':[{'code':'000001','pct':5.0}]}),
        json.dumps({'ts':'2026-09-07T09:20:01+08:00','rows':[{'code':'000001','pct':3.0}]})
    ])+'\n', encoding='utf-8')
    r = load('竞价撤单差分.py').build(tmp_path, '20260907')
    assert r['status'] == 'pass' and r['metrics']['codes_with_pre_post'] == 1

def test_theme_relocation_only_validates_existing_source(tmp_path):
    m = load('题材归位.py')
    assert m.build(tmp_path, '20260907')['status'] == 'unavailable'
    learn = tmp_path/'_学习'; learn.mkdir()
    (learn/'题材归位_20260907.json').write_text(json.dumps({'映射': {'000001': {'大方向':'A'}}}), encoding='utf-8')
    assert m.build(tmp_path, '20260907')['status'] == 'pass'
