@echo off
chcp 65001 >nul
REM 月末加速批(#038补注2): 断点续跑,预算42万格(台账已72.3万,连19:40自动场收在约118万=79%内)
cd /d D:\股票数据\市场数据
python iFind回填驱动.py --budget 420000
pause
