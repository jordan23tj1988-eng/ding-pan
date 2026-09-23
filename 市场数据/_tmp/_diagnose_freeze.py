from pathlib import Path
import sys, json, time
ROOT=Path(r'D:/股票数据/市场数据')
sys.path.insert(0,str(ROOT))
import review_publish
orig=review_publish.hashes
calls=[]
def wrapped(base,names):
    out=orig(base,names)
    calls.append((str(base), out))
    if len(calls)>=2:
        prev=calls[-2][1]
        diff=[k for k in names if prev.get(k)!=out.get(k)]
        print('HASH_CALL',len(calls),base,'diff_from_prev',len(diff),diff[:30],flush=True)
    else:
        print('HASH_CALL',len(calls),base,'count',len(out),flush=True)
    return out
review_publish.hashes=wrapped
res=review_publish.build_release(ROOT,'20260922',publish=False)
print('RESULT',json.dumps(res,ensure_ascii=False)[:5000])
