---
name: sentiment-memory-snapshot
description: 每天18:40把情绪复盘相关的Claude持久记忆导出成快照,存进市场数据供19:00 GitHub同步
backup_date: 2026-07-13晚(加任务二:技能备份自动刷新)
cron: 40 18 * * *
---

把你的持久记忆中【情绪复盘系统相关】的条目导出为一份快照文件,供用户的GitHub每日同步(19:00)留档。用中文。

## 任务一:记忆快照

### 选取范围
读你的记忆索引 MEMORY.md(在你的持久记忆目录,如 C:\Users\66353\AppData\Local\Claude-3p\local-agent-mode-sessions\a021c5d4\00000000\memory\memory\),动态选取所有与"情绪复盘系统"相关的记忆文件,包括但不限于:sentiment_* 系列、auction_pool_bucket_lib、logic_autonomous_expansion、mikai_corpus(只导体系/手册要点,语料本身不入库)、feedback_concurrent_overwrite、feedback_visual_review。以后新增的情绪复盘相关记忆(索引里含"情绪/复盘/盯盘台/竞价/席位/题材/涨停/模拟盘/温度/三窗"等关键词)也要纳入。
★排除铁律:自研战法(5分V6/V8/aAb/反转底b段)、缠论引擎/隧道画法、qlib、tdxrs 等私有策略记忆一律不导——目标仓库是公开的。

## 输出
- 目标文件(固定名,整体覆盖,历史靠git):`D:\股票数据\市场数据\_学习\_claude记忆快照\情绪复盘_Claude记忆快照.md`
- 文件头必须注明:导出日期、"真身在Claude应用记忆内,以真身为准;本快照每日自动刷新"、"私有策略记忆刻意未导出"。
- 结构:每条记忆一节(## 编号. 记忆名 — 一句话描述),保留原文关键内容(Why/How to apply/数据结论/铁律),可适度压缩重复叙述但不许改数字、不许编造。

## 写入方法(防挂载盘中文长文件截断,铁律)
1. 用 Write 工具把完整快照先写到你自己的 outputs 工作目录(不要直接 Write 到 D:\股票数据)。
2. 用 bash 把它 cp 到 /sessions/*/mnt/股票数据/市场数据/_学习/_claude记忆快照/情绪复盘_Claude记忆快照.md(目录不存在就 mkdir -p)。
3. 校验:bash 里比对源/目标字节数与 md5 一致,并 UTF-8 解码打印末行确认无截断。不一致必须重写,禁止留半截文件。


## 任务二:技能备份刷新(2026-07-13加,堵"手动刷会忘"的洞)
用 bash 把技能缓存字节级复制到GitHub同步区并校验:
`cp /sessions/*/mnt/.claude/skills/sentiment-review-system/SKILL.md /sessions/*/mnt/股票数据/同步GitHub/_extras/skill/sentiment-review-system/SKILL.md`(目标只读先chmod u+w;复制后md5比对+UTF-8解码末行验完整;若源缓存疑似截断则跳过并在通知里报警,禁止用坏源覆盖好备份)。通知里报技能版本号。

## 收尾
一句话通知用户:快照已刷新(共N条记忆/字节数/较昨日有无新增条目)。若当天记忆索引读不到或无变化,照常覆盖写并如实说明。
