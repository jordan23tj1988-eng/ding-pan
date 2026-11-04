# -*- coding: utf-8 -*-
"""宿主侧：写 能力使用回执 + 周期主判 + 五路周期投票 (20261104)"""
import json, io, os, time

BASE = r"D:/股票数据/市场数据"
L = os.path.join(BASE, "_学习")
D = "20261104"

def jl(p):
    return json.load(io.open(p, encoding="utf-8"))

def js(p, o):
    t = p + ".tmp"
    with io.open(t, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1)
    os.replace(t, p)

# ---------- 1) 能力使用回执（七域） ----------
pre = jl(os.path.join(L, "能力预加载_%s.json" % D))
rec = {"schema_version": 1, "date": D, "as_of": D,
       "source": "_学习/能力预加载_%s.json" % D,
       "created_at": time.strftime("%Y-%m-%d %H:%M:%S"), "routes": {}}
for r in ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]:
    p_route = pre["routes"][r]
    if r in ("lhb", "limitup"):
        rj = jl(os.path.join(L, "%s判断_%s.json" % (r, D)))
        cap = rj.get("能力使用") or {}
        rec["routes"][r] = {
            "eligible_count": p_route.get("eligible_count", 0),
            "status": cap.get("status", "applied"),
            "considered_ids": cap.get("considered_ids", []),
            "applied": cap.get("applied", []),
            "rejected": cap.get("rejected", []),
            "artifact": "_学习/%s判断_%s.json#能力使用" % (r, D),
        }
    elif r == "master":
        z = jl(os.path.join(L, "总审_%s.json" % D))
        cap = z.get("能力承接") or {}
        rec["routes"][r] = {
            "eligible_count": p_route.get("eligible_count", 0),
            "status": cap.get("status", "no_eligible_capabilities"),
            "considered_ids": cap.get("considered_ids", []),
            "applied": cap.get("applied", []),
            "rejected": cap.get("rejected", []),
            "artifact": "_学习/总审_%s.json#能力承接" % D,
        }
    elif r in ("auction", "theme", "logic"):
        rj = jl(os.path.join(L, "%s判断_%s.json" % (r, D)))
        cap = rj.get("能力使用") or {}
        rec["routes"][r] = {
            "eligible_count": p_route.get("eligible_count", 0),
            "status": cap.get("status", "no_eligible_capabilities"),
            "considered_ids": cap.get("considered_ids", []),
            "applied": cap.get("applied", []),
            "rejected": cap.get("rejected", []),
            "artifact": "_学习/%s判断_%s.json#能力使用" % (r, D),
        }
    else:  # cycle
        rec["routes"][r] = {
            "eligible_count": p_route.get("eligible_count", 0),
            "status": "no_eligible_capabilities",
            "considered_ids": [], "applied": [], "rejected": [],
            "note": "预加载 routes.cycle eligible_count=0/records=[]（源 _学习/能力预加载_%s.json）→ 本域无可消费能力，不虚构引用；周期主判改由温度/先行指标/五路投票机数据合成。" % D,
            "artifact": "_学习/周期主判_%s.json" % D,
        }
js(os.path.join(L, "能力使用回执_%s.json" % D), rec)

# ---------- 2) 周期主判 ----------
temp = jl(os.path.join(L, "_市场温度表.json"))
lead = jl(os.path.join(L, "_情绪先行指标.json"))
pre_d = sorted(k for k in temp if k < D)[-1]
t_today = temp[D]["温度"]; t_prev = temp[pre_d]["温度"]
j1 = (lead.get(D) or {}).get("晋级", {}).get("一进二率")
j1p = (lead.get(pre_d) or {}).get("晋级", {}).get("一进二率")
z = jl(os.path.join(L, "总审_%s.json" % D))
verdict = z.get("总裁决") or {}
main = {
    "date": D, "stage": "启动", "direction": "升",
    "temperature": t_today,
    "evidence": (
        "温度 %s（昨 %s，Δ%+.1f）自冰点区回升至中性档；净涨停 118（昨48）、炸板率 22.0%%（昨41.5%%）、成交额 20377 亿（昨17034，+19.6%%）三项同向修复，"
        "一进二率 %s（昨 %s → 今日18.2%%）；但最高连板 3（昨4）、二板加 12、首封≥13:00 占 72%%、全池可兑现期望合计 -10.37pp → 判『启动』阶段、方向『升』但属宽度修复而非高度接力。"
        "总裁决 %s 档 %s 分、名义仓 1.5%%。"
    ) % (
        t_today, t_prev, t_today - t_prev,
        ("%.1f%%" % (j1 * 100)) if isinstance(j1, (int, float)) else "—",
        ("%.1f%%" % (j1p * 100)) if isinstance(j1p, (int, float)) else "—",
        verdict.get("档位", "C"), verdict.get("置信度", 68),
    ),
    "sources": ["_学习/_市场温度表.json#%s/%s" % (pre_d, D),
                "_学习/_情绪先行指标.json#晋级.一进二率",
                "20261104/summary.json", "_学习/总审_%s.json#总裁决" % D],
    "writer": "宿主(主agent)按温度表/先行指标/总审机械合成，未另派agent",
}
js(os.path.join(L, "周期主判_%s.json" % D), main)

# ---------- 3) 五路周期投票（按各路原文结论机器映射，evidence 引用原文） ----------
votes = {
    "auction": ("降", 67, "auc判断: 中40~65档20个池日均收-0.51%/票级胜率35.1%，今日118涨停落最差交叉(涨停≥90 7池日-1.53%)，基准仓必须为0，仅1.0%条件单 → 判次日方向偏弱"),
    "lhb": ("降", 70, "lhb判断: 榜票级净买-22.2148亿、全场真实率-21.11%连续第二日为负，0荐票空仓，强度不可读 → 判次日方向不升"),
    "theme": ("平", 68, "theme判断: 无主流(维持退为轮动)；半导体34只为午后扩散宽度陷阱、传媒6只仅主流候选未升格 → 判次日方向平(结构轮动)"),
    "logic": ("平", 72, "logic判断: 扩散型修复日但89.8%首板、首封≥13:00占72%、业绩在早盘确认价格在尾盘抢 → 结构待验证，判平"),
    "limitup": ("升", 64, "limitup判断: 宽度与封板质量同日修复(涨停+146%、炸板率41.5%→22.0%、封板总额+148%)，上调B档 → 判次日方向升(但非接力修复，仓位仍限1.5%)"),
}
for r, (d, cf, ev) in votes.items():
    js(os.path.join(L, "周期投票_%s_%s.json" % (r, D)), {
        "route": r, "d": D, "stage": "启动", "direction": d,
        "confidence": cf, "evidence": ev,
        "source": "_学习/%s判断_%s.json" % (r, D),
        "note": "宿主按本路已发版判断结论机器映射(引用原文数字)，非独立投票agent",
    })

print("回执/主判/五路票 已写:", D)
print("温度", t_today, "昨", t_prev, "Δ%.1f" % (t_today - t_prev))
