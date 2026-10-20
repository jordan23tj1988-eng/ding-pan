@echo off
cd /d "D:\股票数据\市场数据"
"D:\股票数据\.venv312\Scripts\python.exe" _ops\guard.py check --repair --send >> "_学习\_运维\guard.log" 2>&1
