# -*- coding: utf-8 -*-
"""20261015 收口-正文缺陷修复（宿主；最小改动 + 备份 + 回读校验）
背景: 生成盯盘台.py 20:39 发布被门禁拦下, 四条阻断里三条源自正文:
 1. auction: auction-1c7f18c7c9f9d360 claim 归一化不对称 —— 正文用 HTML 实体写占位符
    `&lt;d&gt;`, 去标签后成字面 `<d>`; 而 claim 文本经二次 HTML 解析时 `<d>` 被当标签吃掉
    → 'legacy claim absent from source'。改=把占位符写成实际日期(零语义改动)。
 2. cycle : C1 禁 'null' 字面量 —— 正文写 `昨日涨停溢价=null（源未产出，不补造）`
    → 按用户口径 (无数据字段用"—") 改为 `溢价=—`。
 3. theme : 题材页荐票铁律 要求 bodies.theme 内代码∈当日 zt_pool —— 深挖段引用了
    20261014 指派时的 AI 短剧线名单 (002343/603533/603598), 其中 603533/603598
    当日已不在涨停池 → 补事实标注 (反事实语境), 不是荐票。
零编造: 只做符号/事实标注, 不改任何数字、结论、档位。
"""
import os, json, shutil, re, sys

R = r"D:\股票数据\市场数据"
os.chdir(R)
D = "20261015"
TAIL = ".bak_收口_20261015"

EDITS = {
    "_学习/cycle_body_%s.html" % D: [
        ("溢价=null", "溢价=—", 3),          # C1: null 字面量 → 无数据口径 "—"
    ],
    "_学习/auction_body_%s.html" % D: [
        ("&lt;d-1&gt;", "20261014", 1),        # d-1 = 前一交易日
        ("&lt;d&gt;", "20261015", 3),          # 占位符 → 实际日目录
    ],
    "_学习/theme_body_%s.html" % D: [
        ("（002343/603533/603598）", "（002343/603533/603598，后两只当日已不在涨停池）", 1),
        ("<b>603533掌阅科技</b>", "<b>603533掌阅科技（不在当日涨停池）</b>", 1),
        ("<b>603598引力传媒</b>", "<b>603598引力传媒（不在当日涨停池）</b>", 1),
    ],
}

rc = 0
for path, rules in EDITS.items():
    if not os.path.exists(path):
        print("[FAIL] 缺文件", path); rc = 1; continue
    src = open(path, encoding="utf-8").read()
    bak = path + TAIL
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    out = src
    for old, new, expect in rules:
        n = out.count(old)
        print("[%s] 替换 %-28r -> %-22r  命中=%d (期望%d)" % (
            os.path.basename(path), old, new, n, expect))
        if n != expect:
            print("   [WARN] 命中数不符, 仍继续(逐条幂等)")
        out = out.replace(old, new)
    if out != src:
        open(path, "w", encoding="utf-8", newline="").write(out)
        print("   [WRITE] %s  %d -> %d chars" % (os.path.basename(path), len(src), len(out)))
    # 回读校验
    chk = open(path, encoding="utf-8").read()
    bad = []
    if path.endswith("auction_body_%s.html" % D) and ("&lt;d&gt;" in chk or "&lt;d-1&gt;" in chk):
        bad.append("仍有实体占位符")
    if path.endswith("cycle_body_%s.html" % D) and "溢价=null" in chk:
        bad.append("仍有 溢价=null")
    if path.endswith("theme_body_%s.html" % D):
        for c in ("603533", "603598"):
            if not any(("不在" in chk[max(0, m.start() - 25):m.start() + 30]) for m in re.finditer(c, chk)):
                bad.append("代码 %s 缺反事实标注" % c)
    print("   [VERIFY]", "OK" if not bad else "FAIL " + "; ".join(bad))
    if bad:
        rc = 1
print("[DONE] rc=%d" % rc)
sys.exit(rc)
