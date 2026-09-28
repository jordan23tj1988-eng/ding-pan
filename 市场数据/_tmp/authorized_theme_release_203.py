from __future__ import annotations
import importlib.util, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = '20260923'
SITE = ROOT / '复盘' / '盯盘台'
freeze = SITE / '.theme_page_freeze.json'
bak_freeze = ROOT / '_学习' / f'主题页冻结_{D}_#203_变更前.json'
bak_page = ROOT / '_学习' / f'主题页_{D}_#203_覆盖前.html'

if not freeze.is_file():
    raise SystemExit('freeze metadata missing; refuse override')
bak_freeze.parent.mkdir(exist_ok=True)
if not bak_freeze.exists():
    shutil.copy2(freeze, bak_freeze)
# 现站页面本体备份(只在首次覆盖前留一份)
if not bak_page.exists() and (SITE / 'theme.html').is_file():
    shutil.copy2(SITE / 'theme.html', bak_page)
old = freeze.read_bytes()
os.unlink(freeze)
restored = False
try:
    sys.path.insert(0, str(ROOT))
    import review_publish
    result = review_publish.build_release(ROOT, D, publish=True, allow_degraded=False)
    print('release:', json.dumps({k: result.get(k) for k in ('status', 'build_id', 'release_dir', 'errors')},
                                ensure_ascii=False, default=str))
    if result.get('status') != 'pass':
        raise RuntimeError('release gate failed')
    spec = importlib.util.spec_from_file_location('generator_203', ROOT / '生成盯盘台.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._deploy_site(D, result)
    print('deploy: ok')
except Exception:
    if not freeze.exists():
        freeze.write_bytes(old)
        restored = True
    raise
finally:
    if restored:
        print('freeze: restored after failed override')

print('backup page:', bak_page, bak_page.exists())
print('live theme:', SITE / 'theme.html')
print('freeze:', json.loads(freeze.read_text(encoding='utf-8')))
