import json, re

P = '_学习/judgment_20260901.json'
j = json.load(open(P, encoding='utf-8'))
lu = j['bodies']['limitup']

# 6 blocks by h2 position
b1 = lu[2317:3775]        # 一 质量Top8荐票
b2 = lu[3775:786356]      # 二 全量归位台账 (LEDGER)
b3 = lu[786356:787337]    # 三 训练库
b4 = lu[787337:788332]    # 四 负期望追踪
b5 = lu[788332:789824]    # 五 自主深挖
b6 = lu[789824:]          # 六 认知迭代

def retitle(block, old_title, new_title):
    assert old_title in block, f"找不到标题: {old_title[:20]}"
    return block.replace(old_title, new_title, 1)

# 1. 一 质量Top8荐票 → 一 涨停复盘 · Top8荐票
b1 = retitle(b1, '一 质量Top8荐票', '一 涨停复盘 · Top8荐票')
# 2. 二 全量归位台账 → 三 归位台账 (台账移入板块三)
b2 = retitle(b2, '二 全量归位台账', '三 归位台账')
# 3. 三 训练库 → 四 涨停质量库 · 因子与规则 (合并进质量库)
b3 = retitle(b3, '三 训练库 · 质量库v6因子与规则', '四 涨停质量库 · 因子与规则')
# 4. 四 负期望追踪 → 去掉 h2，内容并入板块四
b4_body = re.sub(r'<h2[^>]*>.*?</h2>', '', b4, count=1, flags=re.S)

new_body = b1 + b2 + b3 + b4_body + b5 + b6

# 校验
def divbal(s):
    return s.count('<div') == s.count('</div>')

print('新 body 长度:', len(new_body))
print('div 平衡:', divbal(new_body), '(<div', new_body.count('<div'), '</div>', new_body.count('</div>'))
print('h2 顺序:')
for m in re.finditer(r'<h2[^>]*>([\s\S]*?)</h2>', new_body):
    t = re.sub(r'<[^>]+>', '', m.group(1)).strip().replace('\n', ' ').replace('\r', ' ')
    print('  ', t[:40])
print('LEDGER锚:', new_body.count('<!--LEDGER-->'), '| chain open:', new_body.count('<details class="chain" open>'))

j['bodies']['limitup'] = new_body
json.dump(j, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已写回 judgment_20260901.json')
