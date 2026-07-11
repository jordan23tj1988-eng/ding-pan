# 盯盘台 · A股短线情绪复盘系统

每日"环境→周期→题材→情绪"复盘 + 盯盘台网页 + 自学习（席位胜率/竞价训练/龙虎榜训练）。

- 📱 盯盘台在线看：https://jordan23tj1988-eng.github.io/ding-pan/
- ⚠️ 本仓库为公开仓库（GitHub Pages 要求），请勿在此存放任何账号、token、个人信息。

## 仓库结构

```
├── index.html / theme.html / cycle.html ...   # 盯盘台网页（GitHub Pages 站点，根目录）
├── archive/                                   # 盯盘台每日存档页
├── 市场数据/                                   # ★ 系统本体（完整镜像 D:\股票数据\市场数据）
│   ├── README_系统运行手册.md                  # 系统运行手册（先读这个）
│   ├── 生成盯盘台.py / 复盘闭环.py / 分析引擎.py 等  # 全部脚本
│   ├── _agent规格/ _盯盘台组件规范.md 等         # 多agent设计规范
│   ├── _学习/                                  # 学习数据（席位库/竞价训练/K线缓存等，~112MB）
│   ├── 复盘/                                   # 每日复盘 HTML/MD + 盯盘台源
│   └── 2026MMDD/                               # 每日原始数据快照
├── skill/sentiment-review-system/SKILL.md      # Claude 技能定义（情绪复盘系统入口）
├── 米开朗基瑞/                                  # 体系手册V2/量化规则清单/复盘推演（方法论地基）
└── requirements.txt
```

## 换电脑迁移（新机器跑起来）

1. **克隆并归位**：
   ```bat
   git clone https://github.com/jordan23tj1988-eng/ding-pan.git
   ```
   把 `市场数据` 目录整个复制到 `D:\股票数据\市场数据`（脚本默认根路径，保持一致就零改动；
   如果想放别处，改每个脚本开头的 `BASE='D:\\股票数据\\市场数据'` 一行）。

2. **装依赖**（Python 3.10+）：
   ```bat
   pip install -r requirements.txt
   ```

3. **验证**：
   ```bat
   python D:\股票数据\市场数据\生成盯盘台.py
   ```
   行情数据走网络在线抓取（akshare/东财/THS接口），无需通达信即可跑复盘。

4. **Claude 侧（如在新电脑用 Claude 桌面版）**：
   - 技能：登录同一 Claude 账号即带有 sentiment-review-system 技能；没有的话用 skill/sentiment-review-system/SKILL.md 重新注册。
   - 定时任务：需重新创建两个——sentiment-daily-review（每交易日 18:00 复盘）、sentiment-morning-auction（9:30 竞价复核）。
   - 定时任务只在 Claude 桌面 App 开着时运行。

5. **盯盘台网页发布**：本地 `市场数据\复盘\盯盘台\push-to-github.bat` 一键推送到本仓库根目录，
   1-2 分钟后 GitHub Pages 生效。

## 同步说明

- 本仓库根目录网页 = 市场数据/复盘/盯盘台/ 的发布副本，由同一个同步脚本一并更新。
- 市场数据/ 由 D:\股票数据\同步GitHub\同步到GitHub.bat 完整镜像（不含 __pycache__），每日19:00自动运行。
- 米开朗基瑞原始语料（430篇文章）未入库（版权原因），只入库了提炼后的体系手册。
