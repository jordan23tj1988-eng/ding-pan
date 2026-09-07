"""TEST ONLY timestamp fixture: C3 stays blocked, without unsafe replay advice."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]

def test_mtime_does_not_prescribe_latest_state_replay(tmp_path):
    l=tmp_path/'_学习';cache=l/'_bars_cache';cache.mkdir(parents=True)
    f=cache/'000001.csv';f.write_text('TEST_ONLY',encoding='utf-8');os.utime(f,(2000000,2000000))
    kb=l/'_模拟盘/auction/看板_20260902.html';kb.parent.mkdir(parents=True);kb.write_text('TEST_ONLY',encoding='utf-8');os.utime(kb,(1999800,1999800))
    source=(ROOT/'复盘一致性哨兵.py').read_text(encoding='utf-8')
    a=source.index('# ---------- C3');b=source.index('# ---------- C4',a)
    scope={'L':str(l),'PAGE':{'auction':'auction'},'d':'20260902','os':os,'FAIL':[]}
    exec(compile(source[a:b],str(ROOT/'复盘一致性哨兵.py'),'exec'),scope)
    assert len(scope['FAIL'])==1
    assert '证据不足' in scope['FAIL'][0]
    assert 'dashboard 20260902' not in scope['FAIL'][0]
