# -*- coding: utf-8 -*-
"""题材归位_20260923.json 生成: THS涨停原因(B档)为主证据 + 行业兜底, agent 判定大方向/环节。
零编造: 催化一律取当日 THS 涨停原因原文, 无则 null; 不继承历史催化。"""
import json, os, csv
from collections import Counter

BASE = r"D:\股票数据\市场数据"
L = os.path.join(BASE, "_学习")
D = "20260923"

# 大方向/环节: agent 依当日 THS 涨停原因 + 产业链模板 判定
MAP = {
    "001234": ("消费-纺织服装", "针织服装贴牌"),
    "002238": ("出版文化传媒", "电视广播/数据中心"),
    "600825": ("出版文化传媒", "出版发行"),
    "601811": ("出版文化传媒", "出版发行/数字教育"),
    "603636": ("AI应用-政务智能体", "IT服务"),
    "000560": ("地产链-房产经纪", "房产服务"),
    "600743": ("地产链-物业酒店", "房地产服务"),
    "600503": ("地产链-房地产开发", "房地产开发+机器人"),
    "600802": ("地产链-建材", "水泥"),
    "002989": ("半导体-封装基板", "装修装饰/FCBGA转型"),
    "603328": ("AI硬件-PCB", "元件/PCB"),
    "605058": ("AI硬件-PCB", "元件/HDI板"),
    "002635": ("AI硬件-PCB", "消费电子/光模块基座"),
    "301150": ("AI硬件-铜箔", "电池/电子铜箔"),
    "603937": ("AI硬件-铜箔", "工业金属/电池铝箔"),
    "002426": ("AI硬件-铜箔", "消费电子/复合铜箔"),
    "603124": ("AI硬件-铜箔液冷", "金属新材料/铜基"),
    "603773": ("AI硬件-玻璃基板", "光学光电"),
    "603396": ("AI硬件-玻璃基封装", "光伏设备/半导体装备"),
    "603803": ("AI硬件-光网络", "通信设备/交换机"),
    "600605": ("半导体-光罩存储", "商业零售跨界"),
    "002119": ("半导体-封装材料", "半导体"),
    "603991": ("半导体-引线框架", "半导体"),
    "688512": ("半导体-射频前端", "半导体"),
    "603222": ("半导体-跨界芯片", "医疗器械"),
    "002909": ("液冷散热", "化学制品/液冷硅油"),
    "002937": ("液冷散热", "汽车零部/服务器液冷"),
    "688628": ("仪器仪表-光通信测试", "通用设备"),
    "688337": ("仪器仪表-光通信测试", "通用设备"),
    "002819": ("仪器仪表-光通信测试", "通用设备"),
    "688056": ("仪器仪表-半导体检测", "通用设备"),
    "002935": ("商业航天-时间频率", "军工电子"),
    "000910": ("机器人-七腾机器人", "家居用品/PCB概念"),
    "600843": ("机器人-缝制低空", "专用设备"),
    "002614": ("机器人-健康按摩", "其他家电"),
    "002541": ("机器人-焊接钢结构", "专业工程"),
    "600418": ("汽车-华为尊界", "商用车"),
    "603949": ("汽车-热管理", "汽车零部"),
    "600653": ("汽车-经销服务", "汽车服务"),
    "600293": ("建材-电子玻璃", "玻璃玻纤"),
    "000850": ("国改-纺织矿业", "纺织制造"),
    "600230": ("化工-TDI/PC", "化学制品"),
    "603067": ("化工-铬盐/SOFC", "化学原料"),
    "002286": ("消费-功能糖", "农产品加工"),
    "600371": ("农业-种业", "种植业"),
    "002633": ("高端制造-燃气轮机", "通用设备/滑动轴承"),
    "002849": ("高端制造-智能仪表", "通用设备/智能燃气表"),
    "300931": ("高端制造-电梯", "专用设备/电梯后市场"),
    "603373": ("低空经济-安全服务", "专业服务"),
    "002638": ("照明-车路云储能", "照明设备"),
    "688656": ("医药-过敏诊断", "医疗器械"),
}

reason_path = os.path.join(L, "涨停原因_%s.json" % D)
reasons = {}
if os.path.exists(reason_path):
    reasons = (json.load(open(reason_path, encoding="utf-8")) or {}).get("映射") or {}

rows = list(csv.DictReader(open(os.path.join(BASE, D, "zt_pool.csv"), encoding="utf-8-sig")))
summary = json.load(open(os.path.join(BASE, D, "summary.json"), encoding="utf-8-sig"))

mp = {}
missing = []
for r in rows:
    c = str(r["代码"]).zfill(6)
    rn = reasons.get(c) or {}
    why = rn.get("原因")
    if c in MAP:
        big, seg = MAP[c]
    else:
        big, seg = str(r["所属行业"]).strip(), str(r["所属行业"]).strip()
        missing.append(c)
    mp[c] = {
        "股票代码": c,
        "名称": str(r["名称"]).strip(),
        "大方向": big,
        "环节": seg,
        "催化": why,
        "催化状态": "THS涨停原因(B档, 同花顺涨停池) 20260923" if why else "催化缺失(当日THS涨停原因未覆盖)",
        "来源档": "B" if why else "B",
        "来源说明": ("B档: _学习/涨停原因_20260923.json(同花顺涨停池 reason_type 原文); 大方向/环节为 agent 依原因文本+产业链模板判定, 未继承历史催化。"
                     if why else
                     "B行业兜底: 20260923/zt_pool.csv 所属行业字段; 当日THS涨停原因未覆盖该股。"),
        "所属行业": str(r["所属行业"]).strip(),
        "连板数": str(r["连板数"]),
        "涨停统计": str(r["涨停统计"]),
        "首次封板时间": str(r["首次封板时间"]),
        "炸板次数": str(r["炸板次数"]),
        "封板资金": str(r["封板资金"]),
        "涨停原因": why,
    }

zh = str(summary.get("涨停家数", ""))
out = {
    "日期": D,
    "映射": mp,
    "来源": "20260923/zt_pool.csv;20260923/summary.json;_学习/涨停原因_20260923.json(同花顺涨停原因B档)",
    "口径": "逐只覆盖20260923/zt_pool.csv全量涨停池; 催化取当日同花顺涨停原因原文(B档), 无覆盖则催化null并标行业兜底; 大方向/环节由agent依原因文本判定, 不继承历史催化。",
    "source_status": {
        "zt_pool": {"status": "available", "file": "20260923/zt_pool.csv", "rows": len(rows)},
        "summary": {"status": "available", "file": "20260923/summary.json", "declared_limit_up_count": summary.get("涨停家数")},
        "ths_reason_20260923": {"status": "available" if reasons else "missing",
                                "file": "_学习/涨停原因_20260923.json", "rows": len(reasons)},
        "historical_relocation": {"status": "reference_only",
                                  "checked_files": ["_学习/题材归位_20260922.json"], "use": "仅核验字段结构, 不继承催化。"},
    },
    "missing_fields": {"global": [] if reasons else ["20260923当日THS涨停原因"],
                       "by_code": {c: ["催化"] for c in missing}},
    "counts": {
        "zt_pool_rows": len(rows),
        "summary_涨停家数": summary.get("涨停家数"),
        "映射数量": len(mp),
        "覆盖缺口": len(missing),
        "来源档": {"A": 0, "B": len(mp), "C": 0},
        "催化缺口数量": sum(1 for v in mp.values() if not v["催化"]),
        "大方向分布": dict(Counter(v["大方向"] for v in mp.values()).most_common()),
    },
    "A": 0, "B": len(mp), "C": 0,
    "档计数": {"A": 0, "B": len(mp), "C": 0},
    "来源明细": ["20260923/zt_pool.csv", "20260923/summary.json", "_学习/涨停原因_20260923.json"],
}
p = os.path.join(L, "题材归位_%s.json" % D)
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("题材归位生成:", p, len(mp), "只; 催化缺口", out["counts"]["催化缺口数量"], "; summary涨停家数", zh)
print("大方向分布:", json.dumps(out["counts"]["大方向分布"], ensure_ascii=False))
