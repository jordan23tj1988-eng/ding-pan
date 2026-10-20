# -*- coding: utf-8 -*-
"""_jsonl_append.py —— jsonl 去重追加门禁(共享, 2026-08-16 建)。
四条结算脚本(质量/题材/逻辑/席位)追加 jsonl 前先按 key 去重,
防"同日重复跑脚本"导致重复样本污染下游统计/训练/权重重训。
key 语义: 字段名(str, 如 '荐票日') 或 字段名元组(tuple, 如 ('荐票日','代码'))。
幂等: 同 key 记录已存在则跳过, 不改动文件内容与顺序。
"""
import os
import json


def _read_keys(path, keys):
    """读现有 jsonl 的全部 key 集合(容错: 坏行跳过)。"""
    s = set()
    if not os.path.isfile(path):
        return s
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                k = tuple(r.get(x) for x in keys) if isinstance(keys, tuple) else r.get(keys)
                if k is not None:
                    s.add(k)
    except Exception:
        pass
    return s


def append_dedup(path, obj, keys):
    """按 keys 去重追加 obj。已存在同 key 记录则跳过(幂等), 否则 append 一行。
    keys: '荐票日' 或 ('荐票日','代码')。
    返回 True=已写入, False=重复已跳过。"""
    if isinstance(keys, tuple):
        k = tuple(obj.get(x) for x in keys)
    else:
        k = obj.get(keys)
    if k is not None and k in _read_keys(path, keys):
        return False
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return True
