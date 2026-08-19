# -*- coding: utf-8 -*-
"""席位荐票结算链路：画像读源 + append_dedup 去重 + cron 拨正 + 旧脚本停用。离线可跑。"""
import json
import os

import pytest


def _read(mkt, rel):
    p = os.path.join(mkt, rel)
    if not os.path.isfile(p):
        pytest.skip(f"{rel} 不存在")
    with open(p, encoding="utf-8") as f:
        return f.read()


def test_画像席位路读新源(mkt):
    src = _read(mkt, "五路战绩画像.py")
    for line in src.splitlines():
        if '"lhb"' in line or "'lhb'" in line:
            assert "_席位荐票反思.jsonl" in line, f"lhb 配置行未指向新源: {line.strip()}"
            return
    pytest.fail("五路战绩画像.py 未找到 lhb 配置行")


def test_席位荐票结算用append_dedup去重(mkt):
    src = _read(mkt, "席位荐票结算.py")
    assert "append_dedup" in src, "席位荐票结算.py 未用 append_dedup 去重门禁"
    assert "_席位荐票反思.jsonl" in src, "席位荐票结算.py 未写 _席位荐票反思.jsonl"


def test_cron引用席位荐票结算脚本(cron_jobs_path):
    if not os.path.isfile(cron_jobs_path):
        pytest.skip("cron jobs.json 不存在")
    with open(cron_jobs_path, encoding="utf-8") as f:
        d = json.load(f)
    jobs = d.get("jobs", d)
    if isinstance(jobs, dict):
        jobs = list(jobs.values())
    joined = "\n".join(json.dumps(j, ensure_ascii=False) for j in jobs)
    assert "席位荐票结算.py" in joined, "cron 未引用席位荐票结算.py"
    assert "龙虎榜荐票结算.py" not in joined, "cron 仍引用已停用旧脚本龙虎榜荐票结算.py"


def test_旧脚本已停用删除(mkt):
    p = os.path.join(mkt, "龙虎榜荐票结算.py")
    assert not os.path.isfile(p), "旧脚本龙虎榜荐票结算.py 应已停用删除(备份在 _tmp)"
