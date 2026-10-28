import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from backend.app import app,state
@pytest.fixture(scope='module')
def client():
 with TestClient(app) as c: yield c
def test_ready(client):
 r=client.get('/api/v1/health'); assert r.status_code==200; assert r.headers.get('x-request-id'); assert r.json()['status']=='ready'
def test_inference(client):
 r=client.post('/api/v1/predict',json={'text':'My new card has not arrived yet. This is disappointing.'}); assert r.status_code==200
 p=r.json()['results'][0]; assert 0<=p['confidence']<=1; assert len(p['top'])>=2
@pytest.mark.parametrize('text',['','   ','12','a'*2001])
def test_invalid(client,text): assert client.post('/api/v1/predict',json={'text':text}).status_code==422
def test_csv(client):
 r=client.post('/api/v1/batch',files={'file':('reviews.csv',b'text\nVery good product and excellent service\nTerrible product and bad service\n','text/csv')}); assert r.status_code==200; assert len(r.json()['results'])==2
@pytest.mark.parametrize('name,content',[('test.txt',b'text\nHello world'),('empty.csv',b''),('bad.csv',b'wrong\nHello world'),('unicode.csv',b'text\n\xff'),('large.csv',b'text\n'+b'x'*1_000_000),('rows.csv',b'text\n'+b'hello world\n'*101)],ids=['extension','empty','header','encoding','size','row_count'])
def test_bad_upload(client,name,content): assert client.post('/api/v1/batch',files={'file':(name,content,'text/csv')}).status_code in (413,422)
def test_unavailable(client):
 state['ready']=False
 try: assert client.post('/api/v1/predict',json={'text':'hello world'}).status_code==503
 finally: state['ready']=True
def test_reports_and_static(client):
 assert client.get('/api/v1/report').status_code==200
 assert client.get('/').status_code==200
 assert client.get('/artifacts/manifest.json').status_code==404
def test_split_isolation():
 import json
 p=Path(__file__).resolve().parents[1]; splits=json.loads((p/'data/splits.json').read_text(encoding='utf-8')); ids={k:{r['id'] for r in v} for k,v in splits.items()}
 assert not ids['train']&ids['validation']; assert not ids['train']&ids['test']; assert not ids['test']&ids['validation']
@pytest.mark.parametrize('failure',['missing_classifier','corrupt_classifier','wrong_classifier_type','missing_encoder'])
def test_startup_artifact_failure_returns_503(client,tmp_path,monkeypatch,failure):
 import shutil,json,joblib
 import backend.app as module
 original=module.P;previous=state.copy()
 (tmp_path/'artifacts').mkdir();(tmp_path/'reports').mkdir()
 shutil.copyfile(original/'artifacts/manifest.json',tmp_path/'artifacts/manifest.json')
 shutil.copyfile(original/'reports/metrics.json',tmp_path/'reports/metrics.json')
 name=json.loads((tmp_path/'artifacts/manifest.json').read_text())['selected_model']
 target=tmp_path/f'artifacts/{name}.joblib'
 if failure=='corrupt_classifier':target.write_bytes(b'not a valid model')
 elif failure=='wrong_classifier_type':
  joblib.dump({'invalid':'model'},target)
  # Use the already-loaded encoder to reach the classifier probe without another copy.
  monkeypatch.setattr(module,'SentenceTransformer',lambda *a,**kw:previous['encoder'])
 elif failure=='missing_encoder':shutil.copyfile(original/f'artifacts/{name}.joblib',target)
 monkeypatch.setattr(module,'P',tmp_path)
 try:
  with TestClient(app) as failed:
   r=failed.get('/api/v1/health');assert r.status_code==503;assert r.json()['status']=='unavailable'
   assert failed.post('/api/v1/predict',json={'text':'This request cannot be served'}).status_code==503
 finally:
  state.clear();state.update(previous)
