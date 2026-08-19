# -*- coding: utf-8 -*-
"""席位路反思 jsonl 完整性 + 去重断言。离线可跑。"""
import json
import os

import pytest

REQUIRED = ["荐票日", "执行胜率", "均收", "立功", "打脸", "反思"]


def _rows(path):
    if not os.path.isfile(path):
        pytest.skip("席位反思 jsonl 不存在")
    with open(path, encoding="utf-8") as f:
        return [l for l in f if l.strip()]


def test_非空(jsonl_席位反思):
    assert len(_rows(jsonl_席位反思)) > 0


def test_每行合法json且字段完整(jsonl_席位反思):
    for l in _rows(jsonl_席位反思):
        d = json.loads(l)  # 非法行会抛异常
        for k in REQUIRED:
            assert k in d, f"缺字段 {k}: {l[:60]}"


def test_荐票日无重复(jsonl_席位反思):
    days = [json.loads(l)["荐票日"] for l in _rows(jsonl_席位反思)]
    assert len(days) == len(set(days)), "存在重复荐票日(append_dedup 去重门禁失效)"


def test_无完全重复行(jsonl_席位反思):
    rows = _rows(jsonl_席位反思)
    assert len(rows) == len(set(rows)), "存在完全重复行"
