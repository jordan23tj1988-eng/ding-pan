from pathlib import Path
import json
import sys
ROOT = Path(r'D:/股票数据/市场数据')
sys.path.insert(0, str(ROOT))
import review_publish
import 生成盯盘台 as dashboard

root = Path(r'D:/股票数据/市场数据')
date = '20260922'
print('P2/P3 already passed in latest wrapper log; retrying publish gate only.')
result = review_publish.build_release(root, date, publish=True)
print('BUILD_RELEASE_STATUS', result.get('status'))
print('BUILD_RELEASE_ERRORS', json.dumps(result.get('errors', []), ensure_ascii=False))
if result.get('status') != 'pass':
    raise SystemExit(2)
dashboard._deploy_site(date, result)
print('DEPLOY_DONE')
print(json.dumps({k: result.get(k) for k in ('status','build_id','published','release_dir')}, ensure_ascii=False))
