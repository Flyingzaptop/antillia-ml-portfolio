import io,pickle
import pandas as pd,numpy as np,torch
from pydantic import BaseModel,Field,ConfigDict
from core import *
TITLE='MachineSentinel'
import uuid,logging,time,json
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,JSONResponse,HTMLResponse
app=FastAPI(title=TITLE,version='1.0.0',docs_url=None,redoc_url=None)
(ROOT/'logs').mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO,format='%(message)s',handlers=[logging.StreamHandler(),RotatingFileHandler(ROOT/'logs/api.log',maxBytes=2_000_000,backupCount=3,encoding='utf-8')])
@app.middleware('http')
async def log_requests(request,call_next):
 rid=uuid.uuid4().hex;start=time.time()
 try:response=await call_next(request)
 except Exception:
  logging.error(json.dumps({'request_id':rid,'event':'internal_error'}));response=JSONResponse({'detail':'Internal service error','request_id':rid},status_code=500)
 response.headers['X-Request-ID']=rid;response.headers['X-Content-Type-Options']='nosniff';response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'";logging.info(json.dumps({'request_id':rid,'method':request.method,'status':response.status_code,'duration_ms':round((time.time()-start)*1000,2)}));return response
@app.get('/api/v1/health')
def health():return {'status':'ok','project':TITLE,'model_loaded':True}
@app.get('/api/v1/metrics')
def metrics():return json.loads((ROOT/'reports/metrics.json').read_text())

torch.set_num_threads(2);ae=network();ae.load_state_dict(torch.load(ROOT/'artifacts/autoencoder.pt',weights_only=True,map_location='cpu'));ae.eval();iso=pickle.load(open(ROOT/'artifacts/isolationforest.pkl','rb'));scaler=pickle.load(open(ROOT/'artifacts/scaler.pkl','rb'));config=json.loads((ROOT/'artifacts/config.json').read_text())
class Reading(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 air_temperature:float=Field(ge=250,le=400)
 process_temperature:float=Field(ge=250,le=500)
 rotational_speed:float=Field(gt=0,le=10000)
 torque:float=Field(ge=0,le=300)
 tool_wear:float=Field(ge=0,le=1000)
def infer(readings):
 df=pd.DataFrame([[getattr(r,k) for k in KEYS] for r in readings],columns=COLS);x=scaler.transform(df);ss={'autoencoder':scores(ae,x),'isolationforest':-iso.score_samples(x)};name=config['selected'];out=[]
 for i,r in enumerate(readings):
  departures=[{'feature':k,'value':getattr(r,k),'range':v,'outside':not v[0]<=getattr(r,k)<=v[1]} for k,v in config['normal_ranges'].items()];out.append({'anomaly':bool(ss[name][i]>=config['thresholds'][name]),'score':float(ss[name][i]),'threshold':config['thresholds'][name],'model':name,'models':{n:float(s[i]) for n,s in ss.items()},'departures':departures})
 return {'results':out,'synthetic_dataset':True}
@app.post('/api/v1/predict')
def predict(reading:Reading):return infer([reading])
@app.post('/api/v1/predict/csv')
async def predict_csv(file:UploadFile=File(...)):
 raw=await file.read(1024*1024+1)
 if len(raw)>1024*1024:raise HTTPException(413,'CSV limit: 1 MB')
 try:
  df=pd.read_csv(io.BytesIO(raw))
  if set(df.columns)!=set(KEYS) or not 1<=len(df)<=1000:raise ValueError('Invalid columns or row count')
  readings=[Reading(**r) for r in df.to_dict('records')]
 except Exception:raise HTTPException(422,{'message':'Invalid CSV. UTF-8, 1-1000 rows, finite numeric values.','columns':KEYS})
 return infer(readings)
@app.get('/api/v1/examples')
def examples():
 df=pd.read_csv(ROOT/'data/ai4i2020.csv');indices=json.loads((ROOT/'artifacts/splits.json').read_text())['test'];part=df.iloc[indices];return [{'name':name,'reading':dict(zip(KEYS,[float(r[c]) for c in COLS]))} for name,r in [('normal',part[part['Machine failure']==0].iloc[0]),('failure',part[part['Machine failure']==1].iloc[0])]]
@app.get('/api/v1/ranges')
def ranges():return config['normal_ranges']

@app.get('/reports/{name}')
def report_file(name:str):
 if name not in {'report.html','report.pdf','metrics.json','metrics.csv','metrics.png','confusion.png'} or not (ROOT/'reports'/name).is_file():raise HTTPException(404,'Report not found')
 return FileResponse(ROOT/'reports'/name)

@app.get('/docs',response_class=HTMLResponse)
def offline_docs():
 return '<!doctype html><html lang="en"><meta charset="utf-8"><title>'+TITLE+' API</title><style>body{max-width:900px;margin:50px auto;font:16px Arial;line-height:1.8}code{background:#eee;padding:5px}</style><h1>'+TITLE+' API v1</h1><p>Local, same-origin API. <a href="/openapi.json">Complete OpenAPI schema</a></p>'+''.join('<p><code>'+','.join(sorted(getattr(r,'methods',[]) or []))+' '+r.path+'</code></p>' for r in app.routes if r.path.startswith('/api/'))+'<p>POST JSON predictions: application/json. File predictions: multipart/form-data, field name file. Errors use HTTP 4xx and detail; X-Request-ID identifies requests.</p></html>'

if (ROOT/'frontend/dist').exists():app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
