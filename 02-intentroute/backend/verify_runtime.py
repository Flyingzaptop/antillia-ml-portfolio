"""Check upgraded inference runtime against cached training embeddings."""
import os
os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import json,time
from pathlib import Path
import numpy as np,torch,joblib
from sentence_transformers import SentenceTransformer
import importlib.metadata as md
torch.set_num_threads(2)
p=Path(__file__).resolve().parents[1]
rows=json.loads((p/'data/splits.json').read_text(encoding='utf-8'))['test']
enc=SentenceTransformer(str(p/'artifacts/encoder'),device='cpu',local_files_only=True)
x=enc.encode([r['text'] for r in rows],normalize_embeddings=True,batch_size=32)
old=np.load(p/'data/test_embeddings.npy')
m=joblib.load(p/'artifacts/embedding_mlp.joblib')
delta=float(np.abs(x-old).max()); same=bool((m.predict(x)==m.predict(old)).all())
report={'runtime':{name:md.version(name) for name in ['torch','transformers','sentence-transformers','scikit-learn','fastapi','starlette']},'n':len(rows),'max_embedding_absolute_difference':delta,'embedding_tolerance':1e-5,'predicted_labels_identical':same,'passed':bool(delta<1e-5 and same)}
(p/'reports/runtime-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2));assert report['passed']
