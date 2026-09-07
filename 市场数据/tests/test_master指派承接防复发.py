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

def test_master结算截止日查证(mkt, tmp_path, monkeypatch):
    """跨日查证必须实读截止日；不以旧函数名/字符串拼写判正确。"""
    from pathlib import Path
    import review_learning as learning
    source = Path(__file__).resolve().parents[2] / 'evidence' / 'real_samples'
    seen=[]
    original=learning._load
    def tracked(path):
        seen.append(Path(path).name)
        return original(path)
    monkeypatch.setattr(learning, '_load', tracked)
    result=learning.settle_master(source, '20260904', tmp_path / 'audit')
    assert result['status'] == 'pass', result.get('errors')
    assert 'judgment_20260904.json' in seen, '未读取9/3指派的9/4截止日正文'
    assert 'judgment_20260907.json' not in seen, '提前读了未到期未来正文'
    items=[x for x in result['assignments'] if x['d']=='20260903']
    assert items and all(x['due_d']=='20260904' for x in items)
    assert any(x['status']=='acknowledged' for x in items), '截至日真实ID未承接'


def test_master结算承接正则放宽(mkt):
    """承接匹配须容忍 '承接Master指派 [ID]' 等间隔——原正则 '指派[左括号]?ID' 只匹配紧邻。"""
    src = _read(os.path.join(mkt, "master结算.py"))
    assert "{0,20}?%s" in src.replace("\\s", ""), "承接正则未放宽(0-20字符间隔容忍)"
