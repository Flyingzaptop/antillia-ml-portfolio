"""Independent relocation smoke; original venv reuse is never labeled a clean install."""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys,time,zipfile
from pathlib import Path
from datetime import datetime,timezone
from package_portfolio import ROOT,PROJECTS,files_for,verify_recorded_hashes,digest,excluded
FASTAPI_CODE=r"""
import sys,json,os
from pathlib import Path
root=Path.cwd().resolve();sys.path.insert(0,str(root))
from fastapi.testclient import TestClient
if root.name in ['03-terravision','04-machinesentinel']:from app import app
else:from backend.app import app
with TestClient(app) as c:
 health=c.get('/api/v1/health');assert health.status_code==200,health.text
 assert c.get('/').status_code==200
 slug=root.name
 if slug=='03-terravision':
  r=c.post('/api/v1/predict/example/0');assert r.status_code==200,r.text;d=r.json();assert len(d['probabilities'])==10 and d['gradcam'].startswith('data:image/png;base64,');summary={'class':d['class'],'model':d['model']}
 elif slug=='04-machinesentinel':
  sample=c.get('/api/v1/examples').json()[0]['reading'];r=c.post('/api/v1/predict',json=sample);assert r.status_code==200,r.text;d=r.json();summary={'score':d['results'][0]['score'],'model':d['results'][0]['model']}
 elif slug=='01-demandcast':
  r=c.post('/api/v1/predict',json={});assert r.status_code==200,r.text;d=r.json();assert len(d['forecast'])==24;summary={'horizon':24,'model':d['selected_model']}
 elif slug=='05-basketwise':
  r=c.post('/api/v1/predict',json={'items':[],'k':5});assert r.status_code==200,r.text;d=r.json();assert len(d['items'])==5;ids=[v['id'] for v in d['items'][:2]];warm=c.post('/api/v1/predict',json={'items':ids,'k':5});assert warm.status_code==200,warm.text;assert not set(ids)&set(x['id'] for x in warm.json()['items']);summary={'cold_recommendations':5,'warm_recommendations':len(warm.json()['items'])}
 else:
  r=c.post('/api/v1/predict',json={'text':'My card has not arrived yet.' if slug=='02-intentroute' else 'The service was wonderful and I loved it.'});assert r.status_code==200,r.text;summary={'response_keys':list(r.json()),'real_prediction':r.json()}
original=Path(os.environ['PORTFOLIO_ORIGINAL_ROOT']).resolve();allowed_env=Path(os.environ['PORTFOLIO_ALLOWED_ENV']).resolve();bad=[]
for name,module in tuple(sys.modules.items()):
 file=getattr(module,'__file__',None)
 if file:
  p=Path(file).resolve()
  if p.is_relative_to(original) and not p.is_relative_to(root) and not p.is_relative_to(allowed_env):bad.append(str(p))
assert not bad,'Original project source imported: '+str(bad)
print('PORTABLE_RESULT='+json.dumps({'passed':True,'summary':summary,'source_root':str(root),'original_project_source_imports':bad},ensure_ascii=False))
"""
DJANGO_CODE=r"""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));os.environ['DJANGO_SETTINGS_MODULE']='desk.settings'
import django;django.setup()
from django.test import Client
from django.contrib.auth.models import User
from desk.retrieval import retrieve
from desk.models import Document
c=Client(HTTP_HOST='localhost',enforce_csrf_checks=True);s=c.get('/api/v1/session');assert s.status_code==200;s=s.json();creds=json.loads(Path('demo-credentials.json').read_text());user=next(x for x in creds if x['username']=='user');r=c.post('/api/v1/login',data=json.dumps({'username':user['username'],'password':user['password']}),content_type='application/json',HTTP_X_CSRFTOKEN=s['csrf']);assert r.status_code==200,r.content
r=c.get('/api/v1/documents');assert r.status_code==200;assert all(x['access']=='all' for x in r.json());sources=retrieve(User.objects.get(username='user'),'What is the annual learning budget?');assert sources;assert all(x['title'] not in ['Board reserve','Rezerwa zarządu'] for x in sources)
print('PORTABLE_RESULT='+json.dumps({'passed':True,'seed_documents':Document.objects.count(),'visible_documents':len(r.json()),'retrieval_sources':len(sources),'fresh_seed_authentication':True,'llm_generation_tested':False}))
"""
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--projects',nargs='+',choices=PROJECTS,default=PROJECTS);ap.add_argument('--clean-install',action='store_true');ap.add_argument('--from-zips',type=Path);ap.add_argument('--timeout',type=int,default=1200);args=ap.parse_args();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');base=(ROOT/'.runtime/portable-validation'/stamp).resolve();base.mkdir(parents=True,exist_ok=False);reportdir=ROOT/'reports/packaging';reportdir.mkdir(parents=True,exist_ok=True);results=[]
 for slug in args.projects:
  start=time.time();source=ROOT/slug;dest=base/slug;dest.mkdir();result={'project':slug,'snapshot':str(dest),'clean_install':args.clean_install,'environment_note':'Fresh isolated venv installed from pinned requirements' if args.clean_install else 'Original per-project venv reused; validates relocated source/model/data only. NOT clean-install verification.'}
  try:
   if args.from_zips:
    archive=args.from_zips.resolve()/(slug+'.zip')
    with zipfile.ZipFile(archive) as z:
     for info in z.infolist():
      target=(base/info.filename).resolve()
      if not target.is_relative_to(dest) or excluded(target.relative_to(dest)):raise ValueError('Unsafe or excluded archive member')
     z.extractall(base)
    manifest=json.loads((dest/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    for rel,entry in manifest['files'].items():
     candidate=(dest/rel).resolve()
     if not candidate.is_relative_to(dest) or excluded(candidate.relative_to(dest)):raise ValueError('Unsafe manifest member')
     if digest(candidate)!=entry['sha256']:raise ValueError('Extracted package hash mismatch: '+rel)
   else:
    result['source_verification']=verify_recorded_hashes(source)
    for path,rel,external in files_for(source):
     target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
   python=source/'.venv/Scripts/python.exe'
   env=os.environ.copy();env.update({'PORTFOLIO_ORIGINAL_ROOT':str(ROOT),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false','PYTHONUTF8':'1'});env.pop('PYTHONPATH',None)
   if args.clean_install:
    venv=base/(slug+'-clean-env');subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,capture_output=True,text=True,timeout=120);python=venv/'Scripts/python.exe';log=base/(slug+'-install.log')
    with log.open('w',encoding='utf-8') as out:
     requirement_path=dest/('requirements-runtime.txt' if (dest/'requirements-runtime.txt').exists() else ('requirements.lock' if (dest/'requirements.lock').exists() else 'requirements.txt'));requirements=requirement_path.read_text(encoding='utf-8-sig');result['requirements_file']=requirement_path.name
     if 'torch==' in requirements:
      pins=[line.strip().split('+')[0] for line in requirements.splitlines() if line.startswith(('torch==','torchvision=='))];subprocess.run([str(python),'-m','pip','install',*pins,'--index-url','https://download.pytorch.org/whl/cpu'],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=args.timeout)
     subprocess.run([str(python),'-m','pip','install','-r',str(requirement_path)],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=args.timeout)
     subprocess.run([str(python),'-m','pip','check'],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
    result['installation_log']=str(log)
   env['PORTFOLIO_ALLOWED_ENV']=str(python.parent.parent.resolve())
   if slug=='07-ai-desk':
    seed=subprocess.run([str(python),'-I','-c',"import sys,runpy;sys.path.insert(0,'.');runpy.run_path('prepare.py',run_name='__main__')"],cwd=dest,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=args.timeout);(base/(slug+'-seed.log')).write_text(seed.stdout+seed.stderr,encoding='utf-8');seed.check_returncode()
   probe=subprocess.run([str(python),'-I','-c',DJANGO_CODE if slug=='07-ai-desk' else FASTAPI_CODE],cwd=dest,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=args.timeout);(base/(slug+'-smoke.log')).write_text(probe.stdout+probe.stderr,encoding='utf-8');probe.check_returncode();line=next(x for x in probe.stdout.splitlines() if x.startswith('PORTABLE_RESULT='));result.update(json.loads(line.split('=',1)[1]));result['passed']=True
  except Exception as e:result.update({'passed':False,'error':str(e)})
  result['seconds']=round(time.time()-start,2);results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True);(reportdir/('portable-'+stamp+'.json')).write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
 if not all(x['passed'] for x in results):raise SystemExit(1)
if __name__=='__main__':main()
