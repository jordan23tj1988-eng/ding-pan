#!/bin/bash
# 卡生成链 20261020
cd "D:/股票数据/市场数据" || exit 1
P="D:/股票数据/.venv312/Scripts/python.exe"
D=20261020
Y=20261019
run() {
  name="$1"; shift
  echo ""
  echo "===== [$(date +%H:%M:%S)] $name :: $*"
  env -u PYTHONPATH -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy "$P" "$@" 2>&1 | tail -14
  rc=${PIPESTATUS[0]}
  echo "----- rc=$rc $name"
}

run "b市场温度"      市场温度.py $D
run "c质量训练fetch" 涨停质量训练.py --fetch $D
run "a质量结算"      质量荐票结算.py $Y
run "a题材结算"      题材荐票结算.py $Y
run "a逻辑结算"      逻辑荐票结算.py $Y
run "a席位结算"      席位荐票结算.py $Y
run "a2预判结算"     预判结算.py $Y
run "a3条件决断"     预判结算.py --preread $Y
run "d质量荐票"      涨停质量荐票.py $D
run "e温度卡"        市场温度.py --card $D
run "f竞价池结算"    竞价池结算.py $Y
run "g竞价评分"      竞价评分.py $D
run "h席位rank"      席位动向库.py rank
run "i席位荐票"      席位荐票.py $D
run "j资金温度"      资金温度.py
run "k中报雷达"      中报预增雷达.py $D
run "k2双源校验"     龙虎榜双源校验.py $D
run "k3风险日历"     风险日历.py $D
run "k4撤单差分"     竞价撤单差分.py $D
run "k5开盘验证维"   开盘验证维.py $D
run "k6日内温度"     日内温度曲线.py $D
run "k7日内轮动"     日内轮动图谱.py $D
run "l横切面"        横切面扫描.py $D
run "m自主拓展scan"  自主拓展扫描.py scan $D
run "m自主拓展tick"  自主拓展扫描.py tick $D
run "n战绩画像"      五路战绩画像.py $D
echo ""
echo "===== [$(date +%H:%M:%S)] 卡生成链结束"
