# -*- coding: utf-8 -*-
p = r"D:\股票数据\市场数据\_变更总账.md"
entry = (
"\r\n\r\n## #085 四条结算脚本jsonl裸append补去重门禁+历史重复清理 (2026-08-16)\r\n"
"- 动机: 四条结算脚本(质量/题材/逻辑/席位)的 jsonl 追加全是裸 append 无去重, 同日重复跑会重复样本污染下游统计/训练/权重重训(#053附记曾报历史重复)。\r\n"
"- 改了什么:\r\n"
"  1. 新增 _jsonl_append.py 共享模块: append_dedup(path,obj,keys) 按 key 去重追加(幂等), keys='荐票日' 或 ('荐票日','代码')。\r\n"
"  2. 质量荐票结算.py: 3处append改append_dedup(_荐票逐票结算.jsonl用(荐票日,代码), _涨停质量反思/_质量荐票结算用荐票日)。\r\n"
"  3. 题材荐票结算.py: 2处(_题材荐票结算/_题材荐票反思, 荐票日)。\r\n"
"  4. 逻辑荐票结算.py: 2处(_逻辑荐票结算/_逻辑荐票反思, 荐票日)。\r\n"
"  5. 席位荐票结算.py: 1处(_席位荐票反思, 荐票日)。\r\n"
"  6. 清理8个jsonl历史重复78行(保序去重保留第一条, 备份至_tmp/jsonl_bak_20260816/)。\r\n"
"- 验证: 四脚本+_jsonl_append py_compile OK; append_dedup幂等测试(临时文件True/False/True + 真实jsonl对已有荐票日返回False文件不变)全PASS; 端到端跑质量荐票结算.py 20260813(.venv312)正常结算+台账重组装, jsonl行数不变(50/10/10)=去重生效; 下游消费方(module_render_limitup/logic, 五路战绩画像, 自主拓展扫描)均json.loads逐行读, 删重+LF无影响。\r\n"
"- 级别: 小改(追加方式去重化+历史清理, 结算口径/字段不变)。\r\n"
"- 遗留: ①五路战绩画像.py 读的席位文件是_龙虎榜荐票结算.jsonl(非席位荐票结算.py写的_席位荐票反思.jsonl), 命名不一致待核(非本次范围)。②历史jsonl删78行重复=丢重复跑次数信息, 但样本更干净。\r\n"
)
with open(p, "a", encoding="utf-8", newline="") as f:
    f.write(entry)
print("已追加 #085")
