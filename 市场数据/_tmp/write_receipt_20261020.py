# -*- coding: utf-8 -*-
"""写 能力使用回执_20261020.json（七域覆盖，绑定本次能力预加载 sha256）。"""
import json, hashlib, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, "_学习")
D = "20261020"
pre = os.path.join(L, "能力预加载_%s.json" % D)
sha = hashlib.sha256(open(pre, "rb").read()).hexdigest()

receipt = {
    "schema_version": 1,
    "as_of": D,
    "written_at": "20261020 18:55",
    "preload": {"path": "_学习/能力预加载_%s.json" % D, "sha256": sha},
    "routes": {
        "auction": {
            "status": "no_eligible_capabilities",
            "considered_ids": [],
            "applied": [],
            "rejected": [],
        },
        "lhb": {
            "status": "applied",
            "considered_ids": ["extension:cap-lhb-netbuy-valid"],
            "applied": [{
                "id": "extension:cap-lhb-netbuy-valid",
                "effect": "席位判读纳入净买占比维度：今日82条龙虎榜按净买占比分档筛票，净买占比弱/两源净额矛盾的6只（000823/002245/002343/300006/601811/603466）不进荐票，荐票 600267/300115/301313 均带净买占比数值与席位分档；净买占比成为否决/排序维度而非新增推荐",
                "source_locator": "_学习/lhb判断_%s.json#深挖 与 #判断.证据（净买占比出现21处）" % D,
            }],
            "rejected": [],
        },
        "theme": {
            "status": "no_eligible_capabilities",
            "considered_ids": [],
            "applied": [],
            "rejected": [],
        },
        "logic": {
            "status": "no_eligible_capabilities",
            "considered_ids": [],
            "applied": [],
            "rejected": [],
        },
        "limitup": {
            "status": "applied",
            "considered_ids": ["extension:cap-limitup-turnover-valid"],
            "applied": [{
                "id": "extension:cap-limitup-turnover-valid",
                "effect": "质量库选票保留换手率维度：今日54只打标中换手率桶进入主导/拖累因子（≥20%档+0.6、10-20%档+0.5、<3%档-0.6），机械否决高风险票的排序，不改变全池执1负期望符号（预测均涨-0.339%、胜率42.59%）",
                "source_locator": "_学习/limitup判断_%s.json#判断.证据 与 #深挖（cap-limitup-turnover-valid 出现2处）" % D,
            }],
            "rejected": [],
        },
        "cycle": {
            "status": "no_eligible_capabilities",
            "considered_ids": [],
            "applied": [],
            "rejected": [],
            "note": "周期域由 周期投票.py 机械产出（第11b步），今日预加载 0 条可复用能力",
        },
        "master": {
            "status": "no_eligible_capabilities",
            "considered_ids": [],
            "applied": [],
            "rejected": [],
            "note": "总审域由对抗总审子agent承担，今日预加载 0 条可复用能力（环境加权改用 _战绩画像汇总_%s.json）" % D,
        },
    },
}
out = os.path.join(L, "能力使用回执_%s.json" % D)
json.dump(receipt, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", out, "sha", sha[:16])
