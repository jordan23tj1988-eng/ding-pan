# -*- coding: utf-8 -*-
"""构建 题材归位_20261020.json —— agent 逐只语义归位（唯一真源）。
来源档: A=公告级(公告催化补充文件) / B=THS涨停原因原文 / C=行业兜底(无THS原因)
不继承上一交易日内容；不凭记忆补写。
"""
import json, csv, os, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = "20261020"
L = os.path.join(BASE, "_学习")

reason_path = os.path.join(L, "涨停原因_%s.json" % D)
reasons = json.load(open(reason_path, encoding="utf-8"))
rmap = reasons["映射"]
ann_path = os.path.join(L, "公告催化补充_%s.json" % D)
has_ann = os.path.exists(ann_path)

rows = list(csv.DictReader(open(os.path.join(BASE, D, "zt_pool.csv"), encoding="utf-8-sig")))

# code -> (大方向, 环节)
CLS = {
    "600148": ("军工", "军工AMT传动+新能源汽车零部件"),
    "002596": ("海南自贸港", "商品混凝土+智算布局+市政环卫"),
    "603893": ("端侧AI", "端侧AI SoC芯片+机器人"),
    "605177": ("医药", "头孢类原料药+制剂获批"),
    "002929": ("AI算力", "算力网络施工运维+境外词元大单"),
    "688608": ("AI眼镜", "低功耗SoC+AI眼镜+智能可穿戴"),
    "688004": ("AI内容安全", "AI内容安全+视听大数据+传媒安全"),
    "300244": ("医药", "AI病理+医学检验+业绩增长"),
    "603636": ("传媒短剧", "AI短剧+政务智能体+游戏出海"),
    "603366": ("绿电储能", "空气能热泵+储能+太阳能光热"),
    "002696": ("消费农业", "水产饲料+鱼粉涨价+青岛国资"),
    "002076": ("量子科技", "LED封装+量子科技+信息安全"),
    "603341": ("AI眼镜", "AI眼镜+AI PC+智能终端代工"),
    "603683": ("机器人", "人形机器人柔性传感+胶粘材料"),
    "002940": ("医药", "创新药+集采拟中选"),
    "603400": ("机器人", "机器人零部件+液冷电子水泵"),
    "002403": ("机器人", "人形机器人+工业机器人+炊具小家电"),
    "603657": ("机器人", "家庭机器人+清洁电器+小米客户"),
    "603696": ("消费农业", "复合调味品+对台贸易+业绩增长"),
    "001288": ("机器人", "矿山机器人+输送机械+华为合作"),
    "001388": ("物理AI", "物理AI+除冰机器人+具身智能+电力巡检"),
    "001283": ("电池", "消费电子电池+机器人电池+AI眼镜+三季报预增"),
    "603068": ("端侧AI", "端侧AI无线芯片+AIoT量产"),
    "605389": ("机器人", "AGV减速器+液压元件+回购提议"),
    "603407": ("电子材料", "锆基材料+半导体材料"),
    "002881": ("物理AI", "高算力模组+物理AI+光通信"),
    "300115": ("机器人", "人形机器人结构件+消费电子+AI算力"),
    "002242": ("机器人", "机器人投资+厨房小家电"),
    "603236": ("端侧AI", "端侧AI通信模组+机器人+业绩增长"),
    "300466": ("机器人", "工业机器人+智能装备+AI应用"),
    "603119": ("机器人", "人形机器人云母制品+精密结构件"),
    "603626": ("机器人", "机器人结构件+苹果供应链"),
    "001239": ("重组", "盾构机+风电+重组"),
    "003029": ("数字安全", "低空安全+人工智能安全+商用密码"),
    "002164": ("机器人", "机器人减速器小批量供货+股东增持"),
    "301313": ("物理AI", "物理AI数据+具身仿真+数字孪生"),
    "600860": ("机器人", "机器人集成+气体储运+氢能装备"),
    "002313": ("机器人", "无线模组+机器人应用+股权调整"),
    "002347": ("机器人", "工业机器人+冶金装备"),
    "002724": ("军工", "专业照明+AI照明+军工"),
    "603386": ("PCB", "PCB+AI算力+人形机器人+业绩增长"),
    "002088": ("锂电材料", "锂电隔热+陶瓷纤维"),
    "600267": ("医药", "宠物药+受托生产+业绩增长"),
    "002181": ("传媒短剧", "微短剧+AI内容+媒体经营"),
    "605488": ("机器人", "人形机器人柔性传感器+功能性涂布"),
    "002479": ("有色回收", "有色回收+热电联产+业绩增长"),
    "001323": ("端侧AI", "智能睡眠+端侧智能+鸿蒙生态"),
    "603278": ("机器人", "人形机器人+胎圈钢丝"),
    "600293": ("重组", "重大重组+锂电电解液+汽车电子玻璃"),
    "600178": ("低空经济", "飞行汽车+增程动力+定点协议+兵装重组"),
    "600661": ("教育", "教育培训+银发经济+业绩增长"),
    "002835": ("AI安防", "视频监控+AI安防+海外业务+AI ISP"),
    # 无THS原因 → 行业兜底 C档
    "920641": ("LED照明", "照明设备（行业兜底，无当日THS原因原文）"),
    "920096": ("机器人", "自动化设备（行业兜底，无当日THS原因原文）"),
}

SRC_B = ("B档：依据%s当日同花顺涨停原因原文（_学习/涨停原因_%s.json，渠道=同花顺涨停池，"
         "证据级别=THS编辑聚合）作题材归类；未发现公告级证据，不标A档。") % (D, D)
SRC_C = ("C档：%s当日无同花顺涨停原因原文（北交所标的未收录于THS池），仅按所属行业兜底归类，"
         "不得作为题材证据。")

mapping = {}
A_list, B_list, C_list = [], [], []
missing = []
for r in rows:
    code = r["代码"]
    name = r["名称"].replace(" ", "")
    ind = r.get("所属行业", "")
    lb = r.get("涨停统计", "") or ""
    first = (r.get("首次封板时间") or "").strip()
    first_fmt = ("%s:%s:%s" % (first[0:2], first[2:4], first[4:6])) if len(first) == 6 else first
    if code in rmap:
        big, seg = CLS.get(code, (ind or "待归位", ind))
        cat = rmap[code]["原因"]
        item = {
            "代码": code, "名称": name, "大方向": big, "环节": seg,
            "催化": cat, "催化状态": "THS涨停原因原文（同花顺涨停池）",
            "来源档": "B", "来源说明": SRC_B,
            "所属行业": ind,
            "连板口径": "首板" if r.get("连板数") == "1" else "%s天%s板" % (r.get("连板数"), r.get("连板数")),
            "首封": first_fmt,
        }
        B_list.append(code)
    else:
        big, seg = CLS.get(code, (ind or "待归位", ind))
        item = {
            "代码": code, "名称": name, "大方向": big, "环节": seg,
            "催化": "无当日THS原因原文", "催化状态": "行业兜底（无原因原文）",
            "来源档": "C", "来源说明": SRC_C % D,
            "所属行业": ind,
            "连板口径": "首板" if r.get("连板数") == "1" else "%s天%s板" % (r.get("连板数"), r.get("连板数")),
            "首封": first_fmt,
        }
        C_list.append(code)
        missing.append({"代码": code, "名称": name, "缺口": "THS涨停原因原文缺失（北交所未收录），已按行业兜底"})
    mapping[code] = item

agg = collections.OrderedDict()
for code, it in sorted(mapping.items(), key=lambda kv: -int([r for r in rows if r["代码"] == kv[0]][0].get("连板数") or 1)):
    agg.setdefault(it["大方向"], []).append(code)

obj = {
    "日期": D,
    "来源": "%s/zt_pool.csv；_学习/涨停原因_%s.json（同花顺涨停原因）；%s" % (
        D, D, ("_学习/公告催化补充_%s.json（公告催化线索）" % D) if has_ann else "无公告催化补充文件（A档=无）"),
    "口径": ("逐只覆盖%s/zt_pool.csv全量%d只涨停股；以当日THS涨停原因原文归类题材（大方向/环节为对该原文的归纳）；"
             "无公告级证据文件不标A；无THS原因原文的个股仅按所属行业兜底并在missing_fields点名；不继承上一交易日题材内容。"
             % (D, len(rows))),
    "source_status": "pass" if len(mapping) == len(rows) else "partial",
    "missing_fields": [m["代码"] for m in missing],
    "missing_detail": missing,
    "counts": {"total": len(rows), "mapped": len(mapping)},
    "A": A_list, "B": B_list, "C": C_list,
    "档计数": {"A": len(A_list), "B": len(B_list), "C": len(C_list)},
    "来源明细": {
        "A": "无公告级证据文件（_学习/公告催化补充_%s.json %s），本批无A档。" % (D, "存在但未用于升级" if has_ann else "不存在"),
        "B": "%d只均有%s当日同花顺涨停原因原文（_学习/涨停原因_%s.json，渠道=同花顺涨停池，证据级别=THS编辑聚合），按原因语义归类；不将行业兜底或题材推断升级为公告证据。" % (len(B_list), D, D),
        "C": "%d只（THS原因覆盖率 %d/%d=%.0f%%，行业兜底档：%s）。" % (
            len(C_list), len(B_list), len(rows), 100.0 * len(B_list) / len(rows),
            "、".join("%s %s" % (c, mapping[c]["名称"]) for c in C_list) or "无"),
    },
    "方向聚合": agg,
    "映射": mapping,
}

out = os.path.join(L, "题材归位_%s.json" % D)
json.dump(obj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", out)
print("total", len(rows), "mapped", len(mapping), "A/B/C", len(A_list), len(B_list), len(C_list))
for k, v in agg.items():
    print("  %-10s %d" % (k, len(v)))
