from __future__ import annotations
from difflib import SequenceMatcher
from .common import title_signature

def _sim(a,b):
    if not a or not b: return 0.0
    sa,sb=set(a.split()),set(b.split())
    jac=len(sa&sb)/max(1,len(sa|sb))
    seq=SequenceMatcher(None,a,b).ratio()
    return max(jac,seq)

def deduplicate(items):
    # Exact URL IDs first.
    by_id={}
    for x in sorted(items,key=lambda z:z.get('published',''),reverse=True):
        by_id.setdefault(x['id'],x)
    rows=list(by_id.values())
    kept=[]
    for x in sorted(rows,key=lambda z:(float(z.get('relevance_score',0)),z.get('published','')),reverse=True):
        sig=title_signature(x.get('title',''))
        dup=None
        for y in kept:
            if _sim(sig,title_signature(y.get('title','')))>=0.90:
                dup=y;break
        if dup is None:
            kept.append(x)
        else:
            # Preserve additional publisher coverage on the retained event.
            dup.setdefault('other_sources',[])
            if x.get('source') and x.get('source')!=dup.get('source') and x.get('source') not in dup['other_sources']:
                dup['other_sources'].append(x.get('source'))
    # Basic event clusters: looser similarity without removing stories.
    clusters=[]
    for x in kept:
        sig=title_signature(x.get('title',''))
        found=None
        for c in clusters:
            if _sim(sig,c['sig'])>=0.74:
                found=c; break
        if found is None:
            found={'sig':sig,'members':[]};clusters.append(found)
        found['members'].append(x)
    import hashlib
    for c in clusters:
        eid='evt_'+hashlib.sha1(c['sig'].encode()).hexdigest()[:12]
        for x in c['members']: x['event_id']=eid
    return sorted(kept,key=lambda z:z.get('published',''),reverse=True)
