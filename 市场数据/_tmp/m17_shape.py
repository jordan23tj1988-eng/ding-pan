import json
d=json.load(open('_学习/总审_20261022.json',encoding='utf-8'))
def shape(v):
    if isinstance(v,dict): return {k:shape(vv) for k,vv in list(v.items())[:40]}
    if isinstance(v,list): return [shape(v[0])] if v else ['EMPTY']
    if isinstance(v,str): return 'STR:'+(v[:50].replace('\n',' '))
    return type(v).__name__+':'+str(v)
out={k:shape(v) for k,v in d.items()}
open('_tmp/shape.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=1))
print('ok')
