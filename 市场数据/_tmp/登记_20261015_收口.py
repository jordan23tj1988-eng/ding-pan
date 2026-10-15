# -*- coding: utf-8 -*-
"""登记 20261015 晚间收口: 变更总账 #237/#238 + 缺口登记闭环"""
import json, io, os

R = r"D:\股票数据\市场数据"
LEDGER = os.path.join(R, "_变更总账.md")

sec237 = """
## #237 20261015 晚间出页收口: 5 条门禁根源修复 + 周期投票牌补产(宿主机械收口, 零 LLM)
- 背景: 18:00 首跑崩在模型初始化(#234 已修 pin, 崩因与链路/数据无关); 18:21 source=direct 补跑于 20:25:54
  因「Iteration budget exhausted (120/120)」判 wedged 失败。五路判断/总审/推演/交易计划/正文注入(V)-2.57MB 均已落盘,
  缺「11b 五路周期票」与「13–15 出页」。宿主改走纯机械 runner(`_tmp/收口_20261015.py`, 零 LLM)按契约步骤 9→15 收口。
- 门禁① auction claim 归一化不对称(model incomplete / legacy claim absent from source):
  正文用 HTML 实体写占位符 `&lt;d&gt;`/`&lt;d-1&gt;` → 去标签后成**字面** `<d>`; claim 文本二次 HTML 解析时
  `<d>`/`<d-1>` 被当作标签吃掉 → 归一化后与正文不再互为子串 → 门禁判 claim 篡改。
  改=占位符写成实际日期(`20261015` / `20261014`), 零语义改动、零数字改动。文件 `_学习/auction_body_20261015.html`
  (备份 `*.bak_收口_20261015`)。★同类坑: 任何 `<字母…>` 形态占位符都会命中, 正文勿用 HTML 实体写占位符。
- 门禁② cycle 正文 C1 null 字面量: `昨日涨停溢价=null（源未产出，不补造）`(&3处) → `溢价=—`。
  口径依据=用户规则「无数据字段保持 —，不新增占位字样」。文件 `_学习/cycle_body_20261015.html`。
- 门禁③ theme 深挖段代码越池(荐票铁律: bodies.theme 内代码∈当日 zt_pool):
  深挖段引用了**20261014 指派时**的 AI 短剧线名单(002343/603533/603598), 其中 603533/603598 当日已不在涨停池。
  改=就地补事实标注「…（不在当日涨停池）」(反事实语境, 非荐票; 三名中 002343 慈文传媒仍在池内)。文件 `_学习/theme_body_20261015.html`。
- 门禁④/⑤ LEDGER·POLLEDGER·LHBLEDGER 卡整块丢失(check auction: POOLLEDGER component missing;
  C9 xxxLEDGER 最新日块=None): 契约第 13 步自带警告「生成器重跑会冲掉台账注入和五路判断注入」——
  宿主为重注入修好的正文而二次注入五路 body 时, 把台账三件套写进 bodies 的卡一并覆盖了。
  修=按契约顺序重跑 **step10 台账三件套**: `涨停复盘台账.py 20261015 --from-data`(涨停36·无主流·分支轮动) →
  `龙虎榜台账.py 20261015 --from-data`(上榜60·机构在场36只·S/A出手8笔) → `竞价池结算归档.py --inject`。
  ★正确顺序=五路body注入 → 台账注入 → 生成盯盘台.py; 任何二次 body 注入后必须补跑台账三件套。
- 11b 周期投票牌补产: 五路 `周期投票_{route}_20261015.json` **未采集**(补跑 delegate context 未内联第 11b 项,
  与五路自身判断无关) → 按 `周期投票.py` 自身纪律「缺票=弃权照实」跑 `tally 20261015`:
  台账条目 = n_voted 0 / 五路全『弃权』/ 主判=冰点·降·74; 产出 `_学习/周期投票牌_20261015.html` +
  `_学习/周期投票结果_20261015.json` → review_publish 的 IDXVOTE/MACHVOTE 机器卡由 missing 转 ok。
  ★**不代拟五路票**(与当轮 20:31 自审口径「只能立断档标注, 不得代拟」一致; 10/13 曾用宿主桥接, 本次选更严口径)。
- 出页验证(真信号): `生成盯盘台.py 20261015` → staging manifest **status=pass / errors=[] / published=true**;
  专属核对 auction 12/12、lhb 33/33、theme 54/54、limitup 30/30 全过; 一致性哨兵=全过(0警告);
  线上**独立复跑** `复盘一致性哨兵.py 20261015` → 全过(0警告) RC=0;
  7 主页面(index/cycle/auction/lhb/theme/logic/limitup) + `复盘/盯盘台/archive/20261015.html` 落盘(21:00–21:01);
  健康门禁 `复盘链健康检查.py 20261015 --strict` → pass, coverage 1.0(27/27), continuity true;
  链路 watcher 自证 15/15 全阶段就绪。
- 遗留缺口(登记): 第 11b 项未被补跑的 delegate context 内联 → 需在 jobs.json 的 delegate 批次补该项,
  否则每日周期票只能靠『弃权/桥接』; 今日已按弃权如实入账(不阻塞出页)。
- 备份/回滚: 三个正文 `*.bak_收口_20261015`; runner `_tmp/收口_20261015.py`、日志 `_tmp/publish_20261015_r{2,3}.log`。
"""

sec238 = """
## #238 快失败落地: deepseek 显式 stale 截止 180s(替代 600s reasoning floor)
- 背景: 20261015 上午 DeepSeek API 间歇零响应, 非流式 stale 预算走 `deepseek-flash` 的 reasoning floor
  **600s/次** + 放弃阈值 `HERMES_STREAM_STALE_GIVEUP` 默认 5 → 单次故障烧 ~50 分钟, 远超盘中场次窗口(#236)。
- 改动(唯一一处, config 路径): `~/.hermes/profiles/a/config.yaml` 新增
  `providers.deepseek.stale_timeout_seconds: 180`。备份 `config.yaml.bak_stale180_20261015_2106`。
- 为什么必须走 config: `run_agent._resolved_api_call_stale_timeout_base()` 的优先级 =
  per-model/provider `stale_timeout_seconds` > `HERMES_API_CALL_STALE_TIMEOUT` > reasoning floor > 90s;
  **只有 config/env 显式值能压过 600s floor**, 且显式值不再吃 run-budget 缩水(`_stale_timeout_is_explicit`)。
  上下文 >10万 token 时生效值 = max(180,240) = 240s; >5万 = max(180,150) = 180s。
- 安全性核验: ①实测健康调用耗时 2.3–13.1s(agent.log) → 180s ≈13× 余量, 不误杀健康调用;
  ②`hermes_cli/providers.py::resolve_user_provider` 文档明确: 无 endpoint(api/url/base_url) 的
  `providers.<name>` 块=**内置 provider 调参**, 不会被解析成自定义 endpoint。实测复核:
  `resolve_provider_full('deepseek')` → source=models.dev / transport=openai_chat / base_url=https://api.deepseek.com(未变),
  `get_provider_stale_timeout('deepseek','deepseek-flash')`=180.0, reasoning floor 仍=600(但被 config 短路)。
- 生效方式: `hermes -p default gateway restart`(旧 PID 18848 → 新 PID 22452, status ✓); 配置在进程启动时读取。
- 效果: 单次 provider 无响应 180s(大上下文 240s)收敛; 连续 5 次才放弃 → 最坏 ~15 分钟判失败, 匹配
  用户 20261015 拍板的「快失败 + 人工补」; 窗口内自动补火**不做**(用户同日明确否掉)。
"""

with io.open(LEDGER, "a", encoding="utf-8", newline="") as f:
    f.write(sec237)
    f.write(sec238)
print("[LEDGER] 追加 #237/#238 完成, 现尾部:")
tail = open(LEDGER, encoding="utf-8").read()[-400:]
print(tail)

# 缺口登记闭环
gp = os.path.join(R, "_学习", "盘中缺口登记_20261015.json")
g = json.load(open(gp, encoding="utf-8"))
g["待办"] = [
    "✅已落地(20261015 晚, 变更总账 #238): 快失败 —— config providers.deepseek.stale_timeout_seconds=180 "
    "(压过 deepseek-flash 600s reasoning floor) + 网关重启生效 → 单次无响应 180s/大上下文 240s 收敛, 最坏 ~15 分钟判失败。",
    "❌不做(用户 20261015 拍板): 窗口内自动补火 —— 只做『快失败 + 人工补』, 越窗一律登记缺口不补造。",
    "本缺口件保持永久登记: 上述 4 场次决策件按铁律②零后视镜不补造。",
]
g.setdefault("后续登记", {})["晚间收口"] = {
    "登记时间": "2026-10-15T21:10+08:00",
    "出页": "20261015 已出页(archive/20261015.html 21:01:18; 门禁 status=pass; 哨兵全过)",
    "缺口": "第 11b 项『五路周期投票』未被补跑 delegate context 内联 → 当日按『缺票=弃权照实』入账(不代拟); 需在 jobs.json delegate 批次补该项",
}
json.dump(g, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[GAP] 已更新 待办/后续登记; bytes=", os.path.getsize(gp))
