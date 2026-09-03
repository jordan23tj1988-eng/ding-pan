# -*- coding: utf-8 -*-
"""监控 sentiment-daily-review cron (c4d23047161f) 补跑 20260903 复盘进度
里程碑检测 → _tmp/复盘监控_20260903.log, 每轮只追加变化"""
import os, time, json, sqlite3, glob, sys

BASE = r"D:\股票数据\市场数据"
LOG = os.path.join(BASE, "_tmp", "复盘监控_20260903.log")
DB = r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\executions.db"
D = "20260903"
seen = set()
job_status = "unknown"

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def check_job():
    global job_status
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT status, started_at FROM executions WHERE job_id='c4d23047161f' ORDER BY started_at DESC LIMIT 1")
        row = cur.fetchone()
        con.close()
        if row:
            job_status = f"{row[0]}@{row[1][:19]}"
    except Exception as e:
        job_status = f"err:{e}"

def milestone(name, path):
    if os.path.exists(path) and name not in seen:
        seen.add(name)
        log(f"★里程碑达成: {name}")

log("== 监控启动 ==")
dead_since = None
while True:
    check_job()
    # 里程碑文件
    milestone("M0 取数六件套", os.path.join(BASE, D, "summary.json"))
    milestone("M1 题材归位", os.path.join(BASE, "_学习", f"题材归位_{D}.json"))
    milestone("M2 先行指标卡", os.path.join(BASE, "_学习", "_情绪先行指标.json"))
    milestone("M3 市场温度", os.path.join(BASE, "_学习", "温度表.json"))
    milestone("M4 竞价评分", os.path.join(BASE, "_学习", f"竞价评分_{D}.json"))
    milestone("M5 席位荐票", os.path.join(BASE, "_学习", f"席位荐票_{D}.json"))
    milestone("M6 质量荐票", os.path.join(BASE, "_学习", f"涨停质量荐票_{D}.json"))
    for r in ["auction", "lhb", "theme", "logic", "limitup"]:
        milestone(f"M7 五路判断-{r}", os.path.join(BASE, "_学习", f"五路判断_{D}", f"{r}.json"))
    milestone("M8 总审", os.path.join(BASE, "_学习", f"总审_{D}.json"))
    milestone("M9 推演", os.path.join(BASE, "_学习", f"推演_{D}.json"))
    milestone("M10 judgment骨架", os.path.join(BASE, "_学习", f"judgment_{D}.json"))
    milestone("M11 台账注入/收集器", os.path.join(BASE, "复盘", "盯盘台", "index.html"))
    milestone("M12 哨兵完成", os.path.join(BASE, "_tmp", f"哨兵_{D}.txt"))
    # 盯盘台新鲜度
    idx = os.path.join(BASE, "复盘", "盯盘台", "index.html")
    if os.path.exists(idx):
        mt = time.strftime("%m-%d_%H:%M", time.localtime(os.path.getmtime(idx)))
        if mt.startswith("09-03") and ("index09-03" not in seen):
            seen.add("index09-03"); log(f"★盯盘台index已更新: {mt}")
    # 新增 0903 文件(学习目录, 去重)
    try:
        for p in glob.glob(os.path.join(BASE, "_学习", f"*{D}*")) + glob.glob(os.path.join(BASE, "_学习", "五路判断_" + D, "*")):
            if p not in seen:
                seen.add(p)
                log(f"  新文件: {os.path.relpath(p, BASE)} ({time.strftime('%H:%M', time.localtime(os.path.getmtime(p)))})")
    except Exception:
        pass
    # 停止条件: job 结束 且 最近3分钟内无新文件
    if job_status.startswith(("completed", "error", "failed")) and "ended" not in seen:
        seen.add("ended")
        log(f"== cron job 状态={job_status}, 进入收尾观察 ==")
    if job_status.startswith(("completed", "error", "failed")):
        if dead_since is None:
            dead_since = time.time()
        if time.time() - dead_since > 300:
            log("== 收尾观察5分钟无异常, 监控退出 ==")
            sys.exit(0)
    else:
        dead_since = None
    time.sleep(90)
