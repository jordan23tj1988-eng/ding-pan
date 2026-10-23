# -*- coding: utf-8 -*-
"""一次性：按真实最大编号追加 20261023 变更总账（宿主执行）"""
import re, os

os.chdir(r"D:\股票数据\市场数据")
led = "_变更总账.md"
txt = open(led, encoding="utf-8").read()

if "手工接管日链（cron disabled）" in txt:
    print("今日条目已存在，跳过")
    raise SystemExit(0)

nums = [int(x) for x in re.findall(r"^## #(\d+)", txt, re.M)]
n = max(nums) + 1
print("现有最大编号", max(nums), "→ 新编号", n)

entry = f"""

## #{n} | 2026-10-23 | 手工接管日链（cron disabled）+ 五路 Master 指派落地
- **动机**: 定时链 sentiment-daily-review 于 10/21 三次 provider 失败后被禁用，用户要求手工完成 20261023 复盘。
- **改了什么**:
  1. lhb 路：`席位荐票结算.py` 新增 `lhb_net_stock()`（双值净额：值A=剔区间榜每码1行、值B=含区间榜全行）与 `selftest_lhb_net(d)`（5 项自检），payload 增双值字段；落盘件 `_学习/lhb净额双值_20261023.json`。
  2. logic 路：`_ops/` 新增 `卡位纯度复算.py`、`纯度涨停历史.py`、`身位分桶.py`、`三季报池日序列.py`（每日可复用的 F10 卡位纯度/历史/身位/三季报序列）。
  3. 宿主：无生产脚本改动；一次性 runner 在 `_tmp/run_chain_b1_20261023.sh`（含日志）。补跑 B1 漏项 `风险事件.py 20261023`（B1 runner 漏排此步，致 风险日历 首跑 partial）。
- **真实验证**: `selftest_lhb_net('20261023')` 返回 pass_all=True（值A 16.0607亿 / 值B 26.3952亿、唯一码 62、同码多行金额逐位相等）；`卡位纯度复算.py 20261022` 回归得 3/13=23.08%，与昨日手工逐只结果一致。
- **触点文件**: `席位荐票结算.py`、`_ops/卡位纯度复算.py`、`_ops/纯度涨停历史.py`、`_ops/身位分桶.py`、`_ops/三季报池日序列.py`、`_变更总账.md`。
- **待办**: `ifind查.py` 本机不存在（五路各自 0 次外部查证，已如实计入盲区）——需确认是未部署还是路径变更。
"""
with open(led, "a", encoding="utf-8") as f:
    f.write(entry)

tail = open(led, encoding="utf-8").read()[-260:]
print("已追加，尾部:", tail.replace("\n", " | ")[:260])
