# -*- coding: utf-8 -*-
"""真实串行拉取冒烟(碰网络+临时换缓存，默认跳过)。用 -m network 显式跑。

验证 fetch_bars 串行拉取不崩 mini_racer 且产出缓存(仅 000593 单票)。
"""
import importlib.util
import os
import shutil

import pytest

pytestmark = pytest.mark.network


def test_席位动向库fetch_bars真实串行拉取(mkt):
    p = os.path.join(mkt, "席位动向库.py")
    if not os.path.isfile(p):
        pytest.skip("席位动向库.py 不存在")
    spec = importlib.util.spec_from_file_location("xw_dynamic_test", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # 顶层加载失败(环境/依赖)则跳过，不视为断言失败
        pytest.skip(f"席位动向库.py 加载失败: {e}")

    CSV = os.path.join(mkt, "_学习", "_bars_cache", "000593.csv")
    if not os.path.isfile(CSV):
        pytest.skip("缓存无 000593.csv，跳过真实拉取")
    BAK = os.path.join(mkt, "_tmp", "000593.csv.pytestbak")
    shutil.move(CSV, BAK)
    try:
        mod.fetch_bars(["000593"])
        assert os.path.exists(CSV), "fetch_bars 串行拉取未产出缓存"
    finally:
        if os.path.isfile(BAK):
            shutil.move(BAK, CSV)
