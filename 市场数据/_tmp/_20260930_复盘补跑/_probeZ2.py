import json, os, subprocess, glob
from pathlib import Path
sa = Path(sorted(glob.glob('.review_staging/20260929-*'), key=os.path.getmtime)[-1]).resolve()
stage = sa / 'site'
root = sa / 'inputs'
print('stage', stage)
for route in ('lhb', 'theme', 'consistency'):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               REVIEW_STAGE=str(stage), LHB_SITE_ROOT=str(stage))
    r = subprocess.run([r'D:\股票数据\.venv312\Scripts\python.exe', '-B', 'review_publish.py', '_check', '20260929',
                        '--root', str(root), '--stage', str(stage), '--route', route],
                       cwd=str(root), env=env, capture_output=True, text=True, encoding='utf-8', timeout=600)
    print('=====', route, 'rc', r.returncode)
    try:
        row = json.loads(r.stdout)
    except Exception as e:
        print('parse fail', e, r.stdout[:300], r.stderr[:600]); continue
    print('status', row.get('status'), '| errors', json.dumps(row.get('errors'), ensure_ascii=False)[:1200])
    for c in row.get('observed_checks', []):
        if not c.get('ok') and not c.get('negative_injection'):
            print('  FAIL', c.get('label'), '|', str(c.get('detail'))[:180], '|', json.dumps(c.get('errors'), ensure_ascii=False)[:300])
