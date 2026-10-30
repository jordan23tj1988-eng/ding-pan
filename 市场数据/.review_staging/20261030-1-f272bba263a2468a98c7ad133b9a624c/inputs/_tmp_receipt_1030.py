# -*- coding: utf-8 -*-
"""构建 _学习/能力使用回执_20261030.json (七域) —— 按 能力进化接线._validate_receipt 规则
宿主补写：片段缺失，但两路能力均有真实使用痕迹（引用原文），无效果证据的一律 rejected。"""
import json, io, os, hashlib, sys

BASE = r"D:\股票数据\市场数据"
D = sys.argv[1] if len(sys.argv) > 1 else "20261030"
L = os.path.join(BASE, "_学习")
ROUTES = ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]
PRELOAD = os.path.join(L, "能力预加载_%s.json" % D)

APPLIED = {
    "lhb": {
        "extension:cap-lhb-netbuy-valid": (
            "净买占比口径按该能力修正为『净买额/该股成交额』，并在席位判读中落 10-20% 正格遴选"
            "（000995 皇台酒业净买占比落 10-20% 正格→5% 试探仓；601083 打折 3.25×/301520 零 S-A 只观察）"
        ),
    },
    "limitup": {
        "extension:cap-limitup-turnover-valid": (
            "选票保留换手率维度并用于虚胖检测：换手≥20% 桶 n=1934/45.2%/+0.11%（p=0.02，未过 Bonferroni 校正，"
            "故不单独成规则）；一字检测用换手 1.8%/2.5%/3.2% 判『封单是假强度』；001219 换手 24.9% 计入荐票理由"
        ),
    },
}


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


pre = json.load(io.open(PRELOAD, encoding="utf-8"))
routes = pre.get("routes") or {}
eligible = {r: [str(x.get("id")) for x in ((routes.get(r) or {}).get("records") or [])] for r in ROUTES}

out = {}
for r in ROUTES:
    ids = eligible[r]
    applied, rejected = [], []
    for cid in ids:
        eff = APPLIED.get(r, {}).get(cid)
        if eff:
            applied.append({"id": cid, "effect": eff[:400],
                            "source_locator": "_学习/%s判断_%s.json#判断" % (r, D)})
        else:
            rejected.append({"id": cid, "reason": "本路判断未引用该能力(无 effect 证据, 不写 applied 以防编造)"})
    status = "no_eligible_capabilities" if not ids else ("applied" if applied else "rejected_all")
    out[r] = {"status": status, "considered_ids": ids, "applied": applied, "rejected": rejected}

doc = {"schema_version": 1, "as_of": D, "decision_cutoff": D,
       "preload": {"path": PRELOAD, "sha256": sha(PRELOAD)},
       "routes": out,
       "source": "宿主补写(片段缺失)：两路按判断文件原文引用判为 applied，其余零可复用能力→no_eligible_capabilities；零编造"}
p = os.path.join(L, "能力使用回执_%s.json" % D)
json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({r: (out[r]["status"], len(out[r]["applied"]), len(out[r]["rejected"])) for r in ROUTES}, ensure_ascii=False))
print("WROTE", p)
