#!/bin/bash
# 20261019 卡生成链 批3 (k2-k7,l 及补充)
cd "D:/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
run(){ echo "===== $* ====="; env -u PYTHONPATH -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy "$PY" "$@" 2>&1 | tail -12; echo "[rc=$?]"; }
run 龙虎榜双源校验.py 20261019
run 风险日历.py 20261019
run 竞价撤单差分.py 20261019
run 开盘验证维.py 20261019
run 日内温度曲线.py 20261019
run 日内轮动图谱.py 20261019
run 横切面扫描.py 20261019
echo "===== BATCH3 DONE ====="
