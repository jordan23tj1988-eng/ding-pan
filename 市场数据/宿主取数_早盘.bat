@echo off
chcp 65001 >nul
cd /d D:\股票数据\市场数据
set "PYEXE=python"
where python >nul 2>nul || set "PYEXE=py -3"
if "%1"=="auto" (
    %PYEXE% 宿主取数_早盘.py >> _学习\宿主取数控制台.log 2>&1
) else (
    %PYEXE% 宿主取数_早盘.py %*
    pause
)
