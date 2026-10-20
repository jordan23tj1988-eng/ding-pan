@echo off
cd /d D:\股票数据\市场数据
"D:\股票数据\.venv312\Scripts\python.exe" _ops\observability.py >> _学习\_运维\observability.log 2>&1
"D:\股票数据\.venv312\Scripts\python.exe" _ops\render_observability.py >> _学习\_运维\observability.log 2>&1
