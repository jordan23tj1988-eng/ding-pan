# -*- coding: utf-8 -*-
"""复现 limitup 数据核对：按 review_publish._check_one 的方式注入 module_render_limitup 后运行。
用法: python _tmp_lucheck.py <frozen_dir> <stage_dir> <YYYYMMDD>
"""
import sys, os, importlib.util

FROZEN, STAGE, D = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, FROZEN)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dep = load('module_render_limitup', os.path.join(FROZEN, 'module_render_limitup.py'))
dep.BASE = dep.CD = FROZEN
dep.L = os.path.join(FROZEN, '_学习')
sys.modules['module_render_limitup'] = dep

m = load('lucheck', os.path.join(FROZEN, 'limitup数据核对.py'))
m.R = FROZEN
m.BASE = FROZEN
m.L = os.path.join(FROZEN, '_学习')
m.SITE = STAGE
sys.argv = [m.__file__, D]
raise SystemExit(m.main())
