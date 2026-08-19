# -*- coding: utf-8 -*-
"""Master指派承接闭环防复发(#104)：契约五件套含总审 + master结算截止日查证。离线可跑。"""
import json
import os

import pytest


def _read(path):
    if not os.path.isfile(path):
        pytest.skip(f"{path} 不存在")
    with open(path, encoding="utf-8") as f:
        return f.read()


def _load(path):
    if not os.path.isfile(path):
        pytest.skip(f"{path} 不存在")
    return json.load(open(path, encoding="utf-8"))


# ---------- 契约层: cron jobs.json 第6步必读五件套含总审 + 14b master结算接线 ----------

def test_契约五件套含总审指派承接(cron_jobs_path):
    """第6步必读五件套必须含 总审_{昨日}.json(Master指派清单承接源)——#104根因1: 五件套无总审致各路只回旧总审。"""
    jobs = _load(cron_jobs_path)
    p = jobs["jobs"][0]["prompt"]
    assert "总审_{昨日}.json(★Master指派清单承接源" in p, "五件套缺总审——各路看不到Master指派清单"
    assert "承接Master指派[ID]" in p, "契约缺承接响应格式要求"


def test_契约master结算接线(cron_jobs_path):
    """14b步必须调用 master结算.py(截止日查证)——#104根因3: 无调用方, jsonl 0字节。"""
    jobs = _load(cron_jobs_path)
    p = jobs["jobs"][0]["prompt"]
    assert "master结算.py {昨日}" in p, "契约未接线 master结算.py——指派状态流转永不执行"
    assert "按指派截止日查" in p, "master结算须按截止日查证(昨日指派今日承接)"


# ---------- 脚本层: master结算.py 时序/正则/截止解析 ----------

def test_master结算截止日查证(mkt):
    """master结算必须按指派截止日查 judgment_{截止日}, 而非 dprev——#104根因2: 总审晚于五路, dprev当天不可能承接。"""
    src = _read(os.path.join(mkt, "master结算.py"))
    assert "judgment_%s.json' % cut" in src or "judgment_%s.json\" % cut" in src, \
        "master结算仍查 dprev 当日 judgment——时序错位恒未承接"
    assert "_cut_date" in src, "缺 _cut_date 截止日解析"


def test_master结算承接正则放宽(mkt):
    """承接匹配须容忍 '承接Master指派 [ID]' 等间隔——原正则 '指派[左括号]?ID' 只匹配紧邻。"""
    src = _read(os.path.join(mkt, "master结算.py"))
    assert "{0,20}?%s" in src.replace("\\s", ""), "承接正则未放宽(0-20字符间隔容忍)"
