import json, shutil, tempfile, sys, types
from pathlib import Path
sys.modules.setdefault("feedparser", types.SimpleNamespace())
import src.build_feed as bf

ROOT_ORIG=bf.ROOT
fixture=json.loads((ROOT_ORIG/'tests/fixtures/sample_reference.json').read_text())

def fake_collect(src):
    rows=[{
      'id':'abc123','title':'India carbon credits: Verra project VCS 1234 expands in Jaisalmer, Rajasthan',
      'url':'https://example.com/story','source':'Example News','published':'2026-08-14T12:00:00Z',
      'summary':'Example Renewables says its voluntary carbon market project uses ACM0002.',
      'collected_at':'2026-08-14T13:00:00Z','_collector_source_id':src.get('id'),'_collector_source_name':src.get('name'),
      '_priority':1.0,'_official':False
    }]
    return rows,{'id':src.get('id'),'name':src.get('name'),'url':'fixture','ok':True,'items_raw':1,'error':None}

def main():
    td=Path(tempfile.mkdtemp(prefix='indiavcm_news_test_'))
    try:
        (td/'config').mkdir();(td/'state').mkdir();(td/'archive').mkdir()
        for name in ['sources.yml','terms.yml','source_weights.yml']:
            shutil.copy(ROOT_ORIG/'config'/name,td/'config'/name)
        (td/'state/news_store.json').write_text('{"schema_version":2,"items":[]}')
        bf.ROOT=td
        bf.collect_source=fake_collect
        bf.load_reference_bundle=lambda:(fixture['gazetteer'],fixture['entities'],{'base':'fixture','errors':[]})
        bf.main()
        feed=json.loads((td/'news.json').read_text())
        assert feed['items'] and feed['items'][0]['geo']['level']=='project'
        assert 'VCS1234' in feed['items'][0]['entities']['projects']
        assert feed['items'][0]['event_id'].startswith('evt_')
        print('offline end-to-end feed test passed:',feed['items'][0]['title'])
    finally:
        bf.ROOT=ROOT_ORIG
        shutil.rmtree(td,ignore_errors=True)
if __name__=='__main__':main()
