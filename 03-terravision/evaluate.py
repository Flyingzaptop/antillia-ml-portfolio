import json,pickle,time,csv
import numpy as np,torch
from PIL import Image
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from core import *
def main():
 torch.set_num_threads(4);splits=json.loads((ROOT/'artifacts/splits.json').read_text());rows=splits['test'];y=[r['label'] for r in rows];base=pickle.load(open(ROOT/'artifacts/baseline.pkl','rb'));model=network();model.load_state_dict(torch.load(ROOT/'artifacts/resnet18.pt',weights_only=True,map_location='cpu'));model.eval();pred=[];start=time.time()
 with torch.no_grad():
  for x,_ in torch.utils.data.DataLoader(Dataset(rows),batch_size=128):pred.extend(model(x).argmax(1).tolist())
 elapsed=time.time()-start;bpred=base.predict(np.stack([features(Image.open(ROOT/r['path']).convert('RGB')) for r in rows]));metrics={}
 for name,pr in [('resnet18',pred),('baseline',bpred)]:metrics[name]={'accuracy':accuracy_score(y,pr),'macro_f1':f1_score(y,pr,average='macro'),'per_class':classification_report(y,pr,target_names=CLASSES,output_dict=True),'confusion_matrix':confusion_matrix(y,pr).tolist()}
 result={'models':metrics,'test_count':len(rows),'latency_ms_per_image_batch':elapsed*1000/len(rows),'config':json.loads((ROOT/'artifacts/config.json').read_text()),'errors':[{'path':r['path'],'actual':CLASSES[t],'predicted':CLASSES[p]} for r,t,p in zip(rows,y,pred) if t!=p][:30]}
 (ROOT/'reports/metrics.json').write_text(json.dumps(result,indent=2));f=open(ROOT/'reports/metrics.csv','w',newline='');w=csv.writer(f);w.writerow(['model','accuracy','macro_f1']);[w.writerow([n,v['accuracy'],v['macro_f1']]) for n,v in metrics.items()];f.close();print(json.dumps({n:{k:v[k] for k in ['accuracy','macro_f1']} for n,v in metrics.items()}),flush=True)
if __name__=='__main__':
 main()
 import runpy
 runpy.run_path(str(ROOT/'report.py'))
