import sys,pathlib,json
root=pathlib.Path(r'D:\股票数据\市场数据'); sys.path.insert(0,str(root)); import importlib.util
sp=importlib.util.spec_from_file_location('e',root/'情绪先行指标.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
ths=m.load_ths(root); out=m.load_out(root); row={}; row.update(m.promo('20260911','20260910',ths)); row.update(m.nuke('20260911','20260910')); out['20260911']=row
(root/'_学习'/'_情绪先行指标.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
try: m.card('20260911',root)
except Exception as e: print('card',e)
print(row)
