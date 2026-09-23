# -*- coding: utf-8 -*-
"""2026-09-23 #202 概览页黄金骨架锁: 变更总账 + 链路地图 登记(三合一SOP第1步)。

只做文本登记, 不改任何脚本逻辑; 运行后打印差异摘要供人工核对。
"""
from pathlib import Path

MKT = Path("D:/股票数据/市场数据")

# ── 1. _变更总账.md 追加 #202 ────────────────────────────────────────────────
LEDGER = MKT / "_变更总账.md"
entry = """
---

## #202 | 2026-09-23 | 概览页黄金骨架锁(用户拍板: 每次复盘样式不得漂移)

- **动机**: 用户投诉「概览页修过一回, 修完又复盘两次, 样式又全变了」。取证: 同一修好版本连跑两天, 9/21 发出版 index 113KB/78 条判断卡 → 9/22 240KB/279 条判断卡(体量翻倍)。根因 = 概览页是七页里**唯一没有黄金视觉锁**的页面, 段落/卡片形态由总审正文与判断卡数量决定, 内容一涨版式就漂。
- **用户拍板口径(不得自行更改)**: 概览 = **黄金四段(段序冻结) + 两块能力进化模块 = 6 段**; 「明日观察点」不单独成段, 用黄金 `.obs` 形态渲染 Top5(保留跨路筛选能力, 形态归黄金); **只保留 Top5**, Master 综合/阅读条不再上页; 279 条判断卡**退出展示层但一条不删**(复盘体系内部保留); 锁 = 概览单页黄金锁 + 契约自检 + 哨兵 C15 + 快照回归。
- **改了什么**:
  1. **新增 `module_golden_index.py`(唯一真源)**: 概览四段骨架只此一处生产, 只吃页面模型、不读新文件; 段序 一 明日核心观察点(`.obs` 卡×Top5) / 二 拐点预警·命门温度背离 / 三 五路看牌(`.routes > .rt`×5) / 四 总裁决·自主进化(`.hb`×6 + 裁决卡); 每段包 `<!--GOLDEN-INDEX:<id>-->` 机器标记。
  2. `review_pages.py`: 概览路由改调黄金骨架; 新增 `GOLDEN_INDEX_ON`(**由契约段序决定**, 仅当契约声明黄金四段才启用 → 冻结集成根/历史契约的旧渲染路径不受影响); 契约不符即 `ValueError` → `build_site` fail-closed **不写候选页**; 概览撤阅读条、结果层不放判断卡, claim 原文进页尾无痕原文库。
  3. `_契约/页面契约.v1.json`: `routes.index.sections` → 黄金四段(段序冻结)。
  4. `能力进化模块.py`: `BUSINESS_SECTIONS['index']=4`(两块能力模块编号自「五/六」顺延, 否则注入即报错)。
  5. `复盘一致性哨兵.py`: **新增 C15 概览黄金骨架**(契约段序/段标记唯一/业务段数/无判断卡/无阅读条/五锚点成对/`.obs`≤5)。
  6. `组件级快照回归.py`: 新增 `--index`, 概览四段结构指纹快照(合成样本驱动 → 只锁模板结构, 内容日更不误报)。
  7. `tests/`: `test_review_pages.py`(EXPECTED 段序)、`test_review_pages_layout.py`、`test_review_pages_v42_production.py`(概览改锁黄金四段标记, 页内导航改锁 page-map JS 生成器)、`test_review_pages_review.py`(观察点断言改为「黄金骨架在场 + 判断卡不上页 + 原文留痕」)同步合同。
- **实测验证**: `build_site(20260922)` status=ok; 候选页(index) **211KB / h2=6 / 黄金标记=4 / `class="citem"`=0 / `.obs`=5 / `.hb`=6 / 能力模块=2 / 五锚点各 1:1 成对 / `claim-anchor-bank` 在场**; 部署后处理 `_sync_capability_blocks` 七页注入后标记与段序不变; **哨兵 C15 PASS(候选页)**; **高危边#E3 复测**: `竞价上首页.inject_obs` 仍解析 5/5 只票且二次注入幂等(obs-jj 块 5), `竞价快线.parse_watchlist` 正常返回; 快照回归 `--index` init/check/selftest 全 PASS(结构改动必被抓/文本改动不误报)。
- **回归基线(A/B 实测)**: 把 `GOLDEN_INDEX_ROUTES` 临时置空复跑 → 归因清楚: `test_gate_repair_scoped`(5 errors)、`test_review_pages_review`(3 KeyError) 由本轮黄金守卫误伤旧契约根, 已用契约段序开关修掉; **`test_review_pages_reco_wiring`(2)、`test_gate_repair_followup`(2) 在改动前即失败**(theme 荐票源定位/cycle VOTEBOARD), 属既有欠账, 本轮未动。
- **影响面**: 只动概览路由, 其余六页零影响; 未改任何判断结论或数字。
- **发布状态**: **未发布** —— 现网 `复盘/盯盘台/index.html` 仍是旧版(8 段/279 卡), 重发需用户放行(`生成盯盘台.py 20260922` → P1/P2/P3 → 部署 → 哨兵全项)。
- **级别**: 大改(新增页面渲染真源 + 页面结构变更 + 契约/规则同步)。
"""
s = LEDGER.read_bytes().decode("utf-8").replace("\r\n", "\n")
assert "#202" not in s, "ledger already has #202"
if not s.endswith("\n"):
    s += "\n"
LEDGER.write_bytes((s + entry).replace("\n", "\r\n").encode("utf-8"))
print("OK _变更总账.md += #202")

# ── 2. _链路地图.md: 版本戳 + 页面层节点 + 〇.3 节点块 ──────────────────────
MAP = MKT / "_链路地图.md"
m = MAP.read_bytes().decode("utf-8").replace("\r\n", "\n")

old_ver = "> 版本戳: v1.14 | 2026-07-16 建立; v1.14(2026-09-23 #202: 八项遗留机制一次性收口"
new_ver = ("> 版本戳: v1.15 | 2026-07-16 建立; v1.15(2026-09-23 #202: **概览页黄金骨架锁**——"
           "新增唯一真源 `module_golden_index.py`(概览四段段序冻结+每段 `<!--GOLDEN-INDEX:id-->` 标记), "
           "`review_pages.py` 概览路由改调它且 `GOLDEN_INDEX_ON` 由契约段序决定(冻结集成根不受影响)、契约不符即 fail-closed 不写候选, "
           "契约段序/能力模块编号/哨兵 **C15**/快照回归 `--index`/P1 测试同步; 不动其他六页); "
           "v1.14(2026-09-23 #201: 八项遗留机制一次性收口")
assert m.count(old_ver) == 1, "version anchor"
m = m.replace(old_ver, new_ver)

row_anchor = "改动页段数必须同步此表否则注入即报错 |\n"
assert m.count(row_anchor) == 1, "page-layer row anchor"
new_row = ("| **概览页黄金骨架(`module_golden_index.py` 唯一真源)** | "
           "`module_golden_index.py`(2026-09-23 #202 新建; 只吃页面模型, 不读新文件) | "
           "`review_pages.py::_render`(index 路由) + `_契约/页面契约.v1.json` routes.index.sections + "
           "`能力进化模块.py::BUSINESS_SECTIONS['index']=4` + `复盘一致性哨兵.py` **C15** + "
           "`组件级快照回归.py --index` + `tests/test_review_pages*.py` | "
           "**概览骨架四段段序冻结**: 一 明日核心观察点(跨路 Top5 用黄金 `.obs` 卡) / 二 拐点预警·命门温度背离 / "
           "三 五路看牌(`.routes .rt`×5) / 四 总裁决·自主进化(`.hb`×6); 每段必须带 `<!--GOLDEN-INDEX:id-->` 标记; "
           "`GOLDEN_INDEX_ON` 只由契约段序决定(契约=黄金四段才启用); 契约不符 → `build_site` fail-closed **不写候选**; "
           "结果层禁止判断卡(`class=\"citem\"`=0)与阅读条, claim 原文进页尾无痕原文库一条不删; "
           "**改 `.obs` 卡结构必同步复测高危边#E3 两个 parser**(`竞价上首页.inject_obs`/`竞价快线.parse_watchlist`), 否则晨场静默 0 只 |\n")
m = m.replace(row_anchor, row_anchor + new_row)

o3_anchor = "## 四、规则文件三处联动(改规矩必同步)\n"
assert m.count(o3_anchor) == 1, "O3 anchor"
o3 = """## 〇.3 2026-09-23 #202 概览黄金骨架节点

| 节点 | 真源 | 不变量 / 改它必检 |
|---|---|---|
| 概览四段骨架 | `module_golden_index.py`(唯一真源) | 段序=一 明日核心观察点 / 二 拐点预警·命门温度背离 / 三 五路看牌 / 四 总裁决·自主进化; 只吃页面模型, 不新增数据读取 |
| 段落机器标记 | 同上, 每段包 `<!--GOLDEN-INDEX:<id>-->` | 缺标记/缺段 = `review_pages.build_site` 抛错 fail-closed, 不写候选页; 哨兵 C15 逐段核对标记唯一性 |
| 契约段序 | `_契约/页面契约.v1.json` → `routes.index.sections` | 必须恒等于黄金四段; 改契约=改锁, 必须同时改 C15/快照/P1 测试并有用户拍板 |
| 概览启用开关 | `review_pages.py` → `GOLDEN_INDEX_ON` | 由契约段序决定, 不是 `route=='index'`: 冻结集成根/历史契约(observations/master)继续走旧渲染, 不被锁误伤 |
| 能力模块编号 | `能力进化模块.py::BUSINESS_SECTIONS['index']=4` | 概览业务段数改 4 后能力模块从「五/六」顺延; 不同步=注入即报错 |
| 判断卡退场 | 结果层 `class="citem"` 必须为 0 | 证据不删: claim 原文/锚点进页尾无痕原文库(`claim-anchor-bank`)+来源审计折叠, 页面不可见但门禁可复核 |
| 晨场解析兼容 | `竞价上首页.inject_obs` / `竞价快线.parse_watchlist` | 见高危边#E3: 动 `.obs` 卡 markup 必跑 `_tmp` 回归实测(5/5 只票 + 注入幂等), 否则晨场「今晨竞价」全 `—` |

"""
m = m.replace(o3_anchor, o3 + o3_anchor)

MAP.write_bytes(m.replace("\n", "\r\n").encode("utf-8"))
print("OK _链路地图.md: 版本戳 v1.15 + 页面层节点行 + 〇.3 块")
