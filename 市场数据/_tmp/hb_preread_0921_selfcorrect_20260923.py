# -*- coding: utf-8 -*-
"""20260923 竞价预读场(09:21)本场自纠: 同一执行实例内的自纠(非覆盖他场发出版).
更正 3 项: ①两处字典键残留格式化占位符 '%d' → 写入真实计数; ②盲区时长笔误 24 秒 → 243 秒(09:20:57→09:25:00 实测);
③补记更正溯源(更正前版本 sha256 + 更正项明细)。其余结论/数字不变。
"""
import json, os, hashlib, datetime
sys_path = r"D:\股票数据\市场数据\盘中\20260923\临盘决断_20260923_0921.json"
before = open(sys_path, "rb").read()
h_before = hashlib.sha256(before).hexdigest()
d = json.loads(before.decode("utf-8"))

blk = d["决策窗内竞价读数(全池, ≤09:21:00)"]
decay = blk.pop("衰减组(63秒 Δ≤-0.5pp, 共 %d 只)")
surge = blk.pop("上冲组(63秒 Δ≥+0.5pp, 共 %d 只)")
blk["衰减组(63秒 Δ≤-0.5pp, 共 %d 只)" % len(decay)] = decay
blk["上冲组(63秒 Δ≥+0.5pp, 共 %d 只)" % len(surge)] = surge

fixed = []


def fix(obj, old, new, label):
    """递归替换字符串"""
    n = 0
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and old in v:
                obj[k] = v.replace(old, new)
                n += 1
            else:
                n += fix(v, old, new, label)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and old in v:
                obj[i] = v.replace(old, new)
                n += 1
            else:
                n += fix(v, old, new, label)
    if n:
        fixed.append("%s (%d 处)" % (label, n))
    return n


fix(d, "有 24 秒不可观测", "有 243 秒不可观测(09:20:57→09:25:00, 其中 09:21:00 之后的 240 秒依零后视镜铁律不得使用)", "盲区时长 24 秒→243 秒")
fix(d, "并明确标注 24 秒盲区", "并明确标注 243 秒盲区", "盲区时长 24 秒→243 秒")
fix(d, "末 24 秒不可观测", "末 243 秒不可观测", "盲区时长 24 秒→243 秒")

d["本场自纠"] = (
    "同一执行实例内自纠(非覆盖他场发出版): 本文件首次落盘后 %s 内在本场复核中发现 3 类问题并就地更正 —— "
    "①『决策窗内竞价读数』两块(衰减组/上冲组)字典键残留格式化占位符 '%%d' 未代入真实计数, 已改为实际计数(衰减 %d 只 / 上冲 %d 只, 数据本体未变); "
    "②盲区时长笔误: 原写『24 秒不可观测』, 实测 09:20:57(末条可见 tick)→09:25:00(竞价终值) = **243 秒**, 已按实测更正(3 处); "
    "③补记本溯源: 更正前版本 sha256=%s(字节数 %d), 更正后重算 sha256 见『本场自纠.更正后sha256』。"
    "更正仅涉表述/键名, **全部结论、条件决断=[]、落点预判、报警清单均未改动**。"
) % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(decay), len(surge), h_before, len(before))

out = json.dumps(d, ensure_ascii=False, indent=1)
h_after = hashlib.sha256(out.encode("utf-8")).hexdigest()
d["本场自纠"] += " 更正后sha256=" + h_after
out = json.dumps(d, ensure_ascii=False, indent=1)
open(sys_path, "w", encoding="utf-8").write(out)

print("更正项:", fixed)
print("键名:", [k for k in blk if k.startswith(("衰减组", "上冲组"))])
print("sha256 前/后:", h_before[:16], hashlib.sha256(open(sys_path, "rb").read()).hexdigest()[:16])
print("文件大小:", os.path.getsize(sys_path))
