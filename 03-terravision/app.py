import io,base64,pickle,threading
import numpy as np,torch
from PIL import Image,UnidentifiedImageError
from core import *
TITLE='TerraVision'
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

torch.set_num_threads(2)
model=network();model.load_state_dict(torch.load(ROOT/'artifacts/resnet18.pt',weights_only=True,map_location='cpu'));model.eval();baseline=pickle.load(open(ROOT/'artifacts/baseline.pkl','rb'));config=json.loads((ROOT/'artifacts/config.json').read_text());lock=threading.Lock()
rows=json.loads((ROOT/'artifacts/splits.json').read_text())['test'];examples=[next(r for r in rows if r['label']==i) for i in range(10)]
@app.get('/api/v1/examples')
def get_examples():return [{'id':i,'label':CLASSES[r['label']],'url':f'/api/v1/examples/{i}/image'} for i,r in enumerate(examples)]
@app.get('/api/v1/examples/{idx}/image')
def example_image(idx:int):
 if not 0<=idx<len(examples):raise HTTPException(404,'Unknown example')
 return FileResponse(ROOT/examples[idx]['path'],media_type='image/jpeg')
def predict_image(im):
 with lock:
  acts=[]
  def hook(module,inputs,out):acts.append(out);out.retain_grad()
  handle=model.layer4.register_forward_hook(hook)
  try:
   x=transform(im).unsqueeze(0);model.zero_grad();logits=model(x);neural=torch.softmax(logits,1).detach().numpy()[0];p=neural if config['selected']=='resnet18' else baseline.predict_proba(features(im)[None])[0];idx=int(np.argmax(p));logits[0,idx].backward();a=acts[0];cam=torch.relu((a.grad.mean((2,3),keepdim=True)*a).sum(1))[0].detach().numpy();cam/=max(float(cam.max()),1e-8)
  finally:handle.remove()
  heat=np.asarray(Image.fromarray((cam*255).astype('uint8')).resize((256,256)),dtype=float)/255;rgb=np.asarray(im.resize((256,256)),dtype=float);overlay=rgb*.6+np.stack([heat*255,(1-heat)*70,np.zeros_like(heat)],axis=-1)*.4;buf=io.BytesIO();Image.fromarray(overlay.astype('uint8')).save(buf,format='PNG')
 return {'class':CLASSES[idx],'model':config['selected'],'probabilities':[{'class':c,'probability':float(v)} for c,v in zip(CLASSES,p)],'gradcam':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),'gradcam_model':'resnet18','note':'Grad-CAM describes neural model activation, not causal evidence.'}
@app.post('/api/v1/predict/example/{idx}')
def predict_example(idx:int):
 if not 0<=idx<len(examples):raise HTTPException(404,'Unknown example')
 return predict_image(Image.open(ROOT/examples[idx]['path']).convert('RGB'))
@app.post('/api/v1/predict')
async def predict(file:UploadFile=File(...)):
 raw=await file.read(5*1024*1024+1)
 if len(raw)>5*1024*1024:raise HTTPException(413,'Maximum image size: 5 MB')
 try:
  im=Image.open(io.BytesIO(raw))
  if im.width*im.height>16000000 or min(im.size)<16:raise ValueError('Dimensions outside range')
  if im.format not in ['JPEG','PNG','WEBP']:raise ValueError('Use JPEG, PNG or WEBP')
  im.load();im=im.convert('RGB')
 except Exception:raise HTTPException(422,'Invalid image. Use JPEG, PNG or WEBP, at least 16 px, at most 16 megapixels.')
 return predict_image(im)

@app.get('/reports/{name}')
def report_file(name:str):
 if name not in {'report.html','report.pdf','metrics.json','metrics.csv','metrics.png','confusion.png'} or not (ROOT/'reports'/name).is_file():raise HTTPException(404,'Report not found')
 return FileResponse(ROOT/'reports'/name)

@app.get('/docs',response_class=HTMLResponse)
def offline_docs():
 return '<!doctype html><html lang="en"><meta charset="utf-8"><title>'+TITLE+' API</title><style>body{max-width:900px;margin:50px auto;font:16px Arial;line-height:1.8}code{background:#eee;padding:5px}</style><h1>'+TITLE+' API v1</h1><p>Local, same-origin API. <a href="/openapi.json">Complete OpenAPI schema</a></p>'+''.join('<p><code>'+','.join(sorted(getattr(r,'methods',[]) or []))+' '+r.path+'</code></p>' for r in app.routes if r.path.startswith('/api/'))+'<p>POST JSON predictions: application/json. File predictions: multipart/form-data, field name file. Errors use HTTP 4xx and detail; X-Request-ID identifies requests.</p></html>'

if (ROOT/'frontend/dist').exists():app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
