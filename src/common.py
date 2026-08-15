from __future__ import annotations
import hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import yaml
from unidecode import unidecode

ROOT = Path(__file__).resolve().parents[1]

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def load_yaml(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default

def write_json(path: Path, obj, *, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, separators=(',',':') if compact else None, indent=None if compact else 2)
    path.write_text(txt + ('\n' if not compact else ''), encoding='utf-8')

def norm(text: str) -> str:
    s = unidecode(str(text or '')).lower()
    s = s.replace('&',' and ')
    s = re.sub(r"[^a-z0-9+.-]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def phrase_present(text_norm: str, phrase: str) -> bool:
    p = norm(phrase)
    if not p:
        return False
    return re.search(r'(?<![a-z0-9])' + re.escape(p) + r'(?![a-z0-9])', text_norm) is not None

def strip_html(value: str) -> str:
    s = html.unescape(str(value or ''))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def canonical_url(url: str) -> str:
    try:
        p = urlsplit(url)
        drop = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content','gclid','fbclid','mc_cid','mc_eid'}
        q = [(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in drop]
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/') or '/', urlencode(q, doseq=True), ''))
    except Exception:
        return str(url or '')

def stable_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode('utf-8')).hexdigest()[:24]

def title_signature(title: str) -> str:
    t = norm(title)
    # Google News titles often end with " - Publisher". Keep the semantic side.
    t = re.sub(r'\s+-\s+[a-z0-9 .&_-]{2,80}$', '', t)
    stop = {'the','a','an','to','of','for','in','on','and','with','from','by','as','at','is','are','its'}
    toks = [x for x in re.findall(r'[a-z0-9]+', t) if x not in stop]
    return ' '.join(toks[:24])

def parse_datetime(value) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        dt = None
        for candidate in (s, s.replace('Z','+00:00')):
            try:
                dt = datetime.fromisoformat(candidate)
                break
            except Exception:
                pass
        if dt is None:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(s)
            except Exception:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
