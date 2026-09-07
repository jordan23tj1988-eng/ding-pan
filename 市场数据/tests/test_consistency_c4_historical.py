"""C4 historical coverage regression; all CSV payloads below are synthetic TEST ONLY."""
from pathlib import Path
import glob
import json
import os
import pytest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'复盘一致性哨兵.py'

def run_c4(tmp_path, rows, invalid_bytes=False):
    day='20260902'; learning=tmp_path/'_学习'; bars=learning/'_bars_cache'
    bars.mkdir(parents=True); (tmp_path/day).mkdir()
    codes=['000001','000002','000003','000004']
    (tmp_path/day/'zt_pool.csv').write_text('代码\n'+'\n'.join(codes),encoding='utf-8')
    for code in codes:
        data='date,close\n'+'\n'.join(x+',1' for x in rows)+'\n'
        (bars/(code+'.csv')).write_bytes(data.encode()+ (b'\xff' if invalid_bytes else b''))
    text=SOURCE.read_text(encoding='utf-8')
    block=text.split('# ---------- C4 关键股当日bar覆盖 ----------',1)[1].split('# ---------- C5',1)[0]
    env=dict(os=os,glob=glob,json=json,R=str(tmp_path),L=str(learning),bc=str(bars),d=day,_EXPECT_D=day,PAGE={},FAIL=[],WARN=[])
    exec(compile(block,str(SOURCE), 'exec'),env)
    return env['FAIL'],env['WARN']

def test_historical_date_can_precede_latest_row(tmp_path):
    assert run_c4(tmp_path,['2026-09-02','2026-09-04']) == ([],[])

def test_future_row_cannot_replace_absent_target(tmp_path):
    fail,warn=run_c4(tmp_path,['2026-09-01','2026-09-04'])
    assert fail and 'C4' in fail[0]

def test_malformed_csv_is_not_silently_decoded(tmp_path):
    fail,warn=run_c4(tmp_path,['2026-09-02'],invalid_bytes=True)
    assert fail and 'C4' in fail[0]

def test_ambiguous_duplicate_target_is_rejected(tmp_path):
    fail,warn=run_c4(tmp_path,['2026-09-02','2026-09-02'])
    assert fail and 'C4' in fail[0]
