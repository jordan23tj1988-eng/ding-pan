@echo off
chcp 65001 >nul
REM ===== 安装宿主取数(2026-07-17 新机沙箱无外网替代方案,变更总账#005) =====
set HTTP_PROXY=http://127.0.0.1:15236
set HTTPS_PROXY=http://127.0.0.1:15236
set "PYEXE=python"
where python >nul 2>nul || set "PYEXE=py -3"
%PYEXE% --version >nul 2>nul || ( echo [X] 未找到Python,请先安装: winget install Python.Python.3.12 ^(或python.org下载,勾选Add to PATH^),装完重开cmd再跑本bat & pause & exit /b 1 )

echo [1/3] 宿主Python装取数依赖...
%PYEXE% -m pip install -q --upgrade akshare pandas requests lxml beautifulsoup4 openpyxl
if errorlevel 1 ( echo [X] 宿主依赖安装失败,检查python/代理 & pause & exit /b 1 )

echo [2/3] 下载沙箱离线依赖包到 D:\股票数据\_pip_offline (Linux版wheel)...
%PYEXE% -m pip download -d D:\股票数据\_pip_offline --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.10 weasyprint aiohttp tqdm decorator nest-asyncio html5lib curl_cffi xlrd tabulate certifi py-mini-racer akracer
%PYEXE% -m pip download -d D:\股票数据\_pip_offline --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.10 --no-deps akshare
%PYEXE% -m pip download -d D:\股票数据\_pip_offline jsonpath

echo [3/3] 注册Windows计划任务(工作日 17:40傍晚 / 09:24早盘)...
schtasks /Create /F /TN "情绪复盘宿主取数_傍晚" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:40 /TR "D:\股票数据\市场数据\宿主取数_傍晚.bat auto"
schtasks /Create /F /TN "情绪复盘宿主取数_早盘" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 09:24 /TR "D:\股票数据\市场数据\宿主取数_早盘.bat auto"

echo.
echo [√] 完成。手动测试: 双击 宿主取数_傍晚.bat (交易日16:35后跑最佳,龙虎榜16:30后才全)
pause
