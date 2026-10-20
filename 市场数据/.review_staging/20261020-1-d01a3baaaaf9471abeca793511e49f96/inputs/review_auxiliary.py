"""Read-only auxiliary page adapter; no financial content edits."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,urlunsplit,quote,unquote
import hashlib,json,re
PAGES={'index.html','cycle.html','auction.html','lhb.html','theme.html','logic.html','limitup.html','intraday.html','history.html'}
MOBILE='@media(max-width:600px){.wrap{width:auto;min-width:0}.card{min-width:0;max-width:100%;overflow-wrap:anywhere}table{display:block;max-width:100%;overflow-x:auto}}'
class Text(HTMLParser):
 def __init__(self):super().__init__();self.body=False;self.skip=0;self.text=[];self.links=[]
 def handle_starttag(self,t,a):
  if t=='body':self.body=True
  if t in ('script','style'):self.skip+=1
  self.links.extend(v for k,v in a if k in ('href','src') and v)
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
  if t=='body':self.body=False
 def handle_data(self,t):
  if self.body and not self.skip:self.text.append(t)
def body_text(text):
 p=Text();p.feed(text);return ''.join(p.text)
def local_missing(out,name):
 p=Text();p.feed((Path(out)/name).read_text(encoding='utf-8'));bad=[]
 for url in p.links:
  u=urlsplit(url)
  if not u.scheme and not u.netloc and u.path and not (Path(out)/unquote(u.path)).exists():bad.append(url)
 return bad
def _url(url):
 p=urlsplit(url);return urlunsplit((p.scheme,p.netloc,quote(unquote(p.path),safe='/:%'),p.query,p.fragment))
def build_auxiliary(source_site,out,origin_base_url):
 source_site=Path(source_site).resolve();out=Path(out).resolve()
 if source_site==out or out.is_relative_to(source_site) or source_site.is_relative_to(out):raise ValueError('auxiliary output overlaps source')
 if urlsplit(origin_base_url).scheme not in ('http','https'):raise ValueError('http(s) origin required')
 out.mkdir(parents=True,exist_ok=True);records=[]
 for name in ('intraday.html','history.html'):
  source=source_site/name;raw=source.read_bytes();text=raw.decode('utf-8')
  def replace(m):
   value=m.group(3);part=urlsplit(value)
   keep=not part.scheme and part.path in PAGES and (out/part.path).exists()
   if value.startswith('#') or part.scheme or part.netloc or keep:return m.group(0)
   return m.group(1)+'='+m.group(2)+_url(urljoin(origin_base_url,value))+m.group(2)
  output=re.sub(r'''\b(href|src)\s*=\s*(["'])(.*?)\2''',replace,text,flags=re.I)
  if name=='intraday.html':output=output.replace('</head>','<style id="review-aux-mobile">'+MOBILE+'</style></head>',1)
  if body_text(output)!=body_text(text):raise ValueError('auxiliary body changed')
  (out/name).write_text(output,encoding='utf-8',newline='\n')
  records.append({'page':name,'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'body_preserved':True,'output_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
 report={'schema_version':1,'status':'pass','kind':'auxiliary-existing-content','origin':origin_base_url,'records':records}
 (out/'auxiliary_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 return report
