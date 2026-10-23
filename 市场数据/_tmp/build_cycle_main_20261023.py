# -*- coding: utf-8 -*-
"""由 cycle agent 的结构化产物（已归档）生成生产命名的 周期主判_20261023.json
schema 对齐 周期主判_20261022.json（10 键）。所有字段值均原样搬运，不新增判断。
"""
import json, os

os.chdir(r"D:\股票数据\市场数据")
D = "20261023"
o = json.load(open(f"_学习/_归档/cycle判断_{D}_结构化归档.json", encoding="utf-8"))

votes = o.get("投票计票") or {}
detail = o.get("五路投票汇总") or {}
compact = {}
for r, v in detail.items():
    if isinstance(v, dict):
        compact[r] = f"{v.get('隐含周期倾向', '?')}/{v.get('原档位', '?')}/{v.get('置信度', '?')}"
    else:
        compact[r] = str(v)

main = {
    "date": D,
    "stage": o.get("周期阶段"),
    "direction": (o.get("次日方向") or "").replace("（分化）", "").replace("(分化)", ""),
    "温度档": f"{o.get('情绪三态')}（{o.get('情绪三态_依据', '')[:60]}）",
    "evidence": f"【一句话】{o.get('周期阶段_定位')}。{o.get('情绪三态_依据')}",
    "量能台阶": o.get("量能台阶"),
    "攻防档": o.get("攻防总开关_说明"),
    "source": "；".join(o.get("证据") or []),
    "stage_qualifier": o.get("周期阶段_定位"),
    "复议": {
        "五路票": compact,
        "计票": votes,
        "合并说明": o.get("投票合并说明"),
        "与总审一致性": o.get("主判与总审是否一致"),
        "一致性说明": o.get("一致性说明"),
        "可证伪条件": o.get("可证伪条件"),
        "盲区声明": o.get("盲区声明"),
        "置信度": o.get("置信度"),
        "置信度说明": o.get("置信度_说明"),
    },
}
op = f"_学习/周期主判_{D}.json"
json.dump(main, open(op, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("写入", op, os.path.getsize(op), "bytes | 键", list(main))
print("stage", main["stage"], "| direction", main["direction"], "| 五路票", compact)
