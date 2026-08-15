from __future__ import annotations
from urllib.parse import quote_plus
import feedparser

from .common import parse_datetime, strip_html, canonical_url, stable_id, utcnow_iso

GOOGLE_NEWS = 'https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en'

def source_url(src: dict) -> str:
    kind = src.get('type','google_news')
    if kind == 'google_news':
        return GOOGLE_NEWS.format(q=quote_plus(src['query']))
    return src['url']

def collect_source(src: dict):
    url = source_url(src)
    feed = feedparser.parse(url, request_headers={'User-Agent':'IndiaVCMNews/1.0'})
    if getattr(feed,'bozo',False) and not getattr(feed,'entries',[]):
        raise RuntimeError(str(getattr(feed,'bozo_exception','feed parse failed')))
    rows=[]
    for e in list(feed.entries)[:int(src.get('max_items',40))]:
        title = strip_html(e.get('title',''))
        link = canonical_url(e.get('link',''))
        if not title or not link:
            continue
        summary = strip_html(e.get('summary') or e.get('description') or '')[:700]
        publisher = None
        source = e.get('source')
        if isinstance(source,dict):
            publisher = source.get('title')
        publisher = strip_html(publisher or src.get('name') or '')
        published = parse_datetime(e.get('published') or e.get('updated')) or utcnow_iso()
        rows.append({
            'id': stable_id(link), 'title': title, 'url': link, 'source': publisher,
            'published': published, 'summary': summary, 'collected_at': utcnow_iso(),
            '_collector_source_id': src.get('id'), '_collector_source_name': src.get('name'),
            '_priority': float(src.get('priority',1.0)), '_official': bool(src.get('official',False)),
        })
    return rows, {'id':src.get('id'),'name':src.get('name'),'url':url,'ok':True,'items_raw':len(rows),'error':None}
