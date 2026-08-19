@echo off
chcp 65001 >nul
setlocal

REM ===== 情绪复盘系统 · 新机一键还原 (方向:仓库 -> 本地) =====
REM 前提: 已装git。若GitHub连不上,去掉下面两行开头的REM并改成你的代理端口
REM set HTTP_PROXY=http://127.0.0.1:7897
REM set HTTPS_PROXY=http://127.0.0.1:7897

set REPO=D:\股票数据\ding-pan仓库

where git >nul 2>nul
if errorlevel 1 (
    echo [X] 没找到git,请先安装 Git for Windows 再运行本脚本
    pause & exit /b 1
)

if not exist "D:\股票数据" mkdir "D:\股票数据"

echo [1/6] 取回仓库 ...
if not exist "%REPO%\.git" (
    git clone https://github.com/jordan23tj1988-eng/ding-pan.git "%REPO%"
    if errorlevel 1 (
        echo [X] 克隆失败。多半是网络问题:编辑本文件,把顶部两行代理REM去掉并改成本机代理端口后重试
        pause & exit /b 1
    )
) else (
    cd /d "%REPO%" && git pull
)

if not exist "%REPO%\市场数据\生成盯盘台.py" (
    echo [X] 仓库里没有 市场数据\生成盯盘台.py,内容不对,停止还原
    pause & exit /b 1
)

echo [2/6] 还原 市场数据 (脚本+数据+复盘+学习) ...
robocopy "%REPO%\市场数据" "D:\股票数据\市场数据" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
if errorlevel 8 ( echo [X] 复制市场数据失败 & pause & exit /b 1 )

echo [3/6] 还原 同步GitHub 目录 (bat+_extras) ...
robocopy "%REPO%\_tools" "D:\股票数据\同步GitHub" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
robocopy "%REPO%\_tools" "D:\股票数据\同步GitHub\_extras\_tools" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
robocopy "%REPO%\skill" "D:\股票数据\同步GitHub\_extras\skill" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
robocopy "%REPO%\米开朗基瑞" "D:\股票数据\同步GitHub\_extras\米开朗基瑞" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
if exist "%REPO%\README.md" copy /y "%REPO%\README.md" "D:\股票数据\同步GitHub\_extras\" >nul
if exist "%REPO%\requirements.txt" copy /y "%REPO%\requirements.txt" "D:\股票数据\同步GitHub\_extras\" >nul
if exist "%REPO%\AGENTS.md" copy /y "%REPO%\AGENTS.md" "D:\股票数据\同步GitHub\_extras\" >nul

echo [4/6] 还原 D:\skill (finesse-ui / gsap-skills / playwright-env 参考文件) ...
robocopy "D:\股票数据\同步GitHub\_extras\skill\finesse-ui" "D:\skill\finesse-ui" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
robocopy "D:\股票数据\同步GitHub\_extras\skill\gsap-skills" "D:\skill\gsap-skills" /E /R:2 /W:3 /NFL /NDL /NJH /NJS
robocopy "D:\股票数据\同步GitHub\_extras\skill\playwright-env" "D:\skill\playwright-env" /E /R:2 /W:3 /NFL /NDL /NJH /NJS

echo [5/6] 核对关键文件 ...
set OK=1
if not exist "D:\股票数据\市场数据\_链路地图.md" ( echo [X] 缺 _链路地图.md & set OK=0 )
if not exist "D:\股票数据\市场数据\_定时任务备份\sentiment-daily-review_prompt.md" ( echo [X] 缺 定时任务备份 & set OK=0 )
if not exist "D:\股票数据\市场数据\_学习\_claude记忆快照\情绪复盘_Claude记忆快照.md" ( echo [X] 缺 记忆快照 & set OK=0 )
if not exist "D:\股票数据\同步GitHub\_extras\skill\sentiment-review-system\SKILL.md" ( echo [X] 缺 技能定义 & set OK=0 )
if "%OK%"=="0" ( echo [X] 有缺失,先解决再进行Claude侧部署 & pause & exit /b 1 )

echo [6/6] 完成! 文件侧还原OK。
echo.
echo ============= 接下来做两件事 =============
echo  1. 打开 Claude 桌面版,选择文件夹 D:\股票数据,对它说:
echo     读 同步GitHub\_extras\_tools\新机Claude部署提示词.md 并逐步执行
echo     (18:00前完成定时任务重建, 18:45前完成记忆导入!)
echo  2. Claude侧全部完成后,先双击 同步到GitHub.bat 手动推一次
echo     (首次会弹GitHub登录), 成功后再双击 安装每日自动同步.bat
echo ==========================================
echo.
echo [!] 注意: 在Claude侧部署完成前,不要双击 同步到GitHub.bat
pause
