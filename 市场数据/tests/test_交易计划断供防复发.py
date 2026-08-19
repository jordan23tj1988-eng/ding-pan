# -*- coding: utf-8 -*-
"""交易计划六路断供防复发(#103)：契约⑪硬要求 + 哨兵C11 存在性/schema 校验。离线可跑。"""
import json
import os

import pytest


def _read(mkt, rel):
    p = os.path.join(mkt, rel)
    if not os.path.isfile(p):
        pytest.skip(f"{rel} 不存在")
    with open(p, encoding="utf-8") as f:
        return f.read()


# ---------- 契约层: cron jobs.json 第6步⑪ 交易计划硬要求 ----------

def test_契约c11交易计划硬要求(cron_jobs_path):
    if not os.path.isfile(cron_jobs_path):
        pytest.skip("cron jobs.json 不存在")
    with open(cron_jobs_path, encoding="utf-8") as f:
        d = json.load(f)
    jobs = d.get("jobs", [])
    daily = next((j for j in jobs if j.get("name") == "sentiment-daily-review"), None)
    if daily is None:
        pytest.fail("cron jobs.json 未找到 sentiment-daily-review 任务")
    p = daily["prompt"]
    assert "⑪★交易计划硬要求" in p, "契约⑪(交易计划硬要求)缺失——8/13断供根因, 禁止删除"
    assert "交易计划_{route}_{今日}.json" in p, "契约⑪未写明交易计划文件路径"
    assert "buys" in p and "sells" in p, "契约⑪未写明 buys/sells schema"
    assert "在持票逐票表态" in p, "契约⑪未要求在持票逐票表态"


def test_契约master交易计划补回(cron_jobs_path):
    if not os.path.isfile(cron_jobs_path):
        pytest.skip("cron jobs.json 不存在")
    with open(cron_jobs_path, encoding="utf-8") as f:
        d = json.load(f)
    jobs = d.get("jobs", [])
    daily = next((j for j in jobs if j.get("name") == "sentiment-daily-review"), None)
    if daily is None:
        pytest.fail("cron jobs.json 未找到 sentiment-daily-review 任务")
    p = daily["prompt"]
    assert "交易计划_master_{今日}.json" in p, "master路交易计划缺失——C11校验含master, 无写入者=必然FAIL"


# ---------- 哨兵层: C11 存在性 + schema 契约校验 ----------

def test_哨兵C11交易计划检查存在(mkt):
    src = _read(mkt, "复盘一致性哨兵.py")
    assert "C11" in src, "复盘一致性哨兵.py 未实现 C11"
    assert "_PLAN_ROUTES" in src, "C11 未定义六路清单"
    for route in ("auction", "lhb", "theme", "logic", "limitup", "master"):
        assert route in src, f"C11 六路清单缺 {route}"


def test_哨兵C11_schema契约校验(mkt):
    src = _read(mkt, "复盘一致性哨兵.py")
    # 防"荐票格式文件在但引擎读不到buys/sells=静默空仓"(8/11-12 limitup实坑)
    assert "buys" in src and "sells" in src and "notes" in src, (
        "C11 schema校验缺失——文件在但荐票格式(荐票/观察)引擎仍空仓, 存在性检查不够"
    )
    assert "schema不符引擎契约" in src, "C11 未实现 schema 不符 FAIL 分支"


def test_引擎读交易计划buys_sells契约(mkt):
    src = _read(mkt, "模拟盘引擎.py")
    assert "交易计划_%s_%s.json" in src, "模拟盘引擎.py 未读 交易计划_{route}_{d}.json"
    assert "plan.get('buys')" in src, "引擎买入只认 buys 键(荐票/观察格式不认)"
    assert "plan_prev.get('sells')" in src, "引擎卖出只认 sells 键"
