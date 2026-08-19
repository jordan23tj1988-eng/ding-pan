# -*- coding: utf-8 -*-
"""去重门禁加固: ①append_dedup 幂等行为单测(直接调函数,非源码断言) ②五路结算 jsonl 去重完整性。离线可跑。"""
import importlib.util
import json
import os
import tempfile

import pytest


def _load_append_dedup(mkt):
    p = os.path.join(mkt, "_jsonl_append.py")
    if not os.path.isfile(p):
        pytest.skip("_jsonl_append.py 不存在")
    spec = importlib.util.spec_from_file_location("_jsonl_append_t", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.append_dedup


@pytest.fixture(scope="module")
def append_dedup(mkt):
    return _load_append_dedup(mkt)


# ---------- ① append_dedup 幂等行为单测 ----------

def test_首次写True重复写False(append_dedup):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.jsonl")
        obj = {"荐票日": "20260816", "均收": 1.0}
        assert append_dedup(p, obj, "荐票日") is True
        assert append_dedup(p, obj, "荐票日") is False
        lines = [l for l in open(p, encoding="utf-8") if l.strip()]
        assert len(lines) == 1, "重复追加应被幂等跳过(去重门禁失效)"


def test_元组key按组合去重(append_dedup):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.jsonl")
        a = {"荐票日": "20260816", "代码": "000001"}
        b = {"荐票日": "20260816", "代码": "000002"}
        assert append_dedup(p, a, ("荐票日", "代码")) is True
        assert append_dedup(p, b, ("荐票日", "代码")) is True
        assert append_dedup(p, a, ("荐票日", "代码")) is False
        lines = [l for l in open(p, encoding="utf-8") if l.strip()]
        assert len(lines) == 2


def test_坏行容错跳过(append_dedup):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            f.write("{坏行\n")
        obj = {"荐票日": "20260816"}
        assert append_dedup(p, obj, "荐票日") is True


# ---------- ② 五路结算 jsonl 去重完整性 ----------

# 五路结算 jsonl 均接 append_dedup(#085 四路 + #094 竞价池), 严格测日期无重复
ROUTES_ALL = [
    ("_题材荐票结算.jsonl", "荐票日"),
    ("_质量荐票结算.jsonl", "荐票日"),
    ("_逻辑荐票结算.jsonl", "荐票日"),
    ("_席位荐票反思.jsonl", "荐票日"),
    ("_竞价池结算.jsonl", "池日"),
]


def _rows(mkt, fname):
    p = os.path.join(mkt, "_学习", fname)
    if not os.path.isfile(p):
        pytest.skip(f"{fname} 不存在")
    return [l for l in open(p, encoding="utf-8") if l.strip()]


@pytest.mark.parametrize("fname,daykey", ROUTES_ALL)
def test_五路jsonl非空(mkt, fname, daykey):
    assert len(_rows(mkt, fname)) > 0


@pytest.mark.parametrize("fname,daykey", ROUTES_ALL)
def test_五路jsonl每行合法且日期字段存在(mkt, fname, daykey):
    for l in _rows(mkt, fname):
        d = json.loads(l)
        assert daykey in d, f"{fname} 缺日期字段 {daykey}: {l[:60]}"


@pytest.mark.parametrize("fname,daykey", ROUTES_ALL)
def test_五路jsonl日期字段无重复(mkt, fname, daykey):
    days = [json.loads(l)[daykey] for l in _rows(mkt, fname)]
    assert len(days) == len(set(days)), f"{fname} 存在重复{daykey}(去重门禁失效)"


@pytest.mark.parametrize("fname,daykey", ROUTES_ALL)
def test_五路jsonl无完全重复行(mkt, fname, daykey):
    rows = _rows(mkt, fname)
    assert len(rows) == len(set(rows)), f"{fname} 存在完全重复行"
