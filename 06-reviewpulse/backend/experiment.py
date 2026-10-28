"""Reproducible CPU-only experiments. Frozen transformer; validation selects classifier."""
import os
os.environ['OMP_NUM_THREADS']='2'; os.environ['MKL_NUM_THREADS']='2'; os.environ['TOKENIZERS_PARALLELISM']='false'
from pathlib import Path
import json,csv,sys,time,hashlib,zipfile,urllib.request,platform,importlib.metadata
import numpy as np
import joblib,torch,sklearn
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score,f1_score,average_precision_score,confusion_matrix,classification_report
from sentence_transformers import SentenceTransformer
torch.set_num_threads(2)
P=Path(__file__).resolve().parents[1]; CFG=json.loads((P/'project.json').read_text()); KIND=CFG['kind']; SEED=42
MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
def save(path,obj): path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def fetch(url,path):
 if not path.exists():
  print('Download',url,flush=True); urllib.request.urlretrieve(url,path)
def prepare():
 if (P/'data/splits.json').exists(): return json.loads((P/'data/splits.json').read_text(encoding='utf-8'))
 rows=[]
 if KIND=='intent':
  for part in ['train','test']:
   f=P/f'data/{part}.csv'; fetch(f'https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/{part}.csv',f)
   with f.open(encoding='utf-8') as stream:
    rows.extend(dict(text=r['text'],label=r['category'],domain='banking',official=part) for r in csv.DictReader(stream))
 else:
  f=P/'data/sentiment.zip'; fetch('https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip',f)
  with zipfile.ZipFile(f) as z:
   for name in z.namelist():
    if name.endswith('_labelled.txt') and not name.startswith('__MACOSX'):
     pending=''
     for line in z.read(name).decode('utf-8').splitlines():
      pending+=line+' '
      if '\t' not in pending: continue
      text,label=pending.rsplit('\t',1); rows.append(dict(text=text.strip(),label='positive' if label.strip()=='1' else 'negative',domain=Path(name).stem,official='all')); pending=''
 # Exact normalized duplicates cannot cross partitions, first occurrence retained.
 seen=set(); unique=[]
 for r in rows:
  key=' '.join(r['text'].lower().split())
  if key in seen: continue
  seen.add(key); r['id']=hashlib.sha256(key.encode()).hexdigest(); unique.append(r)
 if KIND=='intent':
  training=[r for r in unique if r['official']=='train']; test=[r for r in unique if r['official']=='test']
 else:
  training,test=train_test_split(unique,test_size=.2,random_state=SEED,stratify=[r['label']+'_'+r['domain'] for r in unique])
 train,val=train_test_split(training,test_size=.2,random_state=SEED,stratify=[r['label'] for r in training])
 splits=dict(train=train,validation=val,test=test); save(P/'data/splits.json',splits); return splits
def encoder():
 local=P/'artifacts/encoder'
 if not (local/'modules.json').exists():
  m=SentenceTransformer(MODEL,device='cpu'); m.save(str(local)); return m
 return SentenceTransformer(str(local),device='cpu',local_files_only=True)
def embeddings(enc,rows,name):
 file=P/f'data/{name}_embeddings.npy'
 if file.exists(): return np.load(file)
 x=enc.encode([r['text'] for r in rows],batch_size=32,show_progress_bar=True,normalize_embeddings=True)
 np.save(file,x); return x
def stats(y,proba,classes):
 pred=np.array(classes)[proba.argmax(axis=1)]
 result={'accuracy':accuracy_score(y,pred),'macro_f1':f1_score(y,pred,average='macro',zero_division=0)}
 if KIND=='intent': result['top3_accuracy']=float(np.mean([v in np.array(classes)[np.argsort(p)[-3:]] for v,p in zip(y,proba)]))
 else: result['pr_auc']=average_precision_score(np.array(y)=='positive',proba[:,list(classes).index('positive')])
 return result
def run(mode):
 start=time.time(); splits=prepare(); enc=encoder()
 X={k:embeddings(enc,v,k) for k,v in splits.items()}; Y={k:np.array([r['label'] for r in v]) for k,v in splits.items()}
 if mode=='train':
  base=make_pipeline(TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=40000,sublinear_tf=True),LogisticRegression(C=4,max_iter=600,random_state=SEED))
  base.fit([r['text'] for r in splits['train']],Y['train']); joblib.dump(base,P/'artifacts/tfidf.joblib')
  candidates=[]
  for alpha in [.001,.01]:
   m=MLPClassifier(hidden_layer_sizes=(192,) if KIND=='intent' else (64,),activation='relu',alpha=alpha,max_iter=160,early_stopping=False,n_iter_no_change=12,random_state=SEED,batch_size=128)
   m.fit(X['train'],Y['train']); candidates.append((f1_score(Y['validation'],m.predict(X['validation']),average='macro'),m,alpha))
  _,m,alpha=max(candidates,key=lambda t:t[0]); joblib.dump(m,P/'artifacts/embedding_mlp.joblib')
  save(P/'artifacts/training.json',dict(seed=SEED,alpha=alpha,epochs=int(m.n_iter_),seconds=time.time()-start,device='cpu',threads=2,python=platform.python_version(),torch=torch.__version__,sklearn=sklearn.__version__,encoder=MODEL,encoder_frozen=True,validation_candidates=[{'alpha':a,'macro_f1':s} for s,_,a in candidates],dependencies={x:importlib.metadata.version(x) for x in ['sentence-transformers','transformers','numpy','scipy']}))
 models={name:joblib.load(P/f'artifacts/{name}.joblib') for name in ['tfidf','embedding_mlp']}
 results={}; probabilities={}
 for name,m in models.items():
  results[name]={}
  for part in ['validation','test']:
   probs=m.predict_proba([r['text'] for r in splits[part]] if name=='tfidf' else X[part]); probabilities[name,part]=probs
   results[name][part]=stats(Y[part],probs,m.classes_)
 selected=max(results,key=lambda n:results[n]['validation']['macro_f1'])
 # Validation-only abstention: lowest threshold reaching 95% selective accuracy,
 # with at least 15% coverage. Otherwise highest selective accuracy at that coverage.
 m=models[selected]; vp=probabilities[selected,'validation']; correct=m.classes_[vp.argmax(1)]==Y['validation']
 candidates=[]
 for t in np.arange(.5,.96,.025):
  accepted=vp.max(1)>=t
  if accepted.mean()>=.15: candidates.append((float(t),float(correct[accepted].mean()),float(accepted.mean())))
 good=[c for c in candidates if c[1]>=.95]
 threshold=min(good,key=lambda c:c[0])[0] if good else max(candidates,key=lambda c:(c[1],c[2]))[0]
 curated=json.loads((P/'data/polish_control.json').read_text(encoding='utf-8'))
 polx=enc.encode([r['text'] for r in curated],normalize_embeddings=True); polish={}
 for name,m in models.items(): polish[name]=stats([r['label'] for r in curated],m.predict_proba([r['text'] for r in curated] if name=='tfidf' else polx),m.classes_)
 examples=[]; m=models[selected]; pred=m.classes_[probabilities[selected,'test'].argmax(1)]
 for row,p in zip(splits['test'],pred):
  if row['label']!=p: examples.append(dict(text=row['text'],actual=row['label'],predicted=p))
 report=dict(project=CFG['title'],selected_model=selected,threshold=float(threshold),split_counts={k:len(v) for k,v in splits.items()},models=results,polish_control={'n':len(curated),'description':'Author-written small diagnostic only; not an independent Polish benchmark. Not used for selection.','models':polish},classes=list(m.classes_),confusion_matrix=confusion_matrix(Y['test'],pred,labels=m.classes_).tolist(),classification_report=classification_report(Y['test'],pred,output_dict=True,zero_division=0),errors=examples[:25],training=json.loads((P/'artifacts/training.json').read_text()))
 if KIND=='sentiment':
  report['domain_transfer']={}
  for domain in sorted({r['domain'] for r in splits['train']}):
   # Independent diagnostic: fit only other-domain training rows, evaluate target-domain test rows.
   a=np.array([r['domain']!=domain for r in splits['train']]); b=np.array([r['domain']==domain for r in splits['test']])
   transfer=LogisticRegression(C=1,max_iter=400).fit(X['train'][a],Y['train'][a]); report['domain_transfer'][domain]=stats(Y['test'][b],transfer.predict_proba(X['test'][b]),transfer.classes_)
 t=time.perf_counter(); e=enc.encode([splits['test'][0]['text']],normalize_embeddings=True); models['embedding_mlp'].predict_proba(e); report['single_embedding_inference_ms']=(time.perf_counter()-t)*1000
 save(P/'reports/metrics.json',report); save(P/'artifacts/manifest.json',{'selected_model':selected,'threshold':float(threshold),'classes':list(m.classes_)})
 with (P/'reports/metrics.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f); w.writerow(['model','split','metric','value'])
  for name,parts in results.items():
   for part,metrics in parts.items():
    for k,v in metrics.items(): w.writerow([name,part,k,v])
 hashes={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for d in ['artifacts','data'] for f in (P/d).rglob('*') if f.is_file()}
 save(P/'reports/checksums.json',hashes)
 import html
 (P/'reports/report.html').write_text('<!doctype html><meta charset="utf-8"><title>'+CFG['title']+' experiment</title><style>body{font:16px system-ui;max-width:1100px;margin:60px auto;padding:20px;color:#243536}pre{white-space:pre-wrap;background:#eef3f0;padding:24px}h1{font-size:48px}</style><h1>'+CFG['title']+'</h1><p>Reproducible experiment · seed 42 · validation-only model selection</p><p>EN: Benchmark evaluation. Small authored Polish control is not an independent benchmark.<br>PL: Wyniki eksperymentu. Autorski zestaw polski nie jest niezależnym benchmarkiem.</p><pre>'+html.escape(json.dumps(report,ensure_ascii=False,indent=2))+'</pre>',encoding='utf-8')
 from reporting import render
 render(P)
 print(json.dumps({'selected':selected,'models':results,'polish':polish},indent=2),flush=True)
if __name__=='__main__': run(sys.argv[1] if len(sys.argv)>1 else 'train')

