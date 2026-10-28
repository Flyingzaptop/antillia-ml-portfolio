from __future__ import annotations
import json, logging, time, uuid
from functools import lru_cache
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from .pipeline import ART, ROOT, all_predict, load_models
app=FastAPI(title='DemandCast',version='1.0.0',openapi_url='/api/v1/openapi.json',docs_url=None)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s');log=logging.getLogger('demandcast')
@app.middleware('http')
async def trace(request:Request,call_next):
    rid=uuid.uuid4().hex;started=time.perf_counter()
    try:response=await call_next(request)
    except Exception:
        log.exception('request_id=%s unhandled_error',rid);response=JSONResponse({'detail':'Internal error','request_id':rid},status_code=500)
    response.headers['X-Request-ID']=rid;response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    log.info('request_id=%s method=%s path=%s status=%s duration_ms=%.1f',rid,request.method,request.url.path,response.status_code,(time.perf_counter()-started)*1000);return response
@lru_cache
def state():return np.load(ART/'splits.npz'),load_models(),json.loads((ART/'metrics.json').read_text())
@app.get('/api/v1/health')
def health():
    try:
        state()
        return {'status':'ok','project':'demandcast','models_loaded':True}
    except Exception as exc:
        log.error('readiness_failed type=%s',type(exc).__name__)
        return JSONResponse({'status':'unavailable','project':'demandcast','models_loaded':False},status_code=503)
@app.get('/api/v1/meta')
def meta():
    s,_,m=state()
    return {'metrics':m,'origins':[{'id':i,'date':str(s['dates'][o])} for i,o in enumerate(s['test_origins'])],'config':json.loads((ART/'config.json').read_text()),'split':json.loads((ART/'split_manifest.json').read_text()),'source':'UCI Bike Sharing, 2011–2012; CC BY 4.0'}
class ForecastRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    origin_index:int=Field(default=0,ge=0)
    history_scale:float=Field(default=1,ge=.5,le=1.5)
@app.post('/api/v1/predict')
def predict(q:ForecastRequest):
    s,models,m=state()
    if q.origin_index>=len(s['test_origins']):raise HTTPException(422,'Unknown origin')
    i=q.origin_index;o=int(s['test_origins'][i]);h=s['test_history'][i:i+1]*q.history_scale;start=time.perf_counter();p=all_predict(h,s['test_calendar'][i:i+1],models)
    return {'origin':str(s['dates'][o]),'selected_model':m['selected_model'],'scenario':q.history_scale!=1,'history':[{'date':str(s['dates'][o-168+j]),'value':float(v)} for j,v in enumerate(h[0])],'forecast':[{'date':str(s['dates'][o+j]),'actual':float(s['test_target'][i,j]),**{name:round(float(v[0,j]),2) for name,v in p.items()}} for j in range(24)],'latency_ms':round((time.perf_counter()-start)*1000,2)}
@app.get('/api/v1/report')
def report():return FileResponse(ROOT/'reports/metrics.csv',media_type='text/csv',filename='demandcast-metrics.csv')
if (ROOT/'frontend/dist/assets').exists():app.mount('/assets',StaticFiles(directory=ROOT/'frontend/dist/assets'),name='assets')
@app.get('/')
def index():return FileResponse(ROOT/'frontend/dist/index.html')

@app.get('/api/v1/docs',response_class=HTMLResponse)
def offline_docs():
    import html
    schema=app.openapi()
    rows=''.join('<li><b>'+html.escape(method.upper())+'</b> '+html.escape(path)+'</li>' for path,methods in schema['paths'].items() for method in methods if method in ['get','post'])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Local API documentation</title><style>body{font:16px/1.7 system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4ef;padding:20px}</style><h1>'+html.escape(schema['info']['title'])+' API</h1><p>Offline documentation. <a href="/api/v1/openapi.json">OpenAPI JSON</a></p><ul>'+rows+'</ul><h2>Request and response schemas</h2><pre>'+html.escape(json.dumps(schema.get('components',{}),indent=2))+'</pre></html>'
