from __future__ import annotations
import gzip, json, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .common import ROOT, load_yaml, load_json, write_json, utcnow_iso
from .collect import collect_source
from .reference import load_reference_bundle
from .relevance import score_item, classify_item
from .geolocate import extract_entities, geolocate
from .deduplicate import deduplicate

WINDOW_DAYS=int(os.getenv('NEWS_WINDOW_DAYS','90'))
STORE_DAYS=int(os.getenv('NEWS_STORE_DAYS','180'))

def dt(s):
    try:return datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except:return datetime.now(timezone.utc)

def main():
    sources=(load_yaml(ROOT/'config'/'sources.yml').get('sources') or [])
    terms=load_yaml(ROOT/'config'/'terms.yml')
    publisher_weights=(load_yaml(ROOT/'config'/'source_weights.yml').get('weights') or {})
    gaz, entities_idx, refmeta=load_reference_bundle()
    raw=[]; health=[]
    for src in sources:
        try:
            rows,h=collect_source(src); raw.extend(rows); health.append(h)
        except Exception as exc:
            health.append({'id':src.get('id'),'name':src.get('name'),'url':None,'ok':False,'items_raw':0,'error':str(exc)[:300]})
    accepted=[]
    for x in raw:
        pub=str(x.get('source') or '')
        for label,mult in publisher_weights.items():
            if label.lower() in pub.lower():
                x['_priority']=float(x.get('_priority',1.0))*float(mult); break
        score,reasons,ok=score_item(x,terms,gaz,entities_idx)
        if not ok: continue
        category,tags=classify_item(x,terms)
        ent=extract_entities(x,entities_idx)
        geo=geolocate(x,gaz,entities_idx,ent)
        x.update({'relevance_score':score,'relevance_reasons':reasons,'category':category,'tags':tags,'entities':ent,'geo':geo})
        accepted.append(x)
    accepted=deduplicate(accepted)
    # Merge with previous store so short RSS windows do not erase recent intelligence.
    store=load_json(ROOT/'state'/'news_store.json',{'schema_version':2,'items':[]}) or {'items':[]}
    merged={x['id']:x for x in store.get('items',[]) if x.get('id')}
    for x in accepted: merged[x['id']]=x
    cutoff=datetime.now(timezone.utc)-timedelta(days=STORE_DAYS)
    merged=[x for x in merged.values() if dt(x.get('published'))>=cutoff]
    merged=deduplicate(merged)
    write_json(ROOT/'state'/'news_store.json',{'schema_version':2,'generated_at':utcnow_iso(),'items':merged})
    public_cutoff=datetime.now(timezone.utc)-timedelta(days=WINDOW_DAYS)
    public=[x for x in merged if dt(x.get('published'))>=public_cutoff]
    # Strip internal collector fields from public output.
    for x in public:
        for k in list(x):
            if k.startswith('_'): x.pop(k,None)
    feed={'schema_version':2,'generated_at':utcnow_iso(),'window_days':WINDOW_DAYS,'items':public}
    write_json(ROOT/'news.json',feed,compact=True)
    levels=['project','district','state','national','unresolved']
    counts={'total':len(public),'mapped':sum(1 for x in public if (x.get('geo') or {}).get('lat') is not None)}
    counts.update({k:sum(1 for x in public if (x.get('geo') or {}).get('level')==k) for k in levels})
    # Add per-source accepted counts.
    acc_by={}
    for x in accepted:
        sid=x.get('_collector_source_id');acc_by[sid]=acc_by.get(sid,0)+1
    for h in health:
        h['items']=acc_by.get(h.get('id'),0)
        h['last_success']=feed['generated_at'] if h.get('ok') else None
    meta={'schema_version':2,'generated_at':feed['generated_at'],'sources':health,'counts':counts,
          'reference':refmeta,'window_days':WINDOW_DAYS,
          'pipeline':{'raw_items':len(raw),'accepted_this_run':len(accepted),'stored_items':len(merged)}}
    write_json(ROOT/'news_meta.json',meta)
    # One compressed snapshot per UTC day; repeated runs overwrite the same day's archive.
    adir=ROOT/'archive';adir.mkdir(exist_ok=True)
    ap=adir/f"news_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json.gz"
    with gzip.open(ap,'wt',encoding='utf-8') as f: json.dump(feed,f,ensure_ascii=False,separators=(',',':'))
    # prune old archives
    for p in adir.glob('news_*.json.gz'):
        try:
            day=datetime.strptime(p.stem.replace('news_','').replace('.json',''),'%Y-%m-%d').replace(tzinfo=timezone.utc)
            if day < datetime.now(timezone.utc)-timedelta(days=STORE_DAYS): p.unlink()
        except Exception: pass
    print(json.dumps({'raw':len(raw),'accepted':len(accepted),'published':len(public),'counts':counts,'reference':refmeta.get('base')},indent=2))

if __name__=='__main__': main()
