import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import app
client=TestClient(app)
def test_predict_and_determinism():
 sample=client.get('/api/v1/examples').json()[0]['reading'];a=client.post('/api/v1/predict',json=sample);b=client.post('/api/v1/predict',json=sample);assert a.status_code==200;assert a.json()==b.json();assert len(a.json()['results'][0]['departures'])==5
def test_invalid_and_unknown_fields():
 assert client.post('/api/v1/predict',json={}).status_code==422
 sample=client.get('/api/v1/examples').json()[0]['reading'];sample['torque']=-1;assert client.post('/api/v1/predict',json=sample).status_code==422
 sample['torque']=40;sample['Machine failure']=1;assert client.post('/api/v1/predict',json=sample).status_code==422
def test_csv_validation():
 for content in [b'',b'a,b\n1,2',b'air_temperature,process_temperature,rotational_speed,torque,tool_wear\nNaN,310,1500,40,10']:
  assert client.post('/api/v1/predict/csv',files={'file':('../../outside.csv',content,'text/csv')}).status_code==422
 good=b'air_temperature,process_temperature,rotational_speed,torque,tool_wear\n298,310,1500,40,10';assert client.post('/api/v1/predict/csv',files={'file':('../../outside.csv',good,'text/csv')}).status_code==200
 assert client.post('/api/v1/predict/csv',files={'file':('big.csv',b'x'*1048577)}).status_code==413
def test_split_integrity():
 root=Path(__file__).resolve().parents[1];s=json.loads((root/'artifacts/splits.json').read_text());assert not(set(s['train'])&set(s['test']));assert not(set(s['validation'])&set(s['test']));assert len(set(sum(s.values(),[])))==10000

def test_training_scaler_normal_only():
 import pickle,numpy as np,pandas as pd
 root=Path(__file__).resolve().parents[1];df=pd.read_csv(root/'data/ai4i2020.csv');s=json.loads((root/'artifacts/splits.json').read_text());tr=df.iloc[s['train']];normal=tr[tr['Machine failure']==0]
 from core import COLS
 scaler=pickle.load(open(root/'artifacts/scaler.pkl','rb'));assert np.allclose(scaler.mean_,normal[COLS].mean().to_numpy());assert len(scaler.mean_)==5
