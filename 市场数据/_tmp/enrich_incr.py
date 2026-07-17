# -*- coding: utf-8 -*-
"""增量enrich: 老_S_stage.pkl保留(日<20260709), 近期行(>=20260709)+今日用模块_enrich重算"""
import importlib.util,sys
import pandas as pd
spec=importlib.util.spec_from_file_location('qt','涨停质量训练.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
L='_学习'; CUT='20260709'
P=pd.read_pickle(L+'/_P_stage.pkl')
S_old=pd.read_pickle(L+'/_S_stage.pkl')
keep=S_old[S_old['日']<CUT].copy()
recent=P[P['日']>=CUT].copy().reset_index(drop=True)
D=m._enrich(recent,forward=True)
S=pd.concat([keep,D],ignore_index=True)
S.to_pickle(L+'/_S_stage.pkl')
print('ENRICH_OK',len(S),'重算行',len(D),'E1非空(0715)',int(D[D['日']=='20260715']['E1'].notna().sum()))
