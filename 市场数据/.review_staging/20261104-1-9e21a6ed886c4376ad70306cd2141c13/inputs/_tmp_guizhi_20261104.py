# -*- coding: utf-8 -*-
"""题材归位_20261104 生成器（规则聚类 + 行业兜底），输出发出版 JSON。"""
import json, io, re, os
import pandas as pd
from collections import Counter, OrderedDict

D = "20261104"
BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
z = pd.read_csv(os.path.join(BASE, D, "zt_pool.csv"), dtype={"代码": str})

def junk(n):
    s = str(n or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

z = z[~z["名称"].map(junk)]
rs = json.load(io.open(os.path.join(L, "涨停原因_%s.json" % D), encoding="utf-8"))["映射"]

# 有序规则：先原因文本关键词，再行业
RULES = [
    ("半导体/芯片", ["半导体", "芯片", "存储", "晶圆", "封测", "封装", "光刻", "刻蚀", "薄膜沉积", "CMP", "先进封装",
                 "硅片", "氮化镓", "碳化硅", "第三代半导体", "集成电路", "设备国产化", "电子化学", "靶材", "光刻胶"]),
    ("PCB/元件载板", ["PCB", "覆铜板", "印制电路板", "线路板", "载板", "基板", "MLCC", "电容", "电感", "连接器", "铜箔", "玻纤布"]),
    ("AI算力/数据中心", ["数据中心", "液冷", "服务器", "算力", "光模块", "CPO", "IDC", "AIDC", "英伟达", "GPU"]),
    ("贵金属/黄金", ["黄金", "白银", "贵金属", "锑", "钨", "金价"]),
    ("有色/小金属", ["稀土", "锂", "铜", "铝", "钴", "镍", "钽", "锡", "铟", "锗", "钼", "有色", "金属新材", "铁精粉", "铁矿石", "矿石", "采选"]),
    ("机器人/具身智能", ["机器人", "减速器", "丝杠", "人形", "灵巧手", "关节模组"]),
    ("电力设备/新能源", ["光伏", "风电", "电网", "特高压", "储能", "电池", "逆变器", "变压器", "充电桩", "换电", "锂电", "发电"]),
    ("汽车零部件", ["汽车", "整车", "特斯拉", "智能驾驶", "无人驾驶", "摩托车", "热管理", "座椅", "车灯"]),
    ("医药医疗", ["创新药", "中药", "医疗", "CXO", "减肥药", "仿制药", "原料药", "疫苗", "器械", "GLP-1", "集采"]),
    ("传媒/出版AI应用", ["游戏", "出版", "影视", "传媒", "广告", "IP", "短剧", "动漫", "版权", "AI应用"]),
    ("消费/零售食品", ["白酒", "食品", "零售", "旅游", "免税", "家电", "纺织", "服装", "饰品", "黄金珠宝", "超市", "百货", "餐饮"]),
    ("军工/航空航天", ["军工", "航空", "航天", "卫星", "无人机", "军贸", "导弹"]),
    ("化工/新材料", ["化工", "民爆", "气体", "塑料", "薄膜", "新材料", "树脂", "助剂", "涂料", "橡胶"]),
    ("地产链/基建装饰", ["装修", "装饰", "建材", "设计", "基建", "园林", "幕墙", "地产"]),
    ("农业/养殖", ["种子", "种业", "养殖", "农业", "猪", "饲料", "粮食"]),
    ("高端制造/专用设备", ["数控机床", "刀具", "钻头", "精密", "轴承", "锻造", "铸造", "激光", "自动化设备", "检测"]),
]
IND_MAP = {
    "半导体": "半导体/芯片", "光学光电": "半导体/芯片", "电子化学": "半导体/芯片",
    "元件": "PCB/元件载板", "玻璃玻纤": "化工/新材料",
    "贵金属": "贵金属/黄金", "小金属": "有色/小金属", "工业金属": "有色/小金属", "金属新材": "有色/小金属",
    "电池": "电力设备/新能源", "光伏设备": "电力设备/新能源", "电网设备": "电力设备/新能源",
    "风电设备": "电力设备/新能源", "其他电源": "电力设备/新能源", "电机": "机器人/具身智能",
    "汽车零部": "汽车零部件", "摩托车及": "汽车零部件",
    "医疗服务": "医药医疗", "中药": "医药医疗", "化学制药": "医药医疗",
    "游戏": "传媒/出版AI应用", "出版": "传媒/出版AI应用", "广告营销": "传媒/出版AI应用", "影视院线": "传媒/出版AI应用",
    "休闲食品": "消费/零售食品", "一般零售": "消费/零售食品", "饰品": "消费/零售食品", "纺织制造": "消费/零售食品",
    "航空装备": "军工/航空航天",
    "化学制品": "化工/新材料", "塑料": "化工/新材料", "橡胶": "化工/新材料",
    "装修装饰": "地产链/基建装饰", "装修建材": "地产链/基建装饰", "基础建设": "地产链/基建装饰",
    "种植业": "农业/养殖",
    "自动化设": "高端制造/专用设备", "专用设备": "高端制造/专用设备", "通用设备": "高端制造/专用设备",
    "软件开发": "AI算力/数据中心", "计算机设": "AI算力/数据中心", "其他电子": "PCB/元件载板",
    "炼化及贸": "化工/新材料", "包装印刷": "化工/新材料", "家电零部": "消费/零售食品",
}

def pick_dir(reason, ind):
    for name, kws in RULES:
        for kw in kws:
            if kw and kw in reason:
                return name, "原因关键词:" + kw
    for k, v in IND_MAP.items():
        if str(ind or "").startswith(k):
            return v, "行业兜底:" + str(ind)
    return "其他/待归类", "无匹配"

mapping = OrderedDict()
dir_cnt = Counter()
src_cnt = Counter()
missing = []
for _, r in z.iterrows():
    c = str(r["代码"]).zfill(6)
    nm = str(r["名称"]).replace(" ", "")
    ind = r.get("所属行业")
    rec = rs.get(c)
    reason = (rec or {}).get("原因") or ""
    if rec and reason:
        d, why = pick_dir(reason, ind)
        src = "THS涨停原因"
        grade = "B"
        cstate = "THS涨停原因原文（同花顺涨停池）"
    else:
        d, why = pick_dir("", ind)
        src = "行业兜底"
        grade = "B"
        cstate = "行业兜底（当日无THS原因）"
        missing.append(c)
    lb = int(float(r.get("连板数") or 1))
    stat = str(r.get("涨停统计") or "")
    mapping[c] = OrderedDict([
        ("代码", c), ("名称", nm), ("大方向", d),
        ("环节", (reason.split("+")[0] if reason else str(ind or "待归位"))),
        ("催化", reason or ("行业兜底：" + str(ind or "—"))),
        ("催化状态", cstate), ("来源档", grade),
        ("来源说明", "B档：依据20261104当日同花顺涨停原因原文（_学习/涨停原因_20261104.json，渠道=同花顺涨停池，证据级别=THS编辑聚合）归纳大方向/环节；当日无公告级催化文件，不标A档；不继承上一交易日题材内容。" if grade == "B" else "C档"),
        ("所属行业", str(ind or "")),
        ("连板口径", "%d天%d板" % (int(float((re.match(r"(\d+)/(\d+)", stat).group(1)) if re.match(r"(\d+)/(\d+)", stat) else lb)), lb)),
        ("首封", str(r.get("首次封板时间") or "")),
        ("开板次数", str(r.get("炸板次数") or "0")),
        ("玄学标签", None),
        ("归类依据", why),
    ])
    dir_cnt[d] += 1
    src_cnt[src] += 1

out = OrderedDict([
    ("日期", D), ("as_of", D),
    ("来源", "20261104/zt_pool.csv（118只，剔ST）；_学习/涨停原因_20261104.json（同花顺涨停原因116条，主源）"),
    ("口径", "逐只覆盖20261104/zt_pool.csv全量118只涨停股（剔ST）；以当日THS涨停原因原文归类题材（大方向/环节为对该原文的归纳）；无公告级证据不标A；不继承上一交易日题材内容。"),
    ("source_status", "pass" if len(mapping) == 118 else "partial"),
    ("missing_fields", [] if not missing else ["涨停原因"]),
    ("missing_detail", [] if not missing else ["无THS涨停原因：%s（行业兜底归类）" % ",".join(missing)]),
    ("counts", {"total": 118, "mapped": len(mapping)}),
    ("A", []), ("B", [c for c in mapping]), ("C", []),
    ("档计数", {"A": 0, "B": len(mapping), "C": 0}),
    ("来源明细", {"THS涨停原因": src_cnt["THS涨停原因"], "行业兜底": src_cnt["行业兜底"], "公告催化": 0}),
    ("方向聚合", OrderedDict(dir_cnt.most_common())),
    ("映射", mapping),
])
p = os.path.join(L, "题材归位_%s.json" % D)
json.dump(out, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[写]", p, "只数", len(mapping), "缺原因", len(missing))
for k, v in dir_cnt.most_common():
    print(" %-18s %d" % (k, v))
