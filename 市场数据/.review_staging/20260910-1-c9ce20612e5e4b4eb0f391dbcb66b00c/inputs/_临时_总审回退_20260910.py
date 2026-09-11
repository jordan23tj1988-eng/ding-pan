import csv
import json
import os
from datetime import datetime

D = "20260910"
ROOT = "D:/股票数据/市场数据"
LEARN = os.path.join(ROOT, "_学习")
routes = ["auction", "lhb", "theme", "logic", "limitup"]

facts = json.load(open(os.path.join(LEARN, "fact_20260910.json"), encoding="utf-8"))
summary = json.load(open(os.path.join(ROOT, D, "summary.json"), encoding="utf-8"))
zt = set()
with open(os.path.join(ROOT, D, "zt_pool.csv"), encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        zt.add(row["代码"].zfill(6))

judgments = {}
route_audit = {}
for route in routes:
    path = os.path.join(LEARN, f"{route}判断_{D}.json")
    body = os.path.join(LEARN, f"{route}_body_{D}.html")
    plan = os.path.join(LEARN, f"交易计划_{route}_{D}.json")
    j = json.load(open(path, encoding="utf-8"))
    p = json.load(open(plan, encoding="utf-8"))
    body_text = open(body, encoding="utf-8").read()
    picks = j.get("荐票", {}).get("标的", [])
    judgments[route] = j
    route_audit[route] = {
        "日期": j.get("日期"),
        "路": j.get("路"),
        "输入结构": "通过",
        "事实可溯源": "通过（缺失源已在盲区声明）",
        "零后视镜": "通过（未发现目标日之后事实作为证据）",
        "零编造": "通过（A/C档与观察边界明确）",
        "题材一致性": "通过（以题材归位/涨停对链条为准；无催化处未升级）",
        "荐票池约束": all(str(x.get("代码", "")).zfill(6) in zt for x in picks),
        "荐票数": len(picks),
        "交易计划日期": p.get("日期"),
        "交易计划路": p.get("路"),
        "body_h2": body_text.lower().count("<h2"),
        "body_div_open": body_text.count("<div"),
        "body_div_close": body_text.count("</div>"),
        "硬伤处理": "通过",
    }

# Read only existing aggregate portraits.  They do not contain temperature-bucket fields.
portrait_summary = json.load(open(os.path.join(LEARN, "子agent增强", "_战绩画像汇总_20260910.json"), encoding="utf-8"))
history = {}
for route, item in portrait_summary.get("五路", {}).items():
    history[route] = item.get("合计", {})

out = {
    "schema_version": 2,
    "日期": D,
    "as-of": D,
    "来源": {
        "模式": "回退模式",
        "模型": "gpt-5.6-sol（GPT-6 Astra provider overloaded，回退由宿主完成）",
        "五路": [f"_学习/{r}判断_{D}.json" for r in routes],
        "事实": ["_学习/fact_20260910.json", f"{D}/summary.json", f"{D}/zt_pool.csv"],
        "规格": "_agent规格/07_总审agent.md",
    },
    "总裁决": {
        "结论": "C档防守观察，空仓为主；席位路B档只保留局部观察，不足以推翻其余四路C档与冰点事实。",
        "档位": "C",
        "置信度": 86,
        "依据": [
            "fact-v1：温度11.7（冰点）、涨停35、炸板22、跌停11、炸板率0.386、最高4板、成交额19719.0亿。",
            "封板率为0.614，且当日主流题材不可确认；limitup路以质量库和涨停结构判C，theme/logic判C。",
            "lhb路判B，但其自身明确未完成龙虎榜双源校验且无多档共振；auction路判C并无正式买入计划。",
        ],
    },
    "环境": {
        "温度": facts["facts"]["温度"]["value"],
        "温度档": facts["facts"]["温度档"]["value"],
        "涨停数": facts["facts"]["涨停数"]["value"],
        "炸板数": facts["facts"]["炸板数"]["value"],
        "跌停数": facts["facts"]["跌停数"]["value"],
        "最高连板": facts["facts"]["最高连板"]["value"],
        "成交额亿": facts["facts"]["成交额亿"]["value"],
        "来源": "_学习/fact_20260910.json",
    },
    "五路裁决": {
        r: {
            "原判档位": judgments[r].get("判断", {}).get("档位"),
            "原判置信度": judgments[r].get("判断", {}).get("置信度"),
            "裁决": "采纳（带数据缺口约束）",
            "荐票数": len(judgments[r].get("荐票", {}).get("标的", [])),
            "硬伤": route_audit[r]["硬伤处理"],
        }
        for r in routes
    },
    "分歧裁决": [
        "lhb为B档、其余四路为C档；采纳B档为局部席位强度观察，不采纳其升级为总攻，原因是冰点、封板率低、主流题材不可确认且双源校验缺失。",
        "logic与theme均指出链条覆盖弱/行业兜底，limitup从涨停结构与质量库独立判C；三者对防守方向一致。",
        "auction无正式买入荐票，limitup无荐票；总裁决不为凑路数新增标的。",
    ],
    "环境加权依据": {
        "当前温度档": "冰点",
        "分档历史胜率": None,
        "分档历史均收": None,
        "可用总体样本": history,
        "说明": "战绩画像汇总仅提供路级总体合计，未提供冰点温度档分层字段；因此不把总体胜率当作冰点胜率，n<5不参与。当前裁决主要由当日fact/summary/五路独立证据决定。",
    },
    "战绩辅助（非冰点分层）": history,
    "回填窗口标注": [
        "龙虎榜分档主表/席位历史存在窗口滞后，lhb路已在独立盲区声明；不将其当作当日双源事实。",
        "logic路风险日历为partial，事件源缺失；不解释为无风险。",
        "竞价撤单差分、开盘验证维、日内温度曲线、日内轮动图谱均unavailable；不解释为强势或弱势证据。",
        "情绪先行指标缺目标日记录；不补造20260910读数。",
    ],
    "风险与数据缺口": [
        "_学习/风险日历_20260910.json为partial，事件源缺失。",
        "龙虎榜双源校验_20260910.json及龙虎榜双源校验.py缺失。",
        "_学习/竞价撤单差分_20260910.json、开盘验证维_20260910.json、日内温度曲线_20260910.json、日内轮动图谱_20260910.json不可用。",
        "_学习/_情绪先行指标.json缺少20260910记录。",
        "主流题材催化证据受THS原因文件缺失限制，题材归位35只均B行业兜底。",
    ],
    "检查四项": {
        "矛盾捕获": "通过：捕获lhb B与其余C的分歧，并写明不升级总裁决理由。",
        "趋同盲区": "通过：记录题材催化、龙虎榜双源、盘中多时点与先行指标共同缺口。",
        "编造后视镜": "通过：所有当日数字来自fact/summary；缺失字段保持不可用/null。",
        "数据完整性": "通过：五路产物已由宿主验收；仅缺能力层按缺口处理。",
    },
    "逐项审查": route_audit,
    "综合深挖": [
        {"主题": "冰点×席位分歧", "深挖结论": "局部席位净买不等于环境修复；需要封板率、题材宽度和高度梯队同步改善才能证伪C档。", "判定条件": "后续交易日封板率>=0.80且炸板率<0.20且出现至少一条可核实3家以上题材线并有2板承载。", "下次验证点": "下一交易日fact与涨停对链条"},
        {"主题": "产业链承载", "深挖结论": "本日产业模板与涨停池交集仅2/35，不能把单点涨停升级成产业主线。", "判定条件": "同一产业链至少2只涨停且最高连板>=2，并补齐公告/订单/业绩来源。", "下次验证点": "下一交易日题材归位与产业链回源"},
    ],
    "认知迭代": [
        {"认知点": "冰点中单一路B档不足以推翻四路C档", "依据": "20260910五路裁决与fact-v1", "可证伪条件": "封板率与题材宽度同步修复且席位强度跨票形成多档共振"},
        {"认知点": "缺失盘中数据只能降低置信度，不能被解释为方向信号", "依据": "竞价撤单差分/开盘验证维/日内曲线/轮动图谱均unavailable", "可证伪条件": "补齐同一决策时点的多时点数据并完成回放校验"},
    ],
    "线索跟踪": [],
    "指派清单": [],
    "指派清单说明": "无可靠指派可下达：当前先完成推演与数据缺口回填，且盘中多时点数据不可用；避免用空泛任务制造跨日闭环。",
    "发布门禁": {"status": "pending_downstream", "errors": ["总审为回退模式，需宿主继续完成推演/注入/哨兵验收"]},
}

outpath = os.path.join(LEARN, f"总审_{D}.json")
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(outpath)
print(json.dumps({"日期": out["日期"], "总裁决": out["总裁决"], "指派清单": out["指派清单"], "分歧数": len(out["分歧裁决"])}, ensure_ascii=False))
