import json,logging,time,uuid
from functools import lru_cache
from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.responses import FileResponse,JSONResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from .pipeline import ART,ROOT,load_weights,ranking
app=FastAPI(title='BasketWise',version='1.0.0',openapi_url='/api/v1/openapi.json',docs_url=None)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s');log=logging.getLogger('basketwise')
@app.middleware('http')
async def trace(request:Request,call_next):
    rid=uuid.uuid4().hex;start=time.perf_counter()
    try:response=await call_next(request)
    except Exception:
        log.exception('request_id=%s unhandled_error',rid);response=JSONResponse({'detail':'Internal error','request_id':rid},status_code=500)
    response.headers['X-Request-ID']=rid;response.headers['X-Content-Type-Options']='nosniff';response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    log.info('request_id=%s method=%s path=%s status=%s duration_ms=%.1f',rid,request.method,request.url.path,response.status_code,(time.perf_counter()-start)*1000);return response
@lru_cache
def state():
    return json.loads((ART/'catalog.json').read_text()),load_weights(),json.loads((ART/'metrics.json').read_text()),json.loads((ART/'evaluation_cases.json').read_text())
@app.get('/api/v1/health')
def health():
    try:
        cat,weights,_,_=state()
        if len(weights[0])!=len(cat):raise ValueError('Artifact shape mismatch')
        return {'status':'ok','project':'basketwise','models_loaded':True}
    except Exception as exc:
        log.error('readiness_failed type=%s',type(exc).__name__)
        return JSONResponse({'status':'unavailable','project':'basketwise','models_loaded':False},status_code=503)
@app.get('/api/v1/meta')
def meta():
    cat,w,m,g=state();examples=[{'id':i,'items':[cat[j]['id'] for j in c['history'][:6]],'label':f'Profile {i+1:02d}'} for i,c in enumerate(g['test']['warm'][:12])]
    return {'metrics':m,'examples':examples,'catalog_size':len(cat),'split':json.loads((ART/'split_manifest.json').read_text()),'config':json.loads((ART/'config.json').read_text()),'unknown_catalog_rates':{p:g[p]['unknown_catalog_rate'] for p in ['validation','test']}}
@app.get('/api/v1/catalog')
def catalog(q:str=Query(default='',max_length=100),limit:int=Query(default=24,ge=1,le=100),offset:int=Query(default=0,ge=0)):
    cat,*_=state();matches=[x for x in cat if q.lower() in x['name'].lower() or q.lower() in x['id'].lower()]
    return {'items':matches[offset:offset+limit],'total':len(matches)}
class RecommendationRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    items:list[str]=Field(default_factory=list,max_length=100)
    k:int=Field(default=8,ge=1,le=20)
@app.post('/api/v1/predict')
def predict(q:RecommendationRequest):
    cat,weights,m,_=state();index={v['id']:i for i,v in enumerate(cat)}
    if any(v not in index for v in q.items):raise HTTPException(422,'Unknown product ID')
    history=sorted({index[x] for x in q.items});model=m['selected_model'];start=time.perf_counter();rec=ranking(history,model,weights,q.k);items=[]
    for i in rec:
        linked=max(history,key=lambda j:float(weights[2][i]@weights[2][j]) if model=='factorization' else float(weights[1][i,j])) if history else None
        items.append({**cat[i],'because':cat[linked]['name'] if linked is not None else None,'reason':'similar_history' if history and model!='popularity' else 'popular','illustration':i%6})
    return {'items':items,'model':model if history else 'popularity','cold_start':not history,'latency_ms':round((time.perf_counter()-start)*1000,2)}
@app.get('/api/v1/report')
def report():return FileResponse(ROOT/'reports/metrics.csv',media_type='text/csv',filename='basketwise-metrics.csv')
if (ROOT/'frontend/dist/assets').exists():app.mount('/assets',StaticFiles(directory=ROOT/'frontend/dist/assets'),name='assets')
@app.get('/')
def index():return FileResponse(ROOT/'frontend/dist/index.html')

@app.get('/api/v1/docs',response_class=HTMLResponse)
def offline_docs():
    import html
    schema=app.openapi()
    rows=''.join('<li><b>'+html.escape(method.upper())+'</b> '+html.escape(path)+'</li>' for path,methods in schema['paths'].items() for method in methods if method in ['get','post'])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Local API documentation</title><style>body{font:16px/1.7 system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4ef;padding:20px}</style><h1>'+html.escape(schema['info']['title'])+' API</h1><p>Offline documentation. <a href="/api/v1/openapi.json">OpenAPI JSON</a></p><ul>'+rows+'</ul><h2>Request and response schemas</h2><pre>'+html.escape(json.dumps(schema.get('components',{}),indent=2))+'</pre></html>'
