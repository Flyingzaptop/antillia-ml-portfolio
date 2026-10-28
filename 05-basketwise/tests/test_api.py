from fastapi.testclient import TestClient
from backend.app import app,state
client=TestClient(app)
def test_cold_start_and_exclusion():
    d=client.post('/api/v1/predict',json={}).json();assert d['cold_start'];assert len(d['items'])==8
    chosen=d['items'][0]['id'];r=client.post('/api/v1/predict',json={'items':[chosen]})
    assert r.status_code==200;assert chosen not in [v['id'] for v in r.json()['items']];assert not r.json()['cold_start']
def test_invalid_inputs_rejected():
    for q in [{'items':['../../etc/passwd']},{'k':0},{'k':100},{'items':['x']*101},{'extra':1}]:
        assert client.post('/api/v1/predict',json=q).status_code==422
def test_catalog_search_and_limits():
    assert client.get('/api/v1/catalog',params={'limit':101}).status_code==422
    d=client.get('/api/v1/catalog',params={'q':'HEART','limit':10}).json();assert d['items'];assert all('HEART' in x['name'] for x in d['items'])
def test_split_target_disjoint_from_history():
    _,_,_,groups=state()
    for p in ['validation','test']:
        for case in groups[p]['warm']:assert not(set(case['history'])&set(case['target']))
def test_duplicates_and_stable_ranking():
    product=state()[0][0]['id']
    a=client.post('/api/v1/predict',json={'items':[product]}).json();b=client.post('/api/v1/predict',json={'items':[product,product]}).json()
    assert [p['id'] for p in a['items']]==[p['id'] for p in b['items']]
def test_no_model_exposure():
    assert client.get('/artifacts/weights.npz').status_code==404
    assert client.get('/api/v1/health').headers['x-request-id']
def test_missing_model_returns_unavailable(monkeypatch):
    import importlib
    module=importlib.import_module('backend.app')
    def unavailable():raise FileNotFoundError('missing model')
    monkeypatch.setattr(module,'state',unavailable)
    assert client.get('/api/v1/health').status_code==503
