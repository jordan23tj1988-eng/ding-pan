# -*- coding: utf-8 -*-
"""坑19 SOP: bench删脏重算 + 六路旁路重mark净值 + write_status(全用引擎函数,agent不设新口径)"""
import json,os,sys,time,importlib.util
spec=importlib.util.spec_from_file_location('eng','模拟盘引擎.py'); m=importlib.util.module_from_spec(spec)
sys.argv=['模拟盘引擎.py','dashboard','20260716']  # 防止main触发
try: spec.loader.exec_module(m)
except SystemExit: pass
m.ROOT=m.find_root() or os.getcwd()
d='20260716'; cal=m.calendar()
# 1) bench删脏重算
bp=os.path.join(m.simdir(),'基准净值.json')
bn=m.jload(bp,{})
old=bn.pop(d,None); m.jsave(bp,bn)
print('删脏bench:',old)
m.settle_bench(d,cal,time.time()+35)
# 2) 六路重mark(用引擎load_bars的close)
for route in m.ROUTES:
    st=m.load_state(route)
    mv=0.0; ok=True
    for p in st['positions']:
        b=m.load_bars(p['code']); bar=b.get(d)
        if not bar or bar[3] is None: ok=False; print(route,p['code'],'缺bar!'); continue
        mv+=p['shares']*bar[3]
    navp=os.path.join(m.simdir(route),'净值.json')
    nv=m.jload(navp,{})
    if d in nv and ok:
        nav_new=round((st['cash']+mv)/1e6,6)
        if abs(nav_new-nv[d]['nav'])>1e-6:
            print(route,'重mark',nv[d]['nav'],'->',nav_new)
            nv[d]['nav']=nav_new; nv[d]['mv']=round(mv,0); m.jsave(navp,nv)
            m.write_status(route,d,st,nv)
        else: print(route,'一致',nav_new)
