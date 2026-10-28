from pathlib import Path
import json,html,hashlib,importlib.metadata as md
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'reports/metrics.json').read_text());name=ROOT.name.split('-',1)[1].title();selected=m['config']['selected'];metrics=m['models'];keys=['accuracy','macro_f1'] if 'terravision' in ROOT.name else ['pr_auc','roc_auc','precision','recall']
fig,ax=plt.subplots(figsize=(9,4));xs=range(len(keys));width=.35
for i,(n,v) in enumerate(metrics.items()):ax.bar([x+(i-.5)*width for x in xs],[v[k] for k in keys],width,label=n,color=['#325c49','#a8bc91'][i])
ax.set_xticks(list(xs),keys);ax.set_ylim(0,1);ax.legend();ax.set_title(name+' — held-out test');fig.tight_layout();fig.savefig(ROOT/'reports/metrics.png',dpi=150);plt.close(fig)
cm=metrics[selected]['confusion_matrix'];fig,ax=plt.subplots(figsize=(7,6));im=ax.imshow(cm,cmap='Greens');ax.set_xlabel('Predicted');ax.set_ylabel('Actual');ax.set_title('Confusion matrix: '+selected)
for i,row in enumerate(cm):
 for j,v in enumerate(row):ax.text(j,i,str(v),ha='center',va='center',fontsize=7,color='white' if v>max(map(max,cm))*.5 else '#234')
fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(ROOT/'reports/confusion.png',dpi=150);plt.close(fig)
rows=''.join('<tr><th>'+n+'</th>'+''.join('<td>'+format(v[k],'.5f')+'</td>' for k in keys)+'</tr>' for n,v in metrics.items())
limitations=('Random stratified deduplicated images are not geographically independent. No guarantee of regional transfer. RGB inputs only. Grad-CAM is not causal. Images from other domains can receive confident wrong predictions.' if 'terravision' in ROOT.name else 'AI4I is synthetic. Low recall means failures may be missed. Anomaly scores are not calibrated failure probabilities. This prototype must not control safety-critical equipment.')
body=f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>{name} — experiment report</title><style>body{{font:15px Arial;color:#243d34;max-width:950px;margin:50px auto;padding:25px;line-height:1.6}}h1{{font-size:42px}}small{{letter-spacing:2px}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ccd;padding:12px;text-align:left}}img{{max-width:100%}}code{{overflow-wrap:anywhere}}.notice{{background:#edf2e7;padding:20px}}@media print{{body{{margin:0}}h2{{break-after:avoid}}img{{max-height:410px;object-fit:contain}}}}</style><small>ANTILLIA / APPLIED INTELLIGENCE</small><h1>{name}</h1><p>Reproducible experiment report / Raport eksperymentu</p><h2>Method / Metoda</h2><p>Seed 42. Frozen 70/15/15 train / validation / test split. Model selection on validation only. Selected model: <b>{selected}</b>. Test observations: {m['test_count']}. Training: {m['config']['training_seconds']:.1f} seconds.</p><h2>Held-out results / Wyniki testowe</h2><table><tr><th>Model</th>{''.join('<th>'+k+'</th>' for k in keys)}</tr>{rows}</table><img src="metrics.png" alt="Measured model comparison"><img src="confusion.png" alt="Test confusion matrix"><h2>Limitations / Ograniczenia</h2><div class="notice">{limitations}</div><h2>Reproduce / Odtworzenie</h2><p>Run train.ps1 for training; evaluate.ps1 for saved weights and frozen test set. Full metadata: artifacts/config.json. Source checksum: <code>{m['config']['source_sha256']}</code>. Library versions in reports/environment.txt. Machine-readable metrics in metrics.json and metrics.csv. No external certification is claimed.</p></html>"""
(ROOT/'reports/report.html').write_text(body,encoding='utf-8')
manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts').iterdir() if p.is_file()};(ROOT/'reports/artifact-checksums.json').write_text(json.dumps(manifest,indent=2))
names=['numpy','pandas','scikit-learn','torch','Pillow','fastapi','starlette','uvicorn','python-multipart','requests','httpx','pytest','matplotlib']
if 'terravision' in ROOT.name:names.append('torchvision')
(ROOT/'reports/environment.txt').write_text('\n'.join(n+'=='+md.version(n) for n in names))
