# -*- coding: utf-8 -*-
import sqlite3,time,subprocess,json,os,sys
DB=r'C:/Users/66353/AppData/Local/hermes/profiles/a/cron/executions.db'
PY=r'D:/股票数据/.venv312/Scripts/python.exe'
ROOT=r'D:/股票数据/市场数据'
RUN='2b77d6fa67a5465ebdaacd633d6c4755'
t0=time.time()
while time.time()-t0 < 4*3600:
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    r=c.execute('select status,started_at,finished_at,progress_at,substr(coalesce(error,""),1,400) e from executions where id=?',(RUN,)).fetchone()
    c.close()
    st=r['status'] if r else 'missing'
    print(time.strftime('%H:%M:%S'),st,r['progress_at'] if r else '',flush=True)
    if st!='running': break
    time.sleep(60)
print('=== JOB_END',json.dumps(dict(r),ensure_ascii=False),flush=True)
env=dict(os.environ); env.pop('PYTHONPATH',None)
p=subprocess.run([PY,'复盘一致性哨兵.py','20261020'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
out=(p.stdout or '')+(p.stderr or '')
print('=== SENTINEL rc=%s'%p.returncode,flush=True)
print(out[-4000:],flush=True)
open(os.path.join(ROOT,'_tmp','wait_review_20261020.result.txt'),'w',encoding='utf-8').write(out)
# 显示页/CURRENT状态
for f in ['CURRENT.json']:
    print(f,open(os.path.join(ROOT,f),encoding='utf-8').read(),flush=True)
