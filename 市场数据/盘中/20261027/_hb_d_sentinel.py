# -*- coding: utf-8 -*-
"""hb-d 本场自审（哨兵）：发版一致性/账本闭环/零编造抽查/不可覆盖。"""
import json, os, hashlib, subprocess, sys, datetime

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
fails, oks = [], []


def ck(name, cond, detail=""):
    (oks if cond else fails).append((name, detail))


dec = json.load(open(os.path.join(D, "临盘决断_20261027_1330.json"), encoding='utf-8'))
probe = json.load(open(os.path.join(D, "_hb_d_probe.json"), encoding='utf-8'))
probe2 = json.load(open(os.path.join(D, "_hb_d_probe2.json"), encoding='utf-8'))
nxt = json.load(open(os.path.join(D, "_hb_d_next.json"), encoding='utf-8'))
st = json.load(open(os.path.join(SIM, "lhb", "state.json"), encoding='utf-8'))
au = json.load(open(os.path.join(D, "入账_20261027_1330.json"), encoding='utf-8'))

f = dec["fills"][0]
# 1 算术
ck("C01 唯一fill=300296卖出", len(dec["fills"]) == 1 and f["code"] == "300296" and f["action"] == "fill_sell")
ck("C02 proceeds=px_exec×qty", abs(f["proceeds"] - round(f["px_exec"] * f["qty"], 2)) < 1e-6, str(f["proceeds"]))
ck("C03 pnl=proceeds-cost", abs(f["pnl"] - round(f["proceeds"] - f["cost"], 2)) < 1e-6, str(f["pnl"]))
ck("C04 ret_pct=proceeds/cost-1", abs(f["ret_pct"] - round((f["proceeds"] / f["cost"] - 1) * 100, 2)) < 1e-6, str(f["ret_pct"]))
# 2 fill 口径
ck("C05 px_exec=下一tick×(1-0.1%)向下取2位",
   f["px_exec"] == int(nxt["quote"]["300296"]["px"] * 0.999 * 100) / 100.0,
   "tick=%s exec=%s" % (nxt["quote"]["300296"]["px"], f["px_exec"]))
ck("C06 tick时戳晚于决断时戳",
   nxt["quote"]["300296"]["t"] > "20261027133600" and f["ts"] == "2026-10-27 13:36:06",
   nxt["quote"]["300296"]["t"])
# 3 零后视镜：决策引用的行情时戳 ≤ 决断时戳
ck("C07 决断数据不晚于决断时戳", probe["dec_ts"] >= probe["frames"]["last"])
ck("C08 池帧未断更(<600s)", probe["frames"]["age_s"] < 600, "%ss" % probe["frames"]["age_s"])
ck("C09 数据新鲜度声明与实测一致", "34s" in dec["数据新鲜度"]["池帧"]["末帧龄_决断时"])
# 4 零编造抽查：指数/池/涨停数逐个对账
q = probe["quotes"]
ck("C10 上证读数一致", abs(q["000001"]["px"] - 3681.31) < 0.01, str(q["000001"]["px"]))
ck("C11 创业板读数一致", abs(q["399006"]["px"] - 2599.87) < 0.01, str(q["399006"]["px"]))
ck("C12 池中位一致", abs(probe["pool_now"]["median"] - 0.95) < 0.01, str(probe["pool_now"]["median"]))
ck("C13 三池口径一致", probe["pools"]["zt"] == 50 and probe["pools"]["zb"] == 14 and probe["pools"]["dt"] == 0)
ck("C14 汽车零部14只/最高4板", len(probe2["auto_parts"]) == 14 and probe2["auto_lb_max"] == 4)
ck("C15 汽车零部首封≤13:24计数=13",
   sum(1 for a in probe2["auto_parts"] if a["fbt"] <= 132430) == 13,
   str([a["fbt"] for a in probe2["auto_parts"]]))
# 5 账本闭环
ck("C16 lhb 已清空300296", all(p["code"] != "300296" for p in st["positions"]))
ck("C17 lhb 现金=原+proceeds", abs(st["cash"] - (au["入账前"]["cash"] + f["proceeds"])) < 0.01,
   "%s vs %s" % (st["cash"], au["入账前"]["cash"] + f["proceeds"]))
ck("C18 closed 已追加且pnl一致", st["closed"][-1]["code"] == "300296" and abs(st["closed"][-1]["pnl"] - f["pnl"]) < 0.01)
ck("C19 done 含20261027", "20261027" in st["done"])
ck("C20 备份存在", os.path.exists(os.path.join(SIM, "lhb", "state.json.bak_hbd_20261027")))
# 6 其它账本未被本场修改（仅 300296 一笔）
ck("C21 logic 持仓未动", [p["code"] for p in json.load(open(os.path.join(SIM, "logic", "state.json"), encoding='utf-8'))["positions"]] == ["002979"])
ck("C22 master/auction/limitup 现金未动",
   json.load(open(os.path.join(SIM, "master", "state.json"), encoding='utf-8'))["cash"] == 985361.28 and
   json.load(open(os.path.join(SIM, "auction", "state.json"), encoding='utf-8'))["cash"] == 958628.04 and
   json.load(open(os.path.join(SIM, "limitup", "state.json"), encoding='utf-8'))["cash"] == 989570.98)
# 7 发版不可覆盖（重跑必须 AssertionError）
r = subprocess.run([sys.executable, os.path.join(D, "_hb_d_write.py")], capture_output=True, text=True)
ck("C23 发版不可覆盖(重跑AssertionError)", r.returncode != 0 and "发出版已存在" in (r.stdout + r.stderr),
   (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "")
# 8 决断件字段完整
need = ["date", "session", "ts", "write_ts", "版本", "场次说明", "交易日校验", "数据新鲜度", "权限分级",
        "fills", "fills_汇总", "延误披露", "持仓核_执行前", "防守三查", "环境读数",
        "复盘_上一场清单核销", "观察照会_非条件决断", "异常与欠账", "下一场预置观察条件_非指令", "口径"]
ck("C24 字段齐全", all(k in dec for k in need), ",".join([k for k in need if k not in dec]))
ck("C25 无null/无占位字样", "null" not in json.dumps(dec, ensure_ascii=False) and "待定" not in json.dumps(dec, ensure_ascii=False))
ck("C26 决断时戳唯一对应本场", dec["ts"] == "2026-10-27 13:36:00" and dec["session"] == "hb-d")

print("PASS %d / FAIL %d" % (len(oks), len(fails)))
for n, d in oks:
    print("  OK  ", n, d)
for n, d in fails:
    print("  FAIL", n, d)
print("RESULT:", "PASS" if not fails else "FAIL")
