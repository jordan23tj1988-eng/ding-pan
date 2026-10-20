# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, r"D:\股票数据\市场数据")
os.environ.pop("PYTHONPATH", None)
from pathlib import Path
import review_publish as RP
res = RP.build_release(Path(r"D:\股票数据\市场数据"), "20261019")
out = {k: v for k, v in res.items() if k in ("status", "d", "build_id", "errors", "publish", "pages", "checks")}
print(json.dumps(out, ensure_ascii=False, default=str)[:4000])
