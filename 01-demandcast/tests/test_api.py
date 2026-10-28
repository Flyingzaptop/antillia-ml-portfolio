import numpy as np
from fastapi.testclient import TestClient
from backend.app import app
from backend.pipeline import ART,tabular
client=TestClient(app)
def test_prediction_is_finite_and_has_24_hours():
    r=client.post('/api/v1/predict',json={'origin_index':0});assert r.status_code==200
    d=r.json();assert len(d['forecast'])==24 and len(d['history'])==168
    assert all(np.isfinite(p[m]) and p[m]>=0 for p in d['forecast'] for m in ['seasonal','boosting','gru'])
    assert r.headers['x-request-id'] and 'nosniff' in r.headers['x-content-type-options']
def test_invalid_origin_and_scale_rejected():
    for q in [{'origin_index':-1},{'origin_index':100000},{'history_scale':0},{'history_scale':2},{'unexpected':True}]:
        assert client.post('/api/v1/predict',json=q).status_code==422
def test_scenario_is_explicit():
    d=client.post('/api/v1/predict',json={'history_scale':1.2}).json();assert d['scenario'] is True
def test_split_horizons_never_cross_boundaries():
    s=np.load(ART/'splits.npz');assert max(s['train_origins'])+24<=min(s['validation_origins'])
    assert max(s['validation_origins'])+24<=min(s['test_origins'])
    assert np.diff(s['test_origins']).min()>=24
def test_features_use_only_given_history_calendar():
    s=np.load(ART/'splits.npz');h=s['test_history'][:1];c=s['test_calendar'][:1]
    f=tabular(h,c);assert f.shape==(24,12);assert np.allclose(f[:,0],np.log1p(h[0,-24:]))
def test_static_boundary_and_source_export():
    assert client.get('/artifacts/gru.pt').status_code==404
    assert client.get('/api/v1/report').status_code==200
def test_unavailable_model_is_not_ready(monkeypatch):
    import importlib
    module=importlib.import_module('backend.app')
    def unavailable():raise FileNotFoundError('missing model')
    monkeypatch.setattr(module,'state',unavailable)
    r=client.get('/api/v1/health');assert r.status_code==503 and not r.json()['models_loaded']
