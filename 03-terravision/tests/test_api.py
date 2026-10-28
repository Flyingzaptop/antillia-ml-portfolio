import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import app
client=TestClient(app)
def test_example_prediction():
 a=client.post('/api/v1/predict/example/0');assert a.status_code==200;r=a.json();assert len(r['probabilities'])==10;assert abs(sum(p['probability'] for p in r['probabilities'])-1)<1e-5;assert r['gradcam'].startswith('data:image/png;base64,');assert client.post('/api/v1/predict/example/0').json()==r
 assert client.post('/api/v1/predict/example/100').status_code==404
def test_invalid_images_and_size():
 for content in [b'',b'<script>alert(1)</script>',b'not an image']:
  assert client.post('/api/v1/predict',files={'file':('../../outside.jpg',content,'image/jpeg')}).status_code==422
 assert client.post('/api/v1/predict',files={'file':('big.png',b'x'*(5*1024*1024+1))}).status_code==413
def test_upload_and_no_path_write():
 raw=client.get('/api/v1/examples/0/image').content;r=client.post('/api/v1/predict',files={'file':('../../outside.jpg',raw,'image/jpeg')});assert r.status_code==200;assert not Path('../outside.jpg').exists()
def test_hash_splits():
 s=json.loads((Path(__file__).resolve().parents[1]/'artifacts/splits.json').read_text());sets=[set(r['sha256'] for r in v) for v in s.values()];assert not sets[0]&sets[1];assert not sets[0]&sets[2];assert not sets[1]&sets[2]
