# 新机Claude部署提示词

> 用法:在新机器上先双击跑完 `新机一键还原.bat`,然后打开 Claude 桌面版、选择文件夹 `D:\股票数据`,把本文件喂给它(或直接说:"读 同步GitHub\_extras\_tools\新机Claude部署提示词.md 并逐步执行")。
> 下面全文是给 Claude 的指令。

---

你好,我刚把"情绪复盘系统"从旧机器迁移到这台新机器。文件已经由 `新机一键还原.bat` 从 GitHub 仓库还原到 `D:\股票数据\`,现在需要你完成 Claude 侧的四步部署。旧机器的定时任务已全部禁用(2026-07-17),今晚起由这台机器接管。请按顺序执行,每步完成后向我报告:

## 第一步:注册技能(save_skill)

读 `同步GitHub\_extras\skill\` 下这些技能的 SKILL.md,用 save_skill 逐个注册(name/description 按各 SKILL.md frontmatter 原文,content 用全文,若已存在同名技能则 overwrite):

1. `sentiment-review-system`(必装,情绪复盘系统主技能)
2. `finesse-ui`(注意:其 description 里写死了完整参考文件在 `D:\skill\finesse-ui`,bat 已还原该路径)
3. `gsap-skills`(同上,完整模块在 `D:\skill\gsap-skills`)
4. `taste-skill`

`playwright-env` 不是技能,是沙箱目检环境脚本,不用注册。

## 第二步:重建 4 个定时任务(时间敏感,18:00 前完成)

读 `市场数据\_定时任务备份\` 下的 4 份 prompt 备份,用 create_scheduled_task 重建。**prompt 用备份正文全文**(去掉 frontmatter 里的 backup_date 行和"⚠备份说明"引用行,保留版本戳行),taskId、description、cron 如下:

| taskId | cron | 说明 |
|---|---|---|
| `sentiment-daily-review` | `0 18 * * 1-5` | 每交易日18:00复盘主链路 |
| `sentiment-morning-auction` | `20 9 * * 1-5` | 每交易日9:20早盘竞价 |
| `sentiment-weekly-training` | `0 20 * * 6` | 每周六20:00六账本考核 |
| `sentiment-memory-snapshot` | `40 18 * * *` | 每天18:40记忆快照(必须早于19:00 GitHub同步) |

## 第三步:导入记忆(时间敏感,18:45 前完成)

读 `市场数据\_学习\_claude记忆快照\情绪复盘_Claude记忆快照.md`,把其中每条记忆按原名恢复成你持久记忆目录下的独立记忆文件(保留原有的 name/description/type 和正文的 Why/How to apply/数据结论,不许改数字),并逐条登记进 MEMORY.md 索引。

⚠️ 为什么 18:45 前:第二步建的快照任务 18:40+抖动 会运行,如果那时你的记忆还是空的,它会用空记忆覆盖仓库里的好快照。若来不及,先把 `sentiment-memory-snapshot` 任务暂时 disabled,导完记忆再 enable。

导入后注意:快照只含情绪复盘相关记忆,不含用户的通用偏好。先补记这几条已知偏好:默认用中文回复;生成图/文件后立刻 present_files 给用户;改任何情绪系统文件前先读 `市场数据\_变更总账.md` 最近3条并遵守改动三合一铁律(`_链路地图.md` 第〇节)。

## 第四步:验收

1. 读 `市场数据\_变更总账.md` 最近 3 条,确认认知与最新改动同步(最近一条应是 #004 跨设备备份补齐)。
2. 跑 `python3 市场数据/复盘一致性哨兵.py {最近交易日YYYYMMDD}`(沙箱路径按 `ls /sessions/*/mnt/股票数据/市场数据` 定位),报告各检查项结果。
3. 向我汇报清单:4个技能✓/4个定时任务✓(各自nextRunAt)/记忆N条✓/哨兵结果,以及今晚 18:00 是否一切就绪。

## 部署完成后提醒我(用户)手动做的两件事

1. 双击 `D:\股票数据\同步GitHub\同步到GitHub.bat` 手动推一次,验证 GitHub 登录凭据(首次会弹登录窗);
2. 成功后双击 `安装每日自动同步.bat` 注册每天 19:00 的 Windows 自动同步任务。

## 边界说明(你应知道的)

- 本仓库是**公开**的:私有策略(自研战法/缠论引擎等)的记忆、技能、语料按铁律一律不进这个仓库,也不在本机快照里。用户如需这些,会从旧机另行迁移。
- 定时任务只在 Claude 应用开着时运行,错过的会在下次启动时补跑。
- 若今晚 18:00 复盘取数报错,先按 skill 里的"取数误判四替代路诊断"排查代理差异(新机网络环境与旧机不同,旧机经验是"出网必走代理127.0.0.1:7897",本机未必)。
