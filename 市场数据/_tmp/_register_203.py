from pathlib import Path

root = Path(r'D:/股票数据/市场数据')
ledger = root / '_变更总账.md'
entry = r'''

---

## #203 | 2026-09-23 | 概览页黄金版 round2 修复与锚点收口

- **范围**: 仅概览页结果层与其长期结构门禁；不改黄金对照目录，不改其它六页业务判断，不发布现网。
- **用户修订**:
  1. 补回基于当日留档数据的概览走马灯；
  2. 概览不展示「机器数据核对层」与「本页阅读」；
  3. Top5 `.obs` 卡恢复名称+代码显示；
  4. 拐点预警继续按黄金版 `rowC + rail` 并入段一，不恢复独立大段；
  5. 来源审计/编辑说明退出概览结果层，原文、证据与内部锚点继续留在体系内。
- **防复发修复**: 页面结果层不显示机器折叠，但 `IDXTEMP/IDXLEAD/IDXVOTE` 隐藏锚点各保留开闭一对；被并入右栏的 `turning` 保留 hidden、aria-hidden 的结构性 section/h2 与黄金标记，满足结构合同而不改变可见版式。
- **涉及文件**: `review_pages.py`、`module_golden_index.py`、`review_publish.py`、`复盘一致性哨兵.py`；`_架构/组件快照_index.json` 按确认后的黄金结构重新落库。
- **实测**: 概览专测 `15 passed`；`py_compile` 通过；候选重建 status=ok；候选 index `rowC=1`、`rail=1`、Top5 `.obs=5`、能力模块=2；机器锚点和四个黄金标记均成对；禁止可见组件计数为0；快照 `init --index` 后 `check --index` 通过。全量 pytest 与生产发布另行记录，不在未完成时宣称通过。
- **发布状态**: 未发布；正式页仍需全量回归、P1/P2/P3、发布后 C1-C28/C15 与 HTTP 读回。
'''
text = ledger.read_text(encoding='utf-8')
assert '## #203 |' not in text
ledger.write_text(text.rstrip() + entry + '\n', encoding='utf-8', newline='\r\n')
print('OK ledger #203')
print('mtime', ledger.stat().st_mtime_ns)
