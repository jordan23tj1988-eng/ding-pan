# -*- coding: utf-8 -*-
"""hb-d 本场自审（哨兵 v2）：发版一致性/账本闭环/零编造抽查/零后视镜/补正闭环/不可覆盖。"""
import json, os, hashlib, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
fails, oks = [], []


def ck(name, cond, detail=""):
    (oks if cond else fails).append((name, detail))


dec_p = os.path.join(D, "临盘决断_20261027_1330.json")
dec = json.load(open(dec_p, encoding='utf-8'))
fix = json.load(open(os.path.join(D, "临盘决断_20261027_1330_补正1.json"), encoding='utf-8'))
probe = json.load(open(os.path.join(D, "_hb_d_probe.json"), encoding='utf-8'))
probe2 = json.load(open(os.path.join(D, "_hb_d_probe2.json"), encoding='utf-8'))
nxt = json.load(open(os.path.join(D, "_hb_d_next.json"), encoding='utf-8'))
st = json.load(open(os.path.join(SIM, "lhb", "state.json"), encoding='utf-8'))
au = json.load(open(os.path.join(D, "入账_20261027_1330.json"), encoding='utf-8'))

f = dec["fills"][0]
q = probe["quotes"]
pn = probe["pool_now"]

ck("C01 唯一fill=300296卖出", len(dec["fills"]) == 1 and f["code"] == "300296" and f["action"] == "fill_sell")
ck("C02 proceeds=px_exec×qty", abs(f["proceeds"] - round(f["px_exec"] * f["qty"], 2)) < 1e-6, str(f["proceeds"]))
ck("C03 pnl=proceeds-cost", abs(f["pnl"] - round(f["proceeds"] - f["cost"], 2)) < 1e-6, str(f["pnl"]))
ck("C04 ret_pct=proceeds/cost-1", abs(f["ret_pct"] - round((f["proceeds"] / f["cost"] - 1) * 100, 2)) < 1e-6, str(f["ret_pct"]))
ck("C05 px_exec=成交tick×(1-0.1%)向下取2位",
   f["px_exec"] == int(nxt["quote"]["300296"]["px"] * 0.999 * 100) / 100.0,
   "决断帧=%s 成交tick=%s exec=%s" % (q["300296"]["px"], nxt["quote"]["300296"]["px"], f["px_exec"]))
ck("C06 成交tick晚于决断时戳", nxt["quote"]["300296"]["t"] > "20261027133600", nxt["quote"]["300296"]["t"])
ck("C07 决断帧≤决断时戳", probe["dec_ts"] >= probe["frames"]["last"] and probe["dec_ts"][:19] == "2026-10-27 13:33:20")
ck("C08 池帧未断更(<600s)", probe["frames"]["age_s"] < 600, "%ss" % probe["frames"]["age_s"])
ck("C09 新鲜度声明=实测", "34s" in dec["数据新鲜度"]["池帧"]["末帧龄_决断时"])
ck("C10 上证读数=决断帧且补正一致", abs(q["000001"]["px"] - 3686.58) < 0.01 and "3686.58" in json.dumps(fix, ensure_ascii=False), str(q["000001"]["px"]))
ck("C11 创业板读数=决断帧且补正一致", abs(q["399006"]["px"] - 2606.88) < 0.01 and "2606.88" in json.dumps(fix, ensure_ascii=False), str(q["399006"]["px"]))
ck("C12 池中位=末帧且补正一致", abs(pn["median"] - 1.65) < 0.01 and "中位 +1.65%" in json.dumps(fix, ensure_ascii=False), str(pn["median"]))
ck("C13 三池口径", probe["pools"]["zt"] == 50 and probe["pools"]["zb"] == 14 and probe["pools"]["dt"] == 0)
ck("C14 汽车零部14只/最高4板", len(probe2["auto_parts"]) == 14 and probe2["auto_lb_max"] == 4)
ck("C15 汽车零部首封≤13:24:30=14只", sum(1 for a in probe2["auto_parts"] if a["fbt"] <= 132430) == 14)
ck("C16 最早/最晚首封=09:30:03/13:24:30",
   min(a["fbt"] for a in probe2["auto_parts"]) == 93003 and max(a["fbt"] for a in probe2["auto_parts"]) == 132430)
ck("C17 发版sha与补正登记一致", fix["依据发版"]["sha256"] == hashlib.sha256(open(dec_p, 'rb').read()).hexdigest())
ck("C18 补正P1-P5齐全", [x["id"] for x in fix["补正清单"]] == ["P1", "P2", "P3", "P4", "P5"])
ck("C19 决断帧对成本-10.34%", abs(round((q["300296"]["px"] / f["buy_px"] - 1) * 100, 2) + 10.34) < 0.011,
   str(round((q["300296"]["px"] / f["buy_px"] - 1) * 100, 2)))
ck("C20 补正后环境读数不含13:36报价", "3681.31" not in json.dumps(fix["补正清单"][0]["改为"]))
ck("C21 lhb已清空300296", all(p["code"] != "300296" for p in st["positions"]))
ck("C22 lhb现金=原+proceeds", abs(st["cash"] - (au["入账前"]["cash"] + f["proceeds"])) < 0.01,
   "%s vs %s" % (st["cash"], au["入账前"]["cash"] + f["proceeds"]))
ck("C23 closed追加且pnl一致", st["closed"][-1]["code"] == "300296" and abs(st["closed"][-1]["pnl"] - f["pnl"]) < 0.01)
ck("C24 done含20261027", "20261027" in st["done"])
ck("C25 备份存在", os.path.exists(os.path.join(SIM, "lhb", "state.json.bak_hbd_20261027")))
ck("C26 logic未动", [p["code"] for p in json.load(open(os.path.join(SIM, "logic", "state.json"), encoding='utf-8'))["positions"]] == ["002979"])
ck("C27 其余三账现金未动",
   json.load(open(os.path.join(SIM, "master", "state.json"), encoding='utf-8'))["cash"] == 985361.28 and
   json.load(open(os.path.join(SIM, "auction", "state.json"), encoding='utf-8'))["cash"] == 958628.04 and
   json.load(open(os.path.join(SIM, "limitup", "state.json"), encoding='utf-8'))["cash"] == 989570.98)
r = subprocess.run([sys.executable, os.path.join(D, "_hb_d_write.py")], capture_output=True, text=True)
ck("C28 发版不可覆盖", r.returncode != 0 and "发出版已存在" in (r.stdout + r.stderr))
r2 = subprocess.run([sys.executable, os.path.join(D, "_hb_d_fix1.py")], capture_output=True, text=True)
ck("C29 补正件不可覆盖", r2.returncode != 0 and "补正件已存在" in (r2.stdout + r2.stderr))
need = ["date", "session", "ts", "write_ts", "版本", "场次说明", "交易日校验", "数据新鲜度", "权限分级",
        "fills", "fills_汇总", "延误披露", "持仓核_执行前", "防守三查", "环境读数",
        "复盘_上一场清单核销", "观察照会_非条件决断", "异常与欠账", "下一场预置观察条件_非指令", "口径"]
ck("C30 字段齐全", all(k in dec for k in need), ",".join([k for k in need if k not in dec]))
ck("C31 无null", "null" not in json.dumps(dec, ensure_ascii=False))

print("PASS %d / FAIL %d" % (len(oks), len(fails)))
for n, d in oks:
    print("  OK  ", n, d)
for n, d in fails:
    print("  FAIL", n, d)
print("RESULT:", "PASS" if not fails else "FAIL")
