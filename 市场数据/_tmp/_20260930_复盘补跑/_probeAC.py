import json, os, subprocess, glob
from pathlib import Path
sa = Path(sorted(glob.glob('.review_staging/20260929-*'), key=os.path.getmtime)[-1]).resolve()
stage, root = sa / 'site', sa / 'inputs'
out = []
for route in ('lhb', 'theme', 'consistency'):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               REVIEW_STAGE=str(stage), LHB_SITE_ROOT=str(stage))
    r = subprocess.run([r'D:\股票数据\.venv312\Scripts\python.exe', '-B', 'review_publish.py', '_check', '20260929',
                        '--root', str(root), '--stage', str(stage), '--route', route],
                       cwd=str(root), env=env, capture_output=True, text=True, encoding='utf-8', timeout=900)
    try:
        row = json.loads(r.stdout)
    except Exception as e:
        out.append('===== %s rc=%s PARSE-FAIL %s' % (route, r.returncode, (r.stdout or '')[:300])); continue
    out.append('===== %s rc=%s status=%s' % (route, r.returncode, row.get('status')))
    for e in (row.get('errors') or []):
        out.append('   ERR ' + str(e)[:220])
    for c in row.get('observed_checks', []):
        if not c.get('ok') and not c.get('negative_injection'):
            out.append('   FAIL %s | %s | %s' % (c.get('label'), str(c.get('detail'))[:200], json.dumps(c.get('errors'), ensure_ascii=False)[:500]))
Path('_学习/_check_digest_20260929.txt').write_text('\n'.join(out), encoding='utf-8')
print('wrote', sum(1 for l in out), 'lines')
