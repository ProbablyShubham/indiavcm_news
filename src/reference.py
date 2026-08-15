from __future__ import annotations
import os
from pathlib import Path
import requests

from .common import ROOT, load_json, write_json, utcnow_iso

DEFAULT_BASES = [
    'https://indiavcm.com/data/reference/',
    'https://probablyshubham.github.io/indiavcm_test/data/reference/',
]

def _bases():
    raw = os.getenv('VCM_REFERENCE_BASES','').strip()
    if raw:
        return [x.strip().rstrip('/') + '/' for x in raw.split(';') if x.strip()]
    return DEFAULT_BASES

def _fetch_json(url: str):
    r = requests.get(url, timeout=25, headers={'User-Agent':'IndiaVCMNews/1.0 (+https://indiavcm.com)'})
    r.raise_for_status()
    return r.json()

def load_reference_bundle():
    gaz = ent = None
    used = None
    errors = []
    for base in _bases():
        try:
            g = _fetch_json(base + 'india_news_gazetteer.json')
            e = _fetch_json(base + 'news_entity_index.json')
            if isinstance(g,dict) and isinstance(e,dict):
                gaz, ent, used = g, e, base
                break
        except Exception as exc:
            errors.append(f'{base}: {exc}')
    if gaz is None:
        gaz = load_json(ROOT/'reference'/'india_news_gazetteer.json', {'states':[],'districts':[]})
        ent = load_json(ROOT/'reference'/'news_entity_index.json', {'projects':[],'developers':[],'methodologies':[],'registries':[]})
        used = 'repository fallback'
    # Keep a copy of the last working live reference for resilience.
    if gaz and (gaz.get('states') or gaz.get('districts')):
        write_json(ROOT/'reference'/'live_india_news_gazetteer.json', gaz)
        write_json(ROOT/'reference'/'live_news_entity_index.json', ent)
    else:
        lg = load_json(ROOT/'reference'/'live_india_news_gazetteer.json')
        le = load_json(ROOT/'reference'/'live_news_entity_index.json')
        if lg and le:
            gaz, ent, used = lg, le, 'last working repository cache'
    return gaz or {'states':[],'districts':[]}, ent or {'projects':[]}, {'base':used,'errors':errors,'loaded_at':utcnow_iso()}
