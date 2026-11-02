# -*- coding: utf-8 -*-
"""在候选 staging 上单跑某路哨兵，拿到逐项 FAIL 明细。用法: _tmp_probe_sentinel.py lhb"""
import io, json, sys, contextlib, pathlib

BASE = pathlib.Path(r"D:\股票数据\市场数据")
route = sys.argv[1]
sts = sorted((BASE / ".review_staging").glob("20261102-*"), key=lambda p: p.stat().st_mtime)
ST = sts[-1]
frozen = ST / "inputs"
stage = ST / "site"
print("staging", ST.name, "route", route)


def load_module(path):
    import types
    module = types.ModuleType(path.stem)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


if route == "limitup":
    dep = load_module(frozen / "module_render_limitup.py")
    dep.BASE = dep.CD = str(frozen)
    dep.L = str(frozen / "_学习")
    sys.modules["module_render_limitup"] = dep

module = load_module(frozen / f"{route}数据核对.py")
module.R = str(frozen)
module.BASE = str(frozen)
module.L = str(frozen / "_学习")
module.SITE = str(stage)
sys.argv = [module.__file__, "20261102", "--page", str(stage / f"{route}.html")]

rows = []
_orig = getattr(module, "chk", None)


def record(issues, ok, label, detail, *a, **k):
    rows.append({"ok": bool(ok), "label": label, "detail": str(detail)})
    if _orig:
        return _orig(issues, ok, label, detail, *a, **k)


if _orig:
    module.chk = record

buf = io.StringIO()
code = 0
try:
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = module.main()
except SystemExit as e:
    code = e.code
print("exit", code, "rows", len(rows))
for r in rows:
    if not r["ok"]:
        print("FAIL", r["label"], "|", r["detail"][:260])
print("---- log tail ----")
print(buf.getvalue()[-3000:])
