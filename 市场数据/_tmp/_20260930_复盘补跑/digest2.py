import glob, json, os, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import review_publish as RP
sa = Path(sorted(glob.glob('.review_staging/20260929-*'), key=os.path.getmtime)[-1]).resolve()
stage, frozen = sa / 'site', sa / 'inputs'
print('stage', stage, 'frozen', frozen)
d = '20260929'
out = []
try:
    c = RP.run_consistency(frozen, stage, d)
    out.append('=== consistency status=%s exit=%s executed=%s' % (c['status'], c['exit_code'], c.get('executed_rules')))
    for e in c['errors']:
        out.append('  ERR ' + str(e)[:600])
    out.append('  --- log 尾部 40 行 ---')
    out += ['  | ' + l for l in c.get('log', '').splitlines()[-40:]]
except Exception:
    out.append('run_consistency EXC\n' + traceback.format_exc())
try:
    fz = dict(frozen=frozen, stage=stage)
    l = RP._check_one(Path(frozen), Path(stage), d, 'lhb')
    out.append('=== lhb check status=%s exit=%s' % (l.get('status'), l.get('exit_code')))
    for e in (l.get('errors') or []):
        out.append('  ERR ' + str(e)[:600])
    out.append('  --- lhb log FAIL/✗ 行 ---')
    out += ['  | ' + x for x in l.get('log', '').splitlines() if ('FAIL' in x or '✗' in x)][:40]
except Exception:
    out.append('_check_one EXC\n' + traceback.format_exc())
Path('_tmp/_20260930_复盘补跑/digest2.txt').write_text('\n'.join(out), encoding='utf-8')
print('WROTE', len(out), 'lines')
