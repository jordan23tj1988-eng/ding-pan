# -*- coding: utf-8 -*-
"""拉 sina K 线的 4 脚本多线程改串行断言(防 mini_racer 整进程崩溃)。离线源码断言。"""
import os

import pytest


def _read(mkt, rel):
    p = os.path.join(mkt, rel)
    if not os.path.isfile(p):
        pytest.skip(f"{rel} 不存在")
    with open(p, encoding="utf-8") as f:
        return f.read()


# 纯拉 sina 的脚本：全文件不得出现 ThreadPoolExecutor
PURE_SINA = ["涨停质量训练.py", "竞价信号训练.py", "链条位置.py"]


@pytest.mark.parametrize("f", PURE_SINA)
def test_纯sina脚本无线程池(mkt, f):
    src = _read(mkt, f)
    assert "ThreadPoolExecutor" not in src, f"{f} 仍含 ThreadPoolExecutor(拉sina多线程会崩mini_racer)"


def test_席位动向库fetch_bars串行(mkt):
    src = _read(mkt, "席位动向库.py")
    assert "ThreadPoolExecutor(4)" not in src, "fetch_bars 拉 sina 应已改串行"
    assert "sum(one(c) for c in codes)" in src, "fetch_bars 应落为 sum(one(c) for c in codes) 串行"
    # 东财席位接口 2 处多线程保留(不涉及 mini_racer，故意保留吞吐)
    assert src.count("ThreadPoolExecutor(16)") == 2, "东财席位接口应保留 2 处 ThreadPoolExecutor(16)"
