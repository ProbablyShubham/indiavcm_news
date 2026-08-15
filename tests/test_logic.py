import json
from pathlib import Path
from src.common import ROOT
from src.relevance import score_item, classify_item
from src.geolocate import extract_entities, geolocate
from src.common import load_yaml

def main():
    fx=json.loads((ROOT/'tests/fixtures/sample_reference.json').read_text())
    cfg=load_yaml(ROOT/'config/terms.yml')
    item={'title':'Verra project VCS1234 expands carbon credit activity in Jaisalmer, Rajasthan','summary':'Indian voluntary carbon market update','_priority':1,'_official':False,'_collector_source_id':'india_vcm_core'}
    sc,rs,ok=score_item(item,cfg,fx['gazetteer'],fx['entities']); assert ok and sc>5
    ent=extract_entities(item,fx['entities']); assert 'VCS1234' in ent['projects'] and 'Verra' in ent['registries']
    geo=geolocate(item,fx['gazetteer'],fx['entities'],ent); assert geo['level']=='project' and geo['project_id']=='VCS1234'
    cat,tags=classify_item(item,cfg); assert isinstance(cat,str)
    print('logic tests passed',sc,cat,geo)
if __name__=='__main__':main()
