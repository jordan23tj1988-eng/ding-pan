# -*- coding: utf-8 -*-
"""20261015 复盘链人工收口 runner（宿主接管；按 job 契约步骤 9→15 顺序，逐步 [RC] 记录）
背景: 18:21 补跑在 20:25 迭代耗尽(120/120)中止；五路 body 已注入(20:08)、index/cycle body 20:29 才落盘。
本 runner: ①归一化 index/cycle body 名 + 注入 7 个 body + 补 一句话 ②台账三件套 ③模拟盘 settle/dashboard
④生成盯盘台(发布+存档) ⑤warboard ⑥专属核对+哨兵 ⑦master结算(昨日)。只跑机械脚本，零 LLM、零编造。
"""
import os, sys, json, subprocess, glob, re

R = r"D:\股票数据\市场数据"
D = "20261015"
DPREV = "20261014"
PY = r"D:\股票数据\.venv312\Scripts\python.exe"
LOG = os.path.join(R, "_tmp", "收口_20261015.log")
os.chdir(R)


def log(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s, flush=True)


ENV = dict(os.environ)
ENV.pop("PYTHONPATH", None)


def run(label, fatal, args, timeout=1800):
    log("[RUN] %s :: %s" % (label, " ".join(args)))
    try:
        p = subprocess.run([PY] + args, cwd=R, env=ENV, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        rc = p.returncode
        out = (p.stdout or "")[-2000:]
        err = (p.stderr or "")[-1200:]
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = (e.stdout or "")[-2000:] if isinstance(e.stdout, str) else ""
        err = "TIMEOUT after %ss" % timeout
    log("[RC] %s = %s\n%s%s" % (label, rc, out, ("\n[STDERR] " + err) if err else ""))
    if fatal and rc != 0:
        log("[FATAL_STOP] %s" % label)
        sys.exit(1)
    return rc


# ── 阶段 0: body 归一化 + 注入 + 一句话 ─────────────────────────────
def prep():
    for route, src in (("index", "_学习/_body_index_%s.html" % D),
                       ("cycle", "_学习/_body_cycle_%s.html" % D)):
        dst = "_学习/%s_body_%s.html" % (route, D)
        s = src % () if "%s" in src else src
        src = src
        assert os.path.exists(src), "缺源: " + src
        if not os.path.exists(dst):
            open(dst, "w", encoding="utf-8").write(open(src, encoding="utf-8").read())
            log("[PREP] 归一化 %s -> %s" % (src, dst))
        else:
            log("[PREP] 已存在, 不覆盖: %s" % dst)

    JP = "_学习/judgment_%s.json" % D
    j = json.load(open(JP, encoding="utf-8"))
    bd = j.setdefault("bodies", {})
    MAP = {"index": "_学习/index_body_%s.html" % D,
           "auction": "_学习/auction_body_%s.html" % D,
           "lhb": "_学习/lhb_body_%s.html" % D,
           "theme": "_学习/theme_body_%s.html" % D,
           "logic": "_学习/logic_body_%s.html" % D,
           "limitup": "_学习/limitup_body_%s.html" % D,
           "cycle": "_学习/cycle_body_%s.html" % D}
    fails = []
    for route, p in MAP.items():
        if not os.path.exists(p):
            fails.append("%s 缺文件 %s" % (route, p)); continue
        s = open(p, encoding="utf-8").read()
        h2 = re.findall(r"<h2[^>]*>", s)
        no, nc = len(re.findall(r"<div[\s>]", s)), len(re.findall(r"</div>", s))
        bad = []
        if route != "index" and len(h2) < 6:
            bad.append("h2=%d<6" % len(h2))
        if route == "index" and len(h2) < 8:
            bad.append("h2=%d<8" % len(h2))
        if no != nc:
            bad.append("div不平 %d/%d" % (no, nc))
        if len(s) < 1500:
            bad.append("过短 %d" % len(s))
        bd[route] = s
        log("[PREP] %-8s len=%-7d h2=%-2d div=%d/%d %s" % (route, len(s), len(h2), no, nc,
                                                           ("[问题] " + "; ".join(bad)) if bad else "OK"))
        if bad:
            fails.append("%s: %s" % (route, "; ".join(bad)))

    # 一句话: 机械投影 fact + 总审 + 五路档位（无编造）
    try:
        fa = json.load(open("_学习/fact_%s.json" % D, encoding="utf-8"))["facts"]
        g = lambda k: fa.get(k, {}).get("value") if isinstance(fa.get(k), dict) else fa.get(k)
        prev = {}
        pp = "_学习/fact_%s.json" % DPREV
        if os.path.exists(pp):
            pf = json.load(open(pp, encoding="utf-8"))["facts"]
            prev = {k: (pf.get(k, {}).get("value") if isinstance(pf.get(k), dict) else pf.get(k))
                    for k in ("温度", "涨停数")}
        z = json.load(open("_学习/总审_%s.json" % D, encoding="utf-8"))
        verdict = z.get("总裁决") or {}
        grades = []
        for rt in ("auction", "lhb", "theme", "logic", "limitup"):
            try:
                jj = json.load(open("_学习/%s判断_%s.json" % (rt, D), encoding="utf-8"))
                grades.append(str((jj.get("判断") or {}).get("档位") or "?"))
            except Exception:
                grades.append("?")
        t = "温度%s" % g("温度")
        if prev.get("温度") is not None:
            t += "（前值%s）" % prev["温度"]
        t += "、涨停%s" % g("涨停数")
        if prev.get("涨停数") is not None:
            t += "（前%s）" % prev["涨停数"]
        t += "、炸板%s、最高%s板；五路%s；总档%s（置信度%s）" % (
            g("炸板数"), g("最高连板"), "、".join(grades),
            verdict.get("档位") or "?", verdict.get("置信度") or "?")
        j["一句话"] = t
        j.setdefault("date", D)
        j.setdefault("更新label", D + " 复盘")
        log("[PREP] 一句话 = " + t)
    except Exception as e:
        log("[PREP] 一句话 生成失败(不阻断): %r" % (e,))

    json.dump(j, open(JP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("[PREP] 注入完成 bodies=%s 总字符=%d" % (sorted(bd), sum(len(v) for v in bd.values())))
    if fails:
        log("[FATAL_STOP] prep 校验失败: " + " | ".join(fails))
        sys.exit(1)
    return True


if __name__ == "__main__":
    log("\n===== 收口开始 %s =====" % D)
    prep()
    run("资金温度(注入lhb FUNDTEMP)", 0, ["资金温度.py", D])
    run("涨停复盘台账", 1, ["涨停复盘台账.py", D, "--from-data"])
    run("龙虎榜台账", 1, ["龙虎榜台账.py", D, "--from-data"])
    run("竞价池结算归档(--inject)", 1, ["竞价池结算归档.py", "--inject"])
    run("模拟盘settle", 1, ["模拟盘引擎.py", "settle", D])
    run("模拟盘dashboard", 1, ["模拟盘引擎.py", "dashboard", D])
    run("生成盯盘台(发布+存档)", 1, ["生成盯盘台.py", D], timeout=2400)
    run("warboard重建", 0, ["warboard_build.py", D])
    run("theme数据核对", 0, ["theme数据核对.py", D])
    run("cycle数据核对", 0, ["cycle数据核对.py", D])
    run("复盘一致性哨兵", 0, ["复盘一致性哨兵.py", D])
    run("master结算(昨日)", 0, ["master结算.py", DPREV])
    log("===== 收口步骤执行完毕 =====")
