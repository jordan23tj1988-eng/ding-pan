@echo off
chcp 65001 >nul
setlocal

REM ===== 配置 =====
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
set SRC=D:\股票数据\市场数据
set EXTRAS=D:\股票数据\同步GitHub\_extras
set REPO=D:\股票数据\ding-pan仓库

echo [盯盘台] 全量同步到 GitHub ...
echo.

REM ===== 首次运行: 克隆仓库 =====
if not exist "%REPO%\.git" (
    echo [首次运行] 正在克隆仓库到 %REPO% ...
    git clone https://github.com/jordan23tj1988-eng/ding-pan.git "%REPO%"
    if errorlevel 1 (
        echo [X] 克隆失败, 请检查网络或代理是否开启
        if "%~1"=="" pause
        exit /b 1
    )
)

cd /d "%REPO%"
git pull origin master

echo [1/4] 镜像 市场数据 (脚本+复盘+学习数据) ...
robocopy "%SRC%" "%REPO%\市场数据" /MIR /XD __pycache__ .git /XF *.pyc /R:2 /W:3 /NFL /NDL /NJH /NJS
if errorlevel 8 ( echo [X] 复制市场数据失败 & if "%~1"=="" pause & exit /b 1 )

echo [2/4] 更新盯盘台网页到仓库根目录 ...
robocopy "%SRC%\复盘\盯盘台" "%REPO%" /E /XD .git /XF push-to-github.bat /R:2 /W:3 /NFL /NDL /NJH /NJS
if errorlevel 8 ( echo [X] 复制网页失败 & if "%~1"=="" pause & exit /b 1 )

echo [3/4] 更新 README / 技能定义 / 米开体系手册 ...
robocopy "%EXTRAS%" "%REPO%" /E /R:2 /W:3 /NFL /NDL /NJH /NJS

echo [4/4] 提交并推送 ...
git add -A
git commit -m "sync %date% %time:~0,5%"
git push origin master
if errorlevel 1 (
    echo [X] 推送失败, 请检查网络/代理/GitHub登录状态
    if "%~1"=="" pause
    exit /b 1
)

echo.
echo [√] 同步成功!
echo [√] 仓库: https://github.com/jordan23tj1988-eng/ding-pan
echo [√] 盯盘台: https://jordan23tj1988-eng.github.io/ding-pan/
if "%~1"=="" pause
