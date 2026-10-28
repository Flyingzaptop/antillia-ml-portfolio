"""Causal rolling-origin 24-hour demand forecasting; no future weather."""
from __future__ import annotations
import os
os.environ.setdefault('OMP_NUM_THREADS','2'); os.environ.setdefault('MKL_NUM_THREADS','2')
import copy, hashlib, json, platform, sys, time, zipfile
from pathlib import Path
import joblib, numpy as np, pandas as pd, requests, torch
from torch import nn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; DATA=ROOT/'data'
SEED=42; LOOKBACK=168; HORIZON=24
torch.set_num_threads(2)
def write_json(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def download():
    DATA.mkdir(exist_ok=True); dest=DATA/'bike-sharing.zip'
    if not dest.exists():
        r=requests.get('https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip',timeout=120); r.raise_for_status(); dest.write_bytes(r.content)
    with zipfile.ZipFile(dest) as z:
        frame=pd.read_csv(z.open(next(x for x in z.namelist() if x.endswith('hour.csv'))))
    dates=pd.to_datetime(frame.dteday)+pd.to_timedelta(frame.hr,unit='h')
    s=pd.Series(frame.cnt.to_numpy(dtype=float),index=dates).sort_index()
    return s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='h'))
def calendar(dates):
    return np.stack([np.sin(2*np.pi*dates.hour/24),np.cos(2*np.pi*dates.hour/24),np.sin(2*np.pi*dates.dayofweek/7),np.cos(2*np.pi*dates.dayofweek/7),np.sin(2*np.pi*dates.dayofyear/366),np.cos(2*np.pi*dates.dayofyear/366)],axis=-1).astype('float32')
def prepare():
    s=download(); n=len(s); a=int(n*.70); b=int(n*.85);raw=s.to_numpy();filled=s.ffill().to_numpy();groups={}
    for name,start,end,stride in [('train',LOOKBACK,a,6),('validation',a,b,24),('test',b,n,24)]:
        origins=[i for i in range(start,end-HORIZON+1,stride) if np.isfinite(raw[i:i+HORIZON]).all()]
        groups[name]={'history':np.stack([filled[i-LOOKBACK:i] for i in origins]).astype('float32'),'target':np.stack([raw[i:i+HORIZON] for i in origins]).astype('float32'),'calendar':np.stack([calendar(s.index[i:i+HORIZON]) for i in origins]),'origins':np.asarray(origins,dtype='int64')}
    ART.mkdir(exist_ok=True)
    np.savez_compressed(ART/'splits.npz',**{f'{part}_{key}':val for part,g in groups.items() for key,val in g.items()},dates=s.index.astype(str).to_numpy(dtype='U19'),counts=filled.astype('float32'))
    write_json(ART/'split_manifest.json',{'seed':SEED,'train_end_exclusive':str(s.index[a]),'validation_end_exclusive':str(s.index[b]),'source_sha256':sha(DATA/'bike-sharing.zip'),'lookback':LOOKBACK,'horizon':HORIZON,'train_stride':6,'evaluation_stride':24,'missing_target_windows':'excluded','missing_history':'causal forward fill','origins':{k:[str(s.index[i]) for i in v['origins']] for k,v in groups.items()}})
    return groups
def tabular(h,c):
    n=len(h);repeat=lambda v:np.repeat(v[:,None],HORIZON,axis=1)
    f=np.stack([np.log1p(h[:,-24:]),np.log1p(h[:,:24]),repeat(np.log1p(h[:,-1])),repeat(np.log1p(h[:,-24:].mean(axis=1))),repeat(np.log1p(h.mean(axis=1))),repeat(np.log1p(h[:,-24:].std(axis=1)))],axis=-1)
    return np.concatenate([f,c],axis=-1).reshape(n*HORIZON,-1)
class GRUForecast(nn.Module):
    def __init__(self):
        super().__init__();self.gru=nn.GRU(1,32,batch_first=True);self.head=nn.Sequential(nn.Linear(32+24*6,64),nn.ReLU(),nn.Linear(64,24))
    def forward(self,x,c):
        _,state=self.gru(x);return self.head(torch.cat([state[-1],c.flatten(1)],dim=1))
def score(y,p):
    return {'MAE':float(mean_absolute_error(y.ravel(),p.ravel())),'RMSE':float(np.sqrt(mean_squared_error(y.ravel(),p.ravel()))),'WAPE':float(np.abs(y-p).sum()/max(y.sum(),1))}
def tensors(group,mean,std):
    return torch.tensor(((np.log1p(group['history'])-mean)/std)[...,None],dtype=torch.float32),torch.tensor(group['calendar']),torch.tensor((np.log1p(group['target'])-mean)/std)
def train():
    started=time.perf_counter();np.random.seed(SEED);torch.manual_seed(SEED);g=prepare()
    print('Prepared',{k:len(v['history']) for k,v in g.items()},flush=True)
    mean=float(np.log1p(g['train']['history']).mean());std=float(np.log1p(g['train']['history']).std());write_json(ART/'scaler.json',{'mean':mean,'std':std})
    print('Fitting gradient boosting',flush=True)
    boost=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=23,l2_regularization=2,learning_rate=.07,random_state=SEED,early_stopping=False)
    with threadpool_limits(limits=2):boost.fit(tabular(g['train']['history'],g['train']['calendar']),np.log1p(g['train']['target']).ravel())
    joblib.dump(boost,ART/'boosting.joblib');net=GRUForecast();opt=torch.optim.Adam(net.parameters(),lr=.003)
    x,c,y=tensors(g['train'],mean,std);vx,vc,vy=tensors(g['validation'],mean,std)
    best=float('inf');best_state=None;history=[];patience=0
    for epoch in range(1,31):
        net.train();losses=[]
        for idx in torch.randperm(len(x)).split(64):
            opt.zero_grad();loss=nn.functional.mse_loss(net(x[idx],c[idx]),y[idx]);loss.backward();nn.utils.clip_grad_norm_(net.parameters(),1);opt.step();losses.append(loss.item())
        net.eval()
        with torch.no_grad():p=np.maximum(np.expm1(net(vx,vc).numpy()*std+mean),0)
        val=score(g['validation']['target'],p)['MAE'];history.append({'epoch':epoch,'loss':float(np.mean(losses)),'validation_MAE':val});print(f'GRU epoch {epoch}: validation MAE={val:.3f}',flush=True)
        if val<best:best=val;best_state=copy.deepcopy(net.state_dict());patience=0
        else:patience+=1
        if patience>=6:break
    torch.save(best_state,ART/'gru.pt');write_json(ART/'training_history.json',history)
    write_json(ART/'config.json',{'seed':SEED,'lookback':LOOKBACK,'horizon':HORIZON,'epochs_run':len(history),'selection':'minimum validation MAE','training_seconds':round(time.perf_counter()-started,2),'hardware':platform.processor() or platform.machine(),'torch':torch.__version__,'future_weather':False})
    evaluate(initial=True)
def load_models():
    net=GRUForecast();net.load_state_dict(torch.load(ART/'gru.pt',map_location='cpu',weights_only=True));net.eval()
    return joblib.load(ART/'boosting.joblib'),net,json.loads((ART/'scaler.json').read_text())
def all_predict(h,c,models):
    boost,net,s=models
    with threadpool_limits(limits=2):b=np.maximum(np.expm1(boost.predict(tabular(h,c))).reshape(-1,HORIZON),0)
    with torch.no_grad():
        x=torch.tensor(((np.log1p(h)-s['mean'])/s['std'])[...,None],dtype=torch.float32);p=net(x,torch.tensor(c,dtype=torch.float32)).numpy()
    return {'seasonal':h[:,:24].copy(),'boosting':b,'gru':np.maximum(np.expm1(p*s['std']+s['mean']),0)}
def evaluate(initial=False):
    split=np.load(ART/'splits.npz');models=load_models();metrics={};predictions={}
    for part in ['validation','test']:
        p=all_predict(split[f'{part}_history'],split[f'{part}_calendar'],models);metrics[part]={name:score(split[f'{part}_target'],v) for name,v in p.items()};predictions[part]=p
    selected=min(metrics['validation'],key=lambda m:metrics['validation'][m]['MAE']);t=time.perf_counter()
    for _ in range(10):all_predict(split['test_history'][:1],split['test_calendar'][:1],models)
    metrics.update({'selected_model':selected,'latency_ms_all_models':(time.perf_counter()-t)*100,'n_test_origins':len(split['test_history']),'horizon_hours':24})
    if initial:write_json(ART/'metrics.json',metrics)
    else:
        previous=json.loads((ART/'metrics.json').read_text());delta=max(abs(previous[p][m][k]-metrics[p][m][k]) for p in ['validation','test'] for m in ['seasonal','boosting','gru'] for k in ['MAE','RMSE','WAPE'])
        write_json(ROOT/'reports/reproduction.json',{'max_absolute_difference':delta,'tolerance':1e-4,'passed':delta<1e-4})
        if delta>=1e-4:raise RuntimeError('Metrics failed reproduction tolerance')
    pd.DataFrame([{'split':p,'model':m,**v} for p in ['validation','test'] for m,v in metrics[p].items()]).to_csv(ROOT/'reports/metrics.csv',index=False)
    rows=[]
    for i,origin in enumerate(split['test_origins']):
        for h in range(HORIZON):rows.append({'origin':str(split['dates'][origin]),'horizon':h+1,'actual':float(split['test_target'][i,h]),**{m:float(v[i,h]) for m,v in predictions['test'].items()}})
    pd.DataFrame(rows).to_csv(ROOT/'reports/predictions.csv',index=False);write_json(ROOT/'reports/artifact_hashes.json',{p.name:sha(p) for p in ART.iterdir() if p.is_file()});print(json.dumps(metrics,indent=2),flush=True);return metrics
if __name__=='__main__':(train if len(sys.argv)<2 or sys.argv[1]=='train' else evaluate)()
