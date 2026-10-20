#!/bin/bash
# 20261019 卡生成链 批1
cd "D:/股票数据/市场数据" || exit 1
PY="D:/股票数据/.venv312/Scripts/python.exe"
run(){ echo "===== $* ====="; env -u PYTHONPATH -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy "$PY" "$@" 2>&1 | tail -12; echo "[rc=$?]"; }
run 市场温度.py 20261019
run 涨停质量训练.py --fetch 20261019
run 质量荐票结算.py 20261016
run 题材荐票结算.py 20261016
run 逻辑荐票结算.py 20261016
run 席位荐票结算.py 20261016
run 预判结算.py 20261016
run 预判结算.py --preread 20261016
echo "===== BATCH1 DONE ====="
