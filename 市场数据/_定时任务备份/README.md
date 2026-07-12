# 定时任务 prompt 备份

此目录=Claude 定时任务 prompt 的**只读备份副本**(随19:00同步进仓库,使项目自包含可复现)。
真身在 Claude 的 Scheduled 存储里(`C:\Users\66353\Claude\Scheduled\{taskId}\SKILL.md`),**改 prompt 必须走 update_scheduled_task,改完同步刷新本目录副本**——直接改这里不生效。

- sentiment-daily-review_prompt.md —— 工作日18:00 傍晚全链路(多agent复盘→judgment→盯盘台)
- sentiment-morning-auction_prompt.md —— 工作日9:30 早盘竞价快线+当日池预览+昨日池初读

旧任务 mikai-daily-review / mikai-morning-auction 已停用(enabled=false),不备份。
备份时间: 2026-07-11(v3.2页面改造+三窗触发器版)

## 2026-07-12 竞价评分体系上线,两任务prompt已更新(备份文件未整份重抄,增量记录)
- sentiment-daily-review 步骤4竞价bullet → 08号v3三步:(a)竞价池结算.py(带评分半区+闸门对账) (b)竞价评分.py {d}(评分卡嵌auction段一) (c)竞价池分桶回填.py滚动;步骤12 auction段一=嵌竞价评分卡;总审加"竞价分各处与竞价评分json同值"。
- sentiment-morning-auction 新增2b全市场竞价快照留档(竞价全市场快照.py)+步骤4闸门(竞价闸门.py {昨日d},高开≥5%必弃,注入★今晨闸门段)。
- 完整prompt以 C:\Users\66353\Claude\Scheduled\{taskId}\SKILL.md 为准(备份md为2026-07-11旧版)。

## 2026-07-12(晚) auction页台账化,daily-review prompt再更新
- 页面链路铁律加"竞价页三标记区各管各"(SCORECARD/POOLLEDGER/晨场段);auction段一禁trow池行表(老卡废除);段二结算台账由 竞价池结算归档.py --inject 注入(最新展开历史折叠);出页顺序=judgment→归档→生成盯盘台;总审+目检加对应检查项。
- 2026-07-12晚补:auction段二台账=全部日期条可折叠(最新open"最新"chip/历史"存档"chip);洞察改按日文件 _学习/竞价池洞察_{d}.html 由归档脚本嵌对应日折叠内,禁body游离card;历史池07-01~07-08已补结算入档。
