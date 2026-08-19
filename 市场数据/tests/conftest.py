# -*- coding: utf-8 -*-
"""pytest 骨架公共配置。

MKT = 市场数据根目录(本文件父目录的父目录)，不硬编码盘符，换机可移植。
所有测试默认离线(读文件/源码断言)，稳定可复现，不依赖网络/数据源/代理。
"""
import os
import sys

import pytest

# 市场数据根目录 = tests/ 的父目录
MKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if MKT not in sys.path:
    sys.path.insert(0, MKT)


@pytest.fixture(scope="session")
def mkt():
    """市场数据根目录(绝对路径)。"""
    return MKT


@pytest.fixture(scope="session")
def cron_jobs_path():
    """Hermes cron jobs.json 路径(profile a；换机/换用户名自动跟随 ~)。"""
    return os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "hermes", "profiles", "a", "cron", "jobs.json",
    )


@pytest.fixture(scope="session")
def jsonl_席位反思(mkt):
    """席位路反思 jsonl 路径。"""
    return os.path.join(mkt, "_学习", "_席位荐票反思.jsonl")
