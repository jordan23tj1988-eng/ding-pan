# -*- coding: utf-8 -*-
import importlib.util,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,BASE/(n+'.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_stability_blocks_under_five(tmp_path):
 m=load('stability_gate'); (tmp_path/'releases'/'20260907-x').mkdir(parents=True); (tmp_path/'releases'/'20260907-x'/'manifest.json').write_text('{"status":"pass"}',encoding='utf-8'); r=m.evaluate(tmp_path,5); assert r['status']=='blocked'

def test_history_policy_blocks_explicit_evidence(tmp_path):
 m=load('history_recovery_gate'); d=tmp_path/'d.md'; p=tmp_path/'p.md'; d.write_text('20260902 BLOCKED damaged\n20260904 缺失\n',encoding='utf-8'); p.write_text('',encoding='utf-8'); r=m.evaluate(d,p); assert r['status']=='blocked'
