import os
os.environ['OMP_NUM_THREADS']='2'; os.environ['MKL_NUM_THREADS']='2'; os.environ['TOKENIZERS_PARALLELISM']='false'
from pathlib import Path
import json,time,uuid,logging,csv,io,threading
from contextlib import asynccontextmanager
import numpy as np,joblib,torch
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI,HTTPException,UploadFile,File,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel,Field,field_validator
torch.set_num_threads(2)
P=Path(__file__).resolve().parents[1]; CFG=json.loads((P/'project.json').read_text()); KIND=CFG['kind']
log=logging.getLogger(CFG['title']); logging.basicConfig(level=logging.INFO,format='%(message)s')
state={}; lock=threading.Lock()
@asynccontextmanager
async def lifespan(app):
 state.clear()
 try:
  state['manifest']=json.loads((P/'artifacts/manifest.json').read_text()); state['metrics']=json.loads((P/'reports/metrics.json').read_text(encoding='utf-8'))
  name=state['manifest']['selected_model']; state['classifier']=joblib.load(P/f'artifacts/{name}.joblib')
  if name=='embedding_mlp': state['encoder']=SentenceTransformer(str(P/'artifacts/encoder'),device='cpu',local_files_only=True)
  probe=state['encoder'].encode(['Local readiness probe'],normalize_embeddings=True) if 'encoder' in state else ['Local readiness probe']
  probabilities=state['classifier'].predict_proba(probe)
  if probabilities.shape!=(1,len(state['manifest']['classes'])) or not np.isfinite(probabilities).all(): raise ValueError('Invalid model prediction')
  state['ready']=True
 except Exception as exc: state['ready']=False; log.error(json.dumps({'event':'model_unavailable','type':type(exc).__name__}))
 yield
app=FastAPI(title=CFG['title'],version='1.0.0',lifespan=lifespan)
@app.exception_handler(HTTPException)
async def http_error(request,exc):
 return JSONResponse({'detail':exc.detail,'request_id':getattr(request.state,'request_id',None)},status_code=exc.status_code)
@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
 return JSONResponse({'detail':'Invalid request. Text must contain 3–2000 characters and letters.','request_id':getattr(request.state,'request_id',None)},status_code=422)
@app.middleware('http')
async def audit(request:Request,call_next):
 rid=uuid.uuid4().hex; start=time.perf_counter()
 request.state.request_id=rid
 try: length=int(request.headers.get('content-length','0') or 0)
 except ValueError: return JSONResponse({'detail':'Invalid content length','request_id':rid},status_code=400)
 if length>1_100_000: return JSONResponse({'detail':'Request exceeds 1 MB','request_id':rid},status_code=413)
 response=await call_next(request); response.headers['X-Request-ID']=rid
 response.headers['X-Content-Type-Options']='nosniff'; response.headers['Referrer-Policy']='no-referrer'; response.headers['X-Frame-Options']='DENY'
 response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
 log.info(json.dumps({'request_id':rid,'method':request.method,'path':request.url.path,'status':response.status_code,'ms':round((time.perf_counter()-start)*1000,1)})); return response
class TextInput(BaseModel):
 text:str=Field(min_length=3,max_length=2000)
 @field_validator('text')
 @classmethod
 def meaningful(cls,v):
  if len(v.strip())<3 or not any(c.isalpha() for c in v): raise ValueError('Enter at least three characters including letters')
  return v.strip()
def ready():
 if not state.get('ready'): raise HTTPException(503,'Model unavailable. See local server log and run train.ps1 if artifacts are missing.')
def inference(texts):
 ready(); t=time.perf_counter()
 with lock:
  x=state['encoder'].encode(texts,normalize_embeddings=True,batch_size=32) if 'encoder' in state else texts
  probs=state['classifier'].predict_proba(x)
 result=[]
 for p in probs:
  order=np.argsort(p)[::-1][:3]; result.append({'label':str(state['classifier'].classes_[order[0]]),'confidence':float(p[order[0]]),'uncertain':bool(p[order[0]]<state['manifest']['threshold']),'top':[{'label':str(state['classifier'].classes_[i]),'probability':float(p[i])} for i in order]})
 return {'results':result,'model':state['manifest']['selected_model'],'elapsed_ms':round((time.perf_counter()-t)*1000,2),'threshold':state['manifest']['threshold']}
@app.get('/api/v1/health')
def health(): return JSONResponse({'status':'ready' if state.get('ready') else 'unavailable','project':CFG['title']},status_code=200 if state.get('ready') else 503)
@app.get('/api/v1/meta')
def meta():
 ready(); return {'title':CFG['title'],'kind':KIND,'metrics':state['metrics'],'examples':json.loads((P/'data/polish_control.json').read_text(encoding='utf-8'))[:6]}
@app.post('/api/v1/predict')
def predict(body:TextInput): return inference([body.text])
@app.post('/api/v1/batch')
async def batch(file:UploadFile=File(...)):
 if not file.filename or not file.filename.lower().endswith('.csv'): raise HTTPException(422,'Expected a UTF-8 CSV with text column')
 raw=await file.read(1_000_001)
 if len(raw)>1_000_000: raise HTTPException(413,'CSV limit is 1 MB')
 try:
  reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
  if not reader.fieldnames or 'text' not in reader.fieldnames: raise ValueError()
  rows=[]
  for r in reader:
   if len(rows)>=100: raise HTTPException(422,'Maximum 100 rows per CSV')
   rows.append(TextInput(text=r.get('text') or '').text)
  if not rows: raise ValueError()
 except (UnicodeDecodeError,ValueError,csv.Error): raise HTTPException(422,'Invalid CSV. UTF-8, text column, 1–100 rows, 3–2000 characters per text required.')
 import starlette.concurrency
 result=await starlette.concurrency.run_in_threadpool(inference,rows)
 for row,pred in zip(rows,result['results']): pred['text']=row
 return result
@app.get('/api/v1/report')
def report():
 ready(); return FileResponse(P/'reports/report.html')
@app.get('/api/v1/metrics')
def metrics():
 ready(); return state['metrics']
@app.get('/api/v1/sample.csv')
def sample(): return FileResponse(P/'data/sample.csv',media_type='text/csv',filename='sample.csv')
if (P/'frontend/dist').exists(): app.mount('/',StaticFiles(directory=P/'frontend/dist',html=True),name='frontend')
