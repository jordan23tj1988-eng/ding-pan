# -*- coding: utf-8 -*-
"""补产 题材生命周期判断_20260819.json（2026-08-19 第三日复发·当日救火）
来源=theme_body_20260819.html "三 主流生命周期"段 LLM 原文逐字提取, 零编造
根因: jobs.json 内嵌 prompt 缺两结构化 json 硬要求 → 子 agent 漏产 → 8/18 修复改错文件(daily_prompt_new.txt 非 cron 真源)
"""
import json, os, re

R = r'D:\股票数据\市场数据'
L = os.path.join(R, '_学习')
d = '20260819'

bp = os.path.join(L, f'theme_body_{d}.html')
body = open(bp, encoding='utf-8').read()

# 提取"三 主流生命周期"段（<h2>三 ... </h2> 到 <h2>四）
i = body.find('<h2>三')
j = body.find('<h2>四', i)
assert i >= 0 and j > i, f'三/四段定位失败 i={i} j={j}'
seg3 = body[i:j]

# 解析表格行: <tr><td>线名</td><td class="red|yel">定性</td><td>机械阶段</td><td>判据</td></tr>
rows = re.findall(r'<tr><td>(.*?)</td><td class="[^"]*">(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', seg3, re.DOTALL)
assert len(rows) == 5, f'预期5行实际{len(rows)}'
life = {}
for nm, qual, mech, jud in rows:
    nm = re.sub(r'<.*?>', '', nm).strip()
    qual = re.sub(r'<.*?>', '', qual).strip()
    jud = re.sub(r'<.*?>', '', jud).strip()
    life[nm] = {'定性': qual, '判据': jud}

# 高低切: 取"次日高低切预判"整句
m = re.search(r'<li><b>次日高低切预判:</b>\s*(.*?)</li>', seg3, re.DOTALL)
assert m, '次日高低切预判未找到'
gaoqie = re.sub(r'<.*?>', '', m.group(1)).strip()

out = {
    '日期': d, '路': 'theme',
    '来源': f'theme_body_{d}.html 三段(主流生命周期) LLM原文逐字提取, 补跑于2026-08-19(键=6有题材聚类口径)',
    '逐线判断': life,
    '高低切': gaoqie,
}
json.dump(out, open(os.path.join(L, f'题材生命周期判断_{d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('补产完成: 逐线判断 %d 条 + 高低切' % len(life))
for k, v in life.items():
    print(' ', k, '|', v['定性'], '|', v['判据'][:40])
print('高低切:', gaoqie[:80])
