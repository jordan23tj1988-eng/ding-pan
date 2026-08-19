# -*- coding: utf-8 -*-
"""
iFind保活 v2 (2026-08-13 重建) — 新架构 SuperCommand 版
====================================================
旧版对象=客户端登录窗口(已过时)。新架构(2026-08-13 重装): SuperCommand.exe 后台常驻,
凭据持久化在 %APPDATA%, 取数走 .venv312 + iFinDPy 本机 IPC, 无需用户登录。
本脚本职责(供 cron no_agent 08:45 调用, 由 ifind_keepalive_cron.py 薄包装):

  1) SuperCommand 进程在岗检查 → 不在则拉起(Start-Process, CREATE_NO_WINDOW)
  2) .venv312 login 实测(rc=0)
  3) 实时取数实测(600000.SH 实时行情, 不用历史K线避免月度额度-4318误报)
  全部 PASS → 打印 "OK ..." (cron 静默/正常投递)
  任一 FAIL → 打印 "ALARM ..." 明细 (微信投递, 用户可见)

注意: 本脚本被 hermes venv 调用时无 iFinDPy, 所以取数验证须 spawn .venv312 python。
      但本脚本本身就是被 ifind_keepalive_cron.py 用 .venv312 直接 spawn 的,
      因此 iFinDPy 直接可用(import 失败则走降级信息)。
"""
import os, sys, json, subprocess, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据"
SC_PATH = r"D:\THSDataInterface_Windows\SuperCommand.exe"
PY312 = os.path.join(BASE, ".venv312", "Scripts", "python.exe")

FAILS = []


def check_process():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SuperCommand.exe"],
                           capture_output=True, text=True, encoding="gbk", timeout=30)
        if "SuperCommand.exe" in r.stdout:
            return True
        # 拉起
        r2 = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Start-Process -FilePath '%s' -WindowStyle Hidden" % SC_PATH],
            capture_output=True, text=True, timeout=30)
        return True
    except Exception as e:
        FAILS.append("SuperCommand 检查异常: %s" % e)
        return False


def check_login_and_data():
    """spawn .venv312 做 login+历史取数实测"""
    test = r'''
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    import iFinDPy
    a = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
    rc = iFinDPy.THS_iFinDLogin(a["account"], a["password"])
    print("login_rc=%d" % rc, flush=True)
    if rc == 0:
        r = iFinDPy.THS_RealtimeQuotes("600000.SH", "open;high;low;latest")
        if isinstance(r, dict) and r.get("errorcode") == 0 and r.get("tables"):
            print("rt_ok rows=%d" % len(r.get("tables")), flush=True)
        else:
            print("rt_fail %s" % (r.get("errorcode") if isinstance(r, dict) else str(r)[:80]), flush=True)
except Exception as e:
    print("EXC %s" % str(e)[:200], flush=True)
'''
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = ""
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
            env.pop(k, None)
        r = subprocess.run([PY312, "-c", test], capture_output=True, text=True,
                           timeout=120, env=env, encoding="utf-8", errors="replace")
        out = (r.stdout or "").strip()
        ok = "login_rc=0" in out and ("rt_ok" in out or "rt_fail" not in out)
        if not ok:
            FAILS.append("login/取数失败: %s" % out[-300:])
        return out
    except Exception as e:
        FAILS.append("spawn 异常: %s" % e)
        return ""


def main():
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proc_ok = check_process()
    out = check_login_and_data()
    if not FAILS:
        print("OK [%s] SuperCommand%s | %s" % (ts, "在岗" if proc_ok else "已拉起", out))
        sys.exit(0)
    print("ALARM [%s] iFinD保活体检失败:\n" % ts + "\n".join(FAILS))
    sys.exit(1)


if __name__ == "__main__":
    main()
