from __future__ import annotations
from .common import norm, phrase_present
import re

def score_item(item: dict, cfg: dict, gazetteer: dict, entity_index: dict):
    rel = cfg.get('relevance',{})
    text = norm((item.get('title') or '') + ' ' + (item.get('summary') or ''))
    score = 0.0
    reasons=[]
    for phrase,w in (rel.get('positive') or {}).items():
        if phrase_present(text,phrase):
            score += float(w); reasons.append(phrase)
    india_hit=False
    for phrase,w in (rel.get('india') or {}).items():
        if phrase_present(text,phrase):
            score += float(w); india_hit=True; reasons.append(phrase)
    # Geography/entity mentions count as India evidence even if the word India is absent.
    geo_terms=[]
    for x in gazetteer.get('states',[]):
        geo_terms += [x.get('state')] + list(x.get('aliases') or [])
    for x in gazetteer.get('districts',[]):
        geo_terms += [x.get('district')] + list(x.get('aliases') or [])
    for term in geo_terms:
        if term and len(str(term))>=4 and phrase_present(text,str(term)):
            score += 2.0; india_hit=True; reasons.append('India geography'); break
    # Direct project IDs/names are very strong relevance evidence.
    direct_project=False
    for p in entity_index.get('projects',[]):
        pid=str(p.get('id') or '').strip()
        name=str(p.get('name') or '').strip()
        pidn=norm(pid)
        pid_hit=bool(pid and (phrase_present(text,pid) or (re.fullmatch(r'([a-z]+)[ ._-]*(\d+)',pidn) and re.search(r'(?<![a-z0-9])'+re.escape(re.fullmatch(r'([a-z]+)[ ._-]*(\d+)',pidn).group(1))+r'[ ._-]*'+re.escape(re.fullmatch(r'([a-z]+)[ ._-]*(\d+)',pidn).group(2))+r'(?![a-z0-9])',text))))
        if pid_hit:
            score += 8; india_hit=True; direct_project=True; reasons.append('project id'); break
        if len(name)>=18 and phrase_present(text,name):
            score += 7; india_hit=True; direct_project=True; reasons.append('project name'); break
    for phrase,w in (rel.get('negative') or {}).items():
        if phrase_present(text,phrase):
            score += float(w); reasons.append('noise:'+phrase)
    score *= float(item.get('_priority',1.0))
    threshold=float(rel.get('official_threshold' if item.get('_official') else 'threshold',5.0))
    # Generic global carbon-market news is not published unless there is India evidence,
    # a direct project match, or the source is an India-specific official query.
    india_query = item.get('_collector_source_id') in {'bee_official','pib_official','moefcc_official','india_vcm_core','india_carbon_market_policy','india_article6','verra_india','gold_standard_india','india_project_sectors','india_business_press','reuters_india','mongabay_india','downtoearth_india'}
    accepted = score >= threshold and (india_hit or direct_project or india_query)
    return round(score,2), sorted(set(reasons)), accepted

def classify_item(item: dict, cfg: dict):
    text=norm((item.get('title') or '')+' '+(item.get('summary') or ''))
    best=('Other',0)
    tags=[]
    for cat, terms in (cfg.get('categories') or {}).items():
        hits=sum(1 for t in terms if phrase_present(text,t))
        if hits:
            tags.extend([t for t in terms if phrase_present(text,t)])
        if hits>best[1]: best=(cat,hits)
    return best[0], sorted(set(tags))[:12]
