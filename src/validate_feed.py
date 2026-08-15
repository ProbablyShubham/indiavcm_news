from __future__ import annotations
import json
from pathlib import Path
from .common import ROOT

def main():
    feed=json.loads((ROOT/'news.json').read_text())
    meta=json.loads((ROOT/'news_meta.json').read_text())
    assert feed.get('schema_version')==2
    assert isinstance(feed.get('items'),list)
    ids=set()
    allowed={'project','district','state','national','unresolved'}
    for x in feed['items']:
        for k in ('id','title','url','source','published','geo'): assert k in x,(k,x)
        assert x['id'] not in ids;ids.add(x['id'])
        assert (x.get('geo') or {}).get('level') in allowed
    assert isinstance(meta.get('sources'),list)
    print(f"validated {len(feed['items'])} public items / {len(meta['sources'])} configured sources")
if __name__=='__main__':main()
