# -*- coding: utf-8 -*-
"""向 _变更总账.md 幂等追加 20261023 出页门禁修复条目（编号取 max+1）。"""
import os, re

os.chdir(r"D:\股票数据\市场数据")
p = "_变更总账.md"
raw = open(p, encoding="utf-8").read()
nums = [int(x) for x in re.findall(r"^## #(\d+)", raw, re.M)]
n = max(nums) + 1 if nums else 1

entry = f"""## #{n} 20261023 出页门禁修复（6 项，全部零语义改动/只修口径与写法）
1) **台账证据修正**：`_学习/_竞价池结算.jsonl` 的 `池日=20261022` 行原为占位坏值（次日封板 0/13、执行胜率 0/0、执行均收 null），导致 C9 `previous_pool_check` 直接 fail；用 `竞价池结算_20261022.json#汇总` 真实值替换（封板 4/13、执行胜率 6/13、均收 -0.26%、全场 +3.26%、增益 -3.52pp），原件留 `.bak_20261023`。**机制隐患**：`竞价池结算.py` 在 T+1 行情未到时先落盘占位行，`_jsonl_append` 幂等按池日去重，后续真实结算无法覆盖 → 待改为「占位标记 + 允许升级」。
2) **日历口径**：`20261024`（周六非交易日）→ `20261026` 共 20 处、8 文件（auction/lhb body + 判断 + 交易计划），全部留 `.bak_cal`。根因：五路 agent 把「明日」写成 T+1 自然日而非下一交易日。
3) **auction body 实体归一**：`&lt;`/`&gt;` 38 处 → 全角 `＜`/`＞`。根因：DOM 抽取的 claim 文本是 `<`，`canonical_text` 不解码实体，`review_publish.py:1622` 报 `legacy claim absent from source`（与 20261015 先例同型）。
4) **limitup body 门禁写法**：①推荐表 `<td>0</td><td>连板≥5×炸≥2` 剥标签后成「观察0连板≥5」，被高标口径正则读成「海洋王 0 板（真实 6 板）」→ 加「桶：」断开；②hero「温度 11.2→53.2」被元信息温度引用正则取到 11.2（温度表 53.2）→ 改「温度 53.2（昨 11.2）」。
5) **组装层温度口径归一**：`_tmp/build_judgment_20261023.py` 对「温度X→Y」统一改写为「温度Y（昨X）」，总审原件不动，只在组装时归一。
6) **补生产命名产物**：`_学习/周期主判_20261023.json`（由 cycle agent 归档件转写，10 键对齐 20261022）+ `周期投票牌_20261023.html`（五路票 修复3/高潮1/发酵1，复议 false、反对路 0）。cycle agent 只写了 `cycle判断_*.json`（非生产命名）导致 `周期投票.py tally` 与 index 页 `IDXVOTE` 双缺。
出页结果：`published=true`、`releases/20261023-1-59104d1139274c1f9858d0faff1bee85`、7 页 × 1440/390 浏览器全过、一致性哨兵 C1-C15 全过（1 警告 C4 002626 bars 未到）。

"""
open(p, "a", encoding="utf-8", newline="\n").write(entry)
print("追加 #%d | 现在最大编号 %d" % (n, n))
print(entry[:200])
