"""Weekly, dependency-free ingestion of publisher RSS and the arXiv API.

No generated factual summaries: imported entries use <=24 words of publisher text.
Failed feeds preserve existing data and are visible in the published status.
"""
import concurrent.futures
import datetime as dt
import email.utils
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'dist'/'data.json'
TODAY=dt.datetime.now(dt.timezone.utc).date()
# Some Windows Python distributions ship an incomplete CA store. Use Mozilla's
# maintained bundle when available; never disable certificate verification.
try:
    import certifi
    TLS=ssl.create_default_context(cafile=certifi.where())
except ImportError:
    TLS=ssl.create_default_context()
ATOM='{http://www.w3.org/2005/Atom}'
FEEDS=[
    ('OpenAI','https://openai.com/news/rss.xml','News'),
    ('Google AI','https://blog.google/technology/ai/rss/','News'),
    ('Google DeepMind','https://deepmind.google/blog/rss.xml','News'),
    ('arXiv','https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':'(cat:cs.AI OR cat:cs.CL OR cat:cs.LG OR cat:cs.CV) AND submittedDate:['+(TODAY-dt.timedelta(days=14)).strftime('%Y%m%d')+'0000 TO '+TODAY.strftime('%Y%m%d')+'2359]','start':0,'max_results':60,'sortBy':'submittedDate','sortOrder':'descending'}),'Research'),
]

class PlainText(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)

def clean(value):
    parser=PlainText();parser.feed(value or '')
    return re.sub(r'\s+',' ',html.unescape(' '.join(parser.parts))).strip()

def date_value(value):
    try:
        result=dt.datetime.fromisoformat(value.strip().replace('Z','+00:00'))
    except (ValueError,AttributeError):
        result=email.utils.parsedate_to_datetime(value)
    return result.date().isoformat()

def canonical(url):
    parts=urllib.parse.urlsplit(url.strip())
    if parts.scheme not in ('http','https') or not parts.hostname: raise ValueError('Invalid source URL')
    host=parts.hostname.lower()
    if not any(host==d or host.endswith('.'+d) for d in ('arxiv.org','openai.com','blog.google','deepmind.google')):
        raise ValueError('Source outside publisher allowlist')
    path=parts.path.rstrip('/')
    if host.endswith('arxiv.org'):
        host='arxiv.org';path=re.sub(r'v\d+$','',path.replace('/pdf/','/abs/').removesuffix('.pdf'))
    return urllib.parse.urlunsplit(('https',host,path,'',''))

def parse_feed(xml,name,kind):
    root=ET.fromstring(xml)
    if root.tag not in ('rss',ATOM+'feed','{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF'):
        raise ValueError('Not an RSS/Atom feed')
    rows=[]
    nodes=root.findall('.//item') if root.tag!=ATOM+'feed' else root.findall(ATOM+'entry')
    for item in nodes:
        try:
            atom=item.tag==ATOM+'entry'
            title=clean(item.findtext(ATOM+'title' if atom else 'title'))
            rawdate=item.findtext(ATOM+'published' if atom else 'pubDate') or item.findtext(ATOM+'updated')
            date=date_value(rawdate)
            if not ('2021-01-01'<=date<=TODAY.isoformat()):continue
            if atom:
                link=next((x.get('href') for x in item.findall(ATOM+'link') if x.get('rel','alternate')=='alternate'),item.findtext(ATOM+'id'))
                description=item.findtext(ATOM+'summary') or ''
            else:
                link=item.findtext('link');description=item.findtext('description') or ''
            url=canonical(link)
            if not title:continue
            # Retain only a short excerpt, including title in the 24-word budget.
            budget=max(0,24-len(title.split()))
            words=clean(description).split();excerpt=' '.join(words[:budget])
            if len(words)>budget and excerpt:excerpt+='…'
            summary=('Publisher excerpt: '+excerpt) if excerpt else 'See the original publication for details.'
            detected='Models' if kind!='Research' and re.search(r'(?i)(introducing|announcing|launch|release).*(gpt|gemini|model)|^(gpt|gemini)\b',title) else kind
            rows.append(dict(date=date,type=detected,publisher=name,title=title,summary=summary,url=url,automated=True))
        except (ValueError,TypeError,AttributeError):continue
    if not rows:raise ValueError('Feed returned no valid dated entries')
    return rows

def fetch_feed(spec):
    name,url,kind=spec
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'AI-Observatory/1.0 (+https://github.com/pushapgandhi/ai-observatory)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urllib.request.urlopen(request,timeout=35,context=TLS) as response:
                payload=response.read(12_000_001)
            if len(payload)>12_000_000:raise ValueError('Feed exceeds size limit')
            return parse_feed(payload,name,kind),dict(name=name,status='ok',checked=TODAY.isoformat())
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            if attempt<2:time.sleep(2*(attempt+1))
    return [],dict(name=name,status='error',checked=TODAY.isoformat(),error=error)

def merge_entries(existing,incoming):
    result={canonical(e['url']) if e.get('automated') else e['url'].rstrip('/'):e for e in existing}
    for row in incoming:
        key=canonical(row['url'])
        if key not in result or result[key].get('automated'):result[key]=row
    return sorted(result.values(),key=lambda e:(e['date'],e['title']),reverse=True)

def main():
    data=json.loads(DATA.read_text('utf-8'));rows=[];statuses=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for incoming,status in pool.map(fetch_feed,FEEDS):
            rows.extend(incoming);statuses.append(status);print(f"{status['name']}: {status['status']} ({len(incoming)} entries)")
    data['entries']=merge_entries(data['entries'],rows)
    data['feeds']=statuses;data['lastChecked']=TODAY.isoformat()
    if all(s['status']=='ok' for s in statuses):data['lastSuccessfulRefresh']=TODAY.isoformat()
    temp=DATA.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(DATA)
    failures=sum(s['status']!='ok' for s in statuses)
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write(f'degraded={str(bool(failures)).lower()}\n')
    print(f"Archive: {len(data['entries'])} entries; {failures} failed sources")
    return 0 # Publish status and preserved archive even when a source is unavailable.

if __name__=='__main__':sys.exit(main())
