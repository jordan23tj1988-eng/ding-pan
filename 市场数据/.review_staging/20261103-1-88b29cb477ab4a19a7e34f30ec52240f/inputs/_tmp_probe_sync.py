# -*- coding: utf-8 -*-
import importlib.util, sys, traceback, pathlib
GEN = r"D:\股票数据\市场数据\生成盯盘台.py"
ST = pathlib.Path(r"D:\股票数据\市场数据") / ".review_staging" / sys.argv[1]
spec = importlib.util.spec_from_file_location("gen_dp", GEN)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
site = ST / "site"
root = ST / "inputs"
print("site exists", site.is_dir(), "root exists", root.is_dir())
try:
    out = m._sync_capability_blocks(site, "20261102", root=root)
    print("OK", out)
except BaseException as e:
    print("EXC TYPE", type(e).__name__, "MSG", repr(str(e))[:800])
    traceback.print_exc()
