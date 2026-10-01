import json, os, subprocess, sys, glob
from pathlib import Path
stage = Path(sorted(glob.glob('.review_staging/20260929-*'), key=os.path.getmtime)[-1]).resolve()
print('stage', stage, 'inputs?', (stage / 'inputs').is_dir(), 'site?', (stage / 'site').is_dir())
root = stage / 'inputs'
for route in ('lhb', 'theme'):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               REVIEW_STAGE=str(stage), LHB_SITE_ROOT=str(stage / 'site'))
    r = subprocess.run([r'D:\股票数据\.venv312\Scripts\python.exe', '-B', 'review_publish.py', '_check', '20260929',
                        '--root', str(root), '--stage', str(stage), '--route', route],
                       cwd=str(root), env=env, capture_output=True, text=True, encoding='utf-8', timeout=600)
    print('=====', route, 'rc', r.returncode)
    try:
        row = json.loads(r.stdout)
    except Exception as e:
        print('stdout parse fail', e, r.stdout[:500], r.stderr[:500]); continue
    print('status', row.get('status'), 'errors', json.dumps(row.get('errors'), ensure_ascii=False)[:1500])
    for c in row.get('observed_checks', []):
        if not c.get('ok') and not c.get('negative_injection'):
            print('  FAIL', c.get('label'), '|', str(c.get('detail'))[:200], '|', json.dumps(c.get('errors'), ensure_ascii=False)[:400])
    bad = [l for l in (row.get('log') or '').splitlines() if 'FAIL' in l or '✗' in l]
    print('  log FAIL lines:', bad[:12])
