"""Legacy command must delegate to the hard release gate, not write first."""
import importlib.util
from pathlib import Path
import sys
import types
import pytest

ROOT=Path(__file__).resolve().parents[1]

def load(monkeypatch,tmp_path,result):
    spec=importlib.util.spec_from_file_location('tested_legacy_entry',ROOT/'生成盯盘台.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.BASE=str(tmp_path);module.SITE=str(tmp_path/'复盘'/'盯盘台');module.ARC=str(tmp_path/'复盘'/'盯盘台'/'archive');module.L=str(tmp_path/'_学习')
    calls=[]
    def build_release(root,d,**kwargs):
        calls.append((root,d,kwargs));return result
    monkeypatch.setitem(sys.modules,'review_publish',types.SimpleNamespace(build_release=build_release))
    return module,calls

def test_failed_build_never_creates_live_tree(monkeypatch,tmp_path):
    mod,calls=load(monkeypatch,tmp_path,{'status':'fail','errors':['missing_cycle']})
    try:mod.build('20260904')
    except Exception:pass
    assert not (tmp_path/'复盘'/'盯盘台').exists(),'entrypoint wrote live directory before gate'
    assert len(calls)==1,'entrypoint did not invoke release gate'

def test_failed_gate_propagates_error(monkeypatch,tmp_path):
    mod,calls=load(monkeypatch,tmp_path,{'status':'fail','errors':['missing_cycle']})
    with pytest.raises(RuntimeError,match='missing_cycle'):mod.build('20260904')

def test_pass_delegates_explicit_publish(monkeypatch,tmp_path):
    mod,calls=load(monkeypatch,tmp_path,{'status':'pass','d':'20260904','build_id':'fixture-release'})
    result=mod.build('20260904')
    assert result['status']=='pass'
    assert calls==[(tmp_path,'20260904',{'publish':True})]
