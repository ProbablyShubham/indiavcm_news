from __future__ import annotations
from collections import defaultdict
from .common import norm, phrase_present, load_yaml, ROOT
import re

def _aliases():
    return load_yaml(ROOT/'config'/'geography_aliases.yml')

def _pid_present(text, pid):
    p=norm(pid)
    if phrase_present(text,p): return True
    m=re.fullmatch(r'([a-z]+)[ ._-]*(\d+)',p)
    if m:
        return re.search(r'(?<![a-z0-9])'+re.escape(m.group(1))+r'[ ._-]*'+re.escape(m.group(2))+r'(?![a-z0-9])',text) is not None
    return False

def extract_entities(item: dict, entity_index: dict):
    text = norm((item.get('title') or '')+' '+(item.get('summary') or ''))
    projects=[]; developers=[]; methods=[]; registries=[]
    for p in entity_index.get('projects',[]):
        pid=str(p.get('id') or '').strip(); name=str(p.get('name') or '').strip()
        if (pid and _pid_present(text,pid)) or (len(name)>=18 and phrase_present(text,name)):
            projects.append(pid)
    for d in entity_index.get('developers',[]):
        name=str(d.get('name') if isinstance(d,dict) else d or '').strip()
        if len(name)>=6 and phrase_present(text,name): developers.append(name)
    for m in entity_index.get('methodologies',[]):
        name=str(m.get('name') if isinstance(m,dict) else m or '').strip()
        if len(name)>=4 and phrase_present(text,name): methods.append(name)
    for r in entity_index.get('registries',[]):
        name=str(r.get('name') if isinstance(r,dict) else r or '').strip()
        if name and phrase_present(text,name): registries.append(name)
    # Common registry aliases.
    if phrase_present(text,'Verra') or phrase_present(text,'Verified Carbon Standard') or phrase_present(text,'VCS'):
        if 'Verra' not in registries: registries.append('Verra')
    if phrase_present(text,'Gold Standard') and 'Gold Standard' not in registries: registries.append('Gold Standard')
    return {'projects':projects[:20],'developers':developers[:20],'methodologies':methods[:20],'registries':registries[:10]}

def geolocate(item: dict, gazetteer: dict, entity_index: dict, entities: dict):
    text=norm((item.get('title') or '')+' '+(item.get('summary') or ''))
    projects_by_id={str(p.get('id')):p for p in entity_index.get('projects',[]) if p.get('id')}
    # A direct project mention is the only case where article placement may use the project's site point.
    for pid in entities.get('projects',[]):
        p=projects_by_id.get(str(pid))
        if p:
            lat=p.get('lat'); lon=p.get('lon')
            if lat is not None and lon is not None:
                return {'level':'project','project_id':str(pid),'district':p.get('district'),'state':p.get('state'),
                        'lat':lat,'lon':lon,'method':'project_match','confidence':'high'}
    aliases=_aliases(); d_alias=aliases.get('district_aliases') or {}; s_alias=aliases.get('state_aliases') or {}
    states=gazetteer.get('states',[]) or []
    districts=gazetteer.get('districts',[]) or []
    state_hits=[]
    for st in states:
        names=[st.get('state')]+list(st.get('aliases') or [])
        names += [a for a,c in s_alias.items() if norm(c)==norm(st.get('state'))]
        if any(n and phrase_present(text,n) for n in names): state_hits.append(st)
    # District names may be duplicated across states. Require state evidence if ambiguous.
    by_name=defaultdict(list)
    for d in districts:
        names=[d.get('district')]+list(d.get('aliases') or [])
        names += [a for a,c in d_alias.items() if norm(c)==norm(d.get('district'))]
        for n in names:
            if n: by_name[norm(n)].append((d,n))
    candidates=[]
    for key, arr in by_name.items():
        if key and phrase_present(text,key):
            for d,matched in arr: candidates.append((d,matched,len(arr)))
    if candidates:
        # Prefer candidates whose state is explicitly present; then unambiguous district names.
        for d,matched,n in candidates:
            if any(norm(s.get('state'))==norm(d.get('state')) for s in state_hits):
                return {'level':'district','district':d.get('district'),'state':d.get('state'),'lat':d.get('lat'),'lon':d.get('lon'),
                        'method':'gazetteer_alias' if norm(matched)!=norm(d.get('district')) else 'gazetteer_exact','confidence':'high'}
        unamb=[x for x in candidates if x[2]==1]
        if unamb:
            d,matched,_=unamb[0]
            return {'level':'district','district':d.get('district'),'state':d.get('state'),'lat':d.get('lat'),'lon':d.get('lon'),
                    'method':'gazetteer_alias' if norm(matched)!=norm(d.get('district')) else 'gazetteer_exact','confidence':'high'}
    if state_hits:
        st=state_hits[0]
        return {'level':'state','district':None,'state':st.get('state'),'lat':st.get('lat'),'lon':st.get('lon'),'method':'state_only','confidence':'medium'}
    if phrase_present(text,'India') or phrase_present(text,'Indian'):
        return {'level':'national','district':None,'state':None,'lat':None,'lon':None,'method':'india_only','confidence':'medium'}
    return {'level':'unresolved','district':None,'state':None,'lat':None,'lon':None,'method':'none','confidence':'low'}
