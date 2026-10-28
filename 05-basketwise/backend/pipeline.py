"""Temporal, full-catalog implicit recommendations; no sampled-negative metric inflation."""
from __future__ import annotations
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import hashlib,json,platform,sys,time,zipfile
from pathlib import Path
import numpy as np,pandas as pd,requests
from scipy.sparse import csr_matrix,save_npz,load_npz
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts';DATA=ROOT/'data';SEED=42
def write_json(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def download():
    DATA.mkdir(exist_ok=True);dest=DATA/'online-retail.zip'
    if not dest.exists():
        r=requests.get('https://archive.ics.uci.edu/static/public/352/online+retail.zip',timeout=180);r.raise_for_status();dest.write_bytes(r.content)
    with zipfile.ZipFile(dest) as z:
        df=pd.read_excel(z.open(next(n for n in z.namelist() if n.endswith('.xlsx'))),engine='openpyxl')
    original=len(df);df=df.dropna(subset=['CustomerID','Description']);df=df[(df.Quantity>0)&(df.UnitPrice>0)&(~df.InvoiceNo.astype(str).str.startswith('C'))].copy()
    df['customer']=df.CustomerID.astype(int).astype(str);df['item']=df.StockCode.astype(str);df['date']=pd.to_datetime(df.InvoiceDate)
    return df.sort_values('date'),original
def history_map(frame,item_index):
    return {str(c):sorted({item_index[x] for x in items if x in item_index}) for c,items in frame.groupby('customer')['item']}
def prepare():
    df,original=download();days=sorted(df.date.dt.normalize().unique());a=pd.Timestamp(days[int(len(days)*.7)]);b=pd.Timestamp(days[int(len(days)*.85)])
    train=df[df.date<a];val=df[(df.date>=a)&(df.date<b)];test=df[df.date>=b]
    counts=train.groupby('item').customer.nunique();items=counts[counts>=5].sort_values(ascending=False).head(1600).index.tolist();index={v:i for i,v in enumerate(items)}
    histories=history_map(train,index);users=sorted(histories);row=[];col=[]
    for i,u in enumerate(users):
        for j in histories[u]:row.append(i);col.append(j)
    X=csr_matrix((np.ones(len(row),dtype='float32'),(row,col)),shape=(len(users),len(items)))
    catalog=[]
    for item in items:
        sub=train[train.item==item];catalog.append({'id':item,'name':str(sub.Description.mode().iloc[0]),'price':round(float(sub.UnitPrice.median()),2),'customers':int(counts[item])})
    groups={}
    for name,part in [('validation',val),('test',test)]:
        future=history_map(part,index);warm=[];cold=[]
        for u,target in sorted(future.items()):
            h=histories.get(u,[]);relevant=sorted(set(target)-set(h))
            if not relevant:continue
            entry={'user':hashlib.sha256(u.encode()).hexdigest()[:10],'history':h,'target':relevant}
            (warm if h else cold).append(entry)
        groups[name]={'warm':warm,'cold':cold,'transactions':len(part),'unknown_catalog_rate':float((~part.item.isin(index)).mean())}
    ART.mkdir(exist_ok=True);save_npz(ART/'train_matrix.npz',X);write_json(ART/'catalog.json',catalog);write_json(ART/'evaluation_cases.json',groups)
    write_json(ART/'split_manifest.json',{'seed':SEED,'train_end_exclusive':a.isoformat(),'validation_end_exclusive':b.isoformat(),'raw_rows':original,'clean_rows':len(df),'source_sha256':sha(DATA/'online-retail.zip'),'catalog_policy':'top 1600 train items, at least 5 train customers','catalog_size':len(items),'customers_train':len(users),'target_policy':'new-to-user known-catalog items; full-catalog ranking','cleaning':'drop absent customer/description, nonpositive quantity/price, cancellations','candidate_catalog':'training only'})
    return X,catalog,groups
def scores(history,model,weights):
    pop,similarity,factors=weights
    if not history:return pop.copy()
    if model=='popularity':s=pop.copy()
    elif model=='item_item':s=np.asarray(similarity[history].sum(axis=0)).ravel()
    elif model=='factorization':s=np.asarray(factors[history].sum(axis=0)@factors.T).ravel()
    else:raise ValueError('Unknown model')
    s=np.asarray(s,dtype=float);s[history]=-np.inf;return s
def ranking(history,model,weights,k=10):
    s=scores(history,model,weights);return np.argsort(-s,kind='stable')[:min(k,len(s)-len(history))].tolist()
def measure(cases,model,weights):
    recalls=[];ndcgs=[];covered=set()
    for case in cases:
        rec=ranking(case['history'],model,weights);target=set(case['target']);hits=[int(i in target) for i in rec];covered.update(rec)
        recalls.append(sum(hits)/len(target));dcg=sum(h/np.log2(i+2) for i,h in enumerate(hits));ideal=sum(1/np.log2(i+2) for i in range(min(10,len(target))));ndcgs.append(dcg/ideal)
    return {'Recall@10':float(np.mean(recalls)) if recalls else 0.,'NDCG@10':float(np.mean(ndcgs)) if ndcgs else 0.,'coverage':len(covered)/len(weights[0]),'users':len(cases)}
def train():
    started=time.perf_counter();np.random.seed(SEED);X,catalog,groups=prepare();print('Prepared',X.shape,flush=True)
    pop=np.asarray(X.sum(axis=0)).ravel();norm=normalize(X,axis=0);similarity=(norm.T@norm).toarray().astype('float32');np.fill_diagonal(similarity,0)
    with threadpool_limits(limits=2):
        svd=TruncatedSVD(n_components=48,n_iter=7,random_state=SEED);svd.fit(X)
    factors=svd.components_.T.astype('float32');np.savez_compressed(ART/'weights.npz',popularity=pop,similarity=similarity,factors=factors)
    write_json(ART/'config.json',{'seed':SEED,'latent_dimensions':48,'training_seconds':round(time.perf_counter()-started,2),'hardware':platform.processor() or platform.machine(),'selection':'maximum validation warm-user NDCG@10','algorithm':'TruncatedSVD of train binary interactions; cosine item similarity','rerank':'remove train history; stable item-index tie break'})
    evaluate(initial=True)
def load_weights():
    w=np.load(ART/'weights.npz');return w['popularity'],w['similarity'],w['factors']
def evaluate(initial=False):
    groups=json.loads((ART/'evaluation_cases.json').read_text());weights=load_weights();result={}
    with threadpool_limits(limits=2):
        for part in ['validation','test']:
            result[part]={m:measure(groups[part]['warm'],m,weights) for m in ['popularity','item_item','factorization']};result[part+'_cold']=measure(groups[part]['cold'],'popularity',weights)
    result['selected_model']=max(result['validation'],key=lambda x:result['validation'][x]['NDCG@10'])
    t=time.perf_counter()
    for _ in range(100):ranking([0,1,2],result['selected_model'],weights)
    result['latency_ms']=(time.perf_counter()-t)*10
    if initial:write_json(ART/'metrics.json',result)
    else:
        old=json.loads((ART/'metrics.json').read_text());delta=max(abs(result[p][m][k]-old[p][m][k]) for p in ['validation','test'] for m in ['popularity','item_item','factorization'] for k in ['Recall@10','NDCG@10','coverage'])
        write_json(ROOT/'reports/reproduction.json',{'max_absolute_difference':delta,'tolerance':1e-8,'passed':delta<1e-8})
        if delta>=1e-8:raise RuntimeError('Reproduction failed')
    pd.DataFrame([{'split':p,'model':m,**v} for p in ['validation','test'] for m,v in result[p].items()]).to_csv(ROOT/'reports/metrics.csv',index=False)
    write_json(ROOT/'reports/artifact_hashes.json',{p.name:sha(p) for p in ART.iterdir() if p.is_file()});print(json.dumps(result,indent=2),flush=True);return result
if __name__=='__main__':(train if len(sys.argv)<2 or sys.argv[1]=='train' else evaluate)()
