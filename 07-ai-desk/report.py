from pathlib import Path
import json,hashlib,platform,html,csv
root=Path(__file__).parent;out=root/'reports';out.mkdir(exist_ok=True)
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'artifacts').rglob('*') if p.is_file()}
(out/'checksums.json').write_text(json.dumps(manifest,indent=2))
retrieval=json.loads((root/'evaluation/retrieval-results.json').read_text(encoding='utf-8')) if (root/'evaluation/retrieval-results.json').exists() else {}
live=json.loads((root/'evaluation/live-results.json').read_text(encoding='utf-8')) if (root/'evaluation/live-results.json').exists() else {}
rows=retrieval.get('results',[])
with (out/'retrieval.csv').open('w',newline='',encoding='utf-8') as f:
 writer=csv.DictWriter(f,fieldnames=['id','category','language','retrieval_pass','seconds']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in rows)
body=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>AI Desk — evaluation report</title><style>body{{font:16px/1.7 Georgia,serif;max-width:1000px;margin:60px auto;color:#203b35;padding:24px}}h1{{font-size:48px}}.eyebrow{{font:12px Arial;letter-spacing:3px}}table{{border-collapse:collapse;width:100%;font:12px Arial}}td,th{{padding:10px;border-bottom:1px solid #ccd8ca;text-align:left}}.metric{{display:inline-block;padding:25px;background:#edf2e5;margin-right:10px}}@media print{{body{{margin:0}}}}</style><p class="eyebrow">ANTILLIA PORTFOLIO / 07</p><h1>Knowledge, with evidence.</h1><p>AI Desk · Raport ewaluacji / Evaluation report</p><div class="metric">Retrieval checks<br><b>{retrieval.get('retrieval_pass','Not run')} / {retrieval.get('count','—')}</b></div><div class="metric">Live scenarios<br><b>{live.get('count','Not run')}</b></div><h2>What was measured</h2><p>40 bilingual document questions, plus permission, no-answer and injection scenarios. Security questions include repeated templates. Results are not an external benchmark. Retrieval success does not establish generated-answer correctness.</p><h2>Reproducibility</h2><p>Run evaluate.ps1 and evaluate.ps1 -Live. Sources: 20 fictional topics in PL/EN; MiniLM multilingual embeddings; local Qwen via Ollama. Python {platform.python_version()}. Model artifact hashes are in checksums.json.</p><h2>Retrieval evidence</h2><table><tr><th>ID</th><th>Category</th><th>Language</th><th>Pass</th><th>Seconds</th></tr>'''
for r in rows:body+='<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['id','category','language','retrieval_pass','seconds'])+'</tr>'
body+='</table><h2>Limitations</h2><p>Citation identifiers are verified, but semantic entailment is not proven automatically. Inspect source excerpts. No shell, browser or filesystem tools are exposed to the language model. This report describes a local demonstration, not certification.</p></html>'
(out/'report.html').write_text(body,encoding='utf-8')
print('Reports and checksums generated.')
