#!/bin/bash
# 一次性：20261023 复盘机械链 batch1（不依赖题材归位）
cd "/d/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
LOG="/d/股票数据/市场数据/_tmp/chain_b1_20261023.log"
D=20261023
P=20261022
: > "$LOG"
run() {
  local tag="$1"; shift
  echo "=== [$tag] $(date +%H:%M:%S) $*" >> "$LOG"
  env -u PYTHONPATH "$PY" "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "--- rc=$rc [$tag] $(date +%H:%M:%S)" >> "$LOG"
  return $rc
}
run 先行指标 情绪先行指标.py "$D"
run 先行指标卡 情绪先行指标.py --card "$D"
run 市场温度 市场温度.py "$D"
run 质量训练 涨停质量训练.py --fetch "$D"
run 结算质量 质量荐票结算.py "$P"
run 结算题材 题材荐票结算.py "$P"
run 结算逻辑 逻辑荐票结算.py "$P"
run 结算席位 席位荐票结算.py "$P"
run 预判结算 预判结算.py "$P"
run 预判预读 预判结算.py --preread "$P"
run 质量荐票 涨停质量荐票.py "$D"
run 温度卡 市场温度.py --card "$D"
run 竞价池结算 竞价池结算.py "$P"
run 竞价评分 竞价评分.py "$D"
run 席位动向库 席位动向库.py rank
run 席位荐票 席位荐票.py "$D"
run 资金温度 资金温度.py
run 中报雷达 中报预增雷达.py "$D"
run 龙虎双源 龙虎榜双源校验.py "$D"
run 风险日历 风险日历.py "$D"
run 撤单差分 竞价撤单差分.py "$D"
run 开盘验证 开盘验证维.py "$D"
run 温度曲线 日内温度曲线.py "$D"
run 轮动图谱 日内轮动图谱.py "$D"
run 横切面 横切面扫描.py "$D"
run 拓展scan 自主拓展扫描.py scan "$D"
run 拓展tick 自主拓展扫描.py tick "$D"
run 战绩画像 五路战绩画像.py "$D"
echo "=== B1 DONE $(date +%H:%M:%S)" >> "$LOG"
