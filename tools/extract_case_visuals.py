"""Create compact, factual visual evidence from our saved model artifacts."""
from pathlib import Path
import json,sqlite3
import numpy as np,torch,joblib
from sklearn.decomposition import PCA
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'case-study-assets';OUT.mkdir(exist_ok=True)
def reduce(a,rows=24,cols=24):
    a=np.asarray(a);return np.array([[block.mean() for block in np.array_split(part,cols,axis=1)] for part in np.array_split(a,rows,axis=0)]).tolist()
data={}
w=torch.load(ROOT/'01-demandcast/artifacts/gru.pt',map_location='cpu',weights_only=True)['gru.weight_hh_l0'].numpy()
data['demandcast']={'kind':'heatmap','shape':list(w.shape),'values':reduce(w),'caption_pl':'Wyuczone wagi rekurencyjne GRU: 96 × 32. Wizualizacja zagregowana do 24 × 24.','caption_en':'Learned GRU recurrent weights: 96 × 32. Aggregated to a 24 × 24 view.'}
for slug,name in [('02-intentroute','intentroute'),('06-reviewpulse','reviewpulse')]:
    model=joblib.load(ROOT/slug/'artifacts/embedding_mlp.joblib');w=model.coefs_[0]
    data[name]={'kind':'heatmap','shape':list(w.shape),'values':reduce(w),'caption_pl':f'Rzeczywiste wagi wyuczonej głowicy MLP: {w.shape[0]} × {w.shape[1]}. Średnie blokowe; kolor nie oznacza ważności cechy.','caption_en':f'Actual learned MLP-head weights: {w.shape[0]} × {w.shape[1]}. Block means; color is not feature importance.'}
w=torch.load(ROOT/'04-machinesentinel/artifacts/autoencoder.pt',map_location='cpu',weights_only=True)['0.weight'].numpy()
data['machinesentinel']={'kind':'heatmap','shape':list(w.shape),'values':w.tolist(),'caption_pl':'Pierwsza warstwa encodera: 12 neuronów × 5 sygnałów. Rzeczywiste zapisane wagi.','caption_en':'First encoder layer: 12 neurons × 5 signals. Actual saved weights.'}
w=np.load(ROOT/'05-basketwise/artifacts/weights.npz')['factors']
data['basketwise']={'kind':'heatmap','shape':list(w.shape),'values':w[:24,:24].tolist(),'caption_pl':'Fragment macierzy czynników: pierwsze 24 produkty × 24 z 48 wymiarów latentnych.','caption_en':'Factor-matrix excerpt: first 24 products × 24 of the 48 latent dimensions.'}
w=torch.load(ROOT/'03-terravision/artifacts/resnet18.pt',map_location='cpu',weights_only=True)['conv1.weight'].numpy()
filters=[]
for f in w[:32]:
    rgb=f.transpose(1,2,0);rgb=(rgb-rgb.min())/(rgb.max()-rgb.min()+1e-9);filters.append(np.round(rgb*255).astype(int).tolist())
data['terravision']={'kind':'filters','values':filters,'shape':list(w.shape),'caption_pl':'Pierwsze 32 z 64 filtrów wyuczonej warstwy conv1 (RGB, 7 × 7). Każdy filtr normalizowany osobno.','caption_en':'First 32 of 64 learned conv1 filters (RGB, 7 × 7). Each filter normalized separately.'}
db=sqlite3.connect(f'file:{(ROOT/"07-ai-desk/data.sqlite3").as_posix()}?mode=ro',uri=True)
rows=db.execute('SELECT d.title,d.language,d.access,c.vector FROM desk_chunk c JOIN desk_document d ON c.document_id=d.id ORDER BY c.id').fetchall();db.close()
vectors=np.array([json.loads(x[3]) for x in rows]);pca=PCA(n_components=2,random_state=42);xy=pca.fit_transform(vectors)
data['ai-desk']={'kind':'embedding','points':[{'title':r[0],'language':r[1],'access':r[2],'x':float(pos[0]),'y':float(pos[1])} for r,pos in zip(rows,xy)],'variance':float(pca.explained_variance_ratio_.sum()),'caption_pl':'Rzeczywiste embeddings 40 fikcyjnych dokumentów PL/EN, rzut PCA 2D. Projekcja redukuje informację; nie jest pełną mapą podobieństwa.','caption_en':'Actual embeddings of 40 fictional PL/EN documents, projected with 2D PCA. Projection loses information; it is not a full similarity map.'}
(OUT/'model-evidence.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8');print('Saved real visual evidence for',len(data),'projects')
