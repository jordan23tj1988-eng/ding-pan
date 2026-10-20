# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, r"D:\股票数据\市场数据")
os.environ.pop("PYTHONPATH", None)
from pathlib import Path
import review_pages as P
root = Path(r"D:\股票数据\市场数据")
c = P._contract(root)
print("routes", c["routes"])
for r in c["routes"]:
    try:
        m = P.build_page_model(root, "20261019", r)
        print("##", r, "status=", m.get("status"), "complete=", m.get("complete"), "errors=", m.get("errors"))
    except Exception as e:
        print("##", r, "EXC", type(e).__name__, e)
