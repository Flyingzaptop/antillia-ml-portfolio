from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
changes={
'01-demandcast':'''\n/* Contrast refinement for small labels and readable muted content. */
.intro p,p{color:#65767a}.eyebrow,.chart-legend,.stats article>span,.controls label,.chart-foot,.small-label,footer,.date-stamp,.breadcrumb{color:#64766d}.chart text{fill:#65756d}.stats strong small{color:#64766d}.sidebar .side-label,.sidebar-bottom small{color:#a8bdc6}.protocol-grid small{color:#607365}\n''',
'05-basketwise':'''\n/* Small informative labels meet readable contrast on the paper surface. */
.hero p,.section-title p,.count,.sku,.product-bottom>span,.basket-empty p,.basket-explainer,.recommend-card p,.recommend-card small,.metrics p,.notes p,.notes small,footer p,footer a,.search input::placeholder{color:#756855}.eyebrow,.live,.profile select,.basket-empty h3,.clear,.latency,.metrics article>span,.benchmark h2,th{color:#7d654b}.product-bottom button,.recommend-card>button{color:#775338}.illustration>span{opacity:1;color:#746b60}\n'''}
for slug,css in changes.items():
    p=ROOT/slug/'frontend/src/style.css'
    if 'Contrast refinement' not in p.read_text() and 'Small informative labels' not in p.read_text():p.write_text(p.read_text()+css,encoding='utf8')
    ap=ROOT/slug/'backend/app.py';s=ap.read_text(encoding='utf8');s=s.replace('FileResponse, JSONResponse','FileResponse, JSONResponse, HTMLResponse').replace('FileResponse,JSONResponse','FileResponse,JSONResponse,HTMLResponse');s=s.replace("docs_url='/api/v1/docs'","docs_url=None")
    if "def offline_docs" not in s:
        s+='''\n@app.get('/api/v1/docs',response_class=HTMLResponse)
def offline_docs():
    import html
    schema=app.openapi()
    rows=''.join('<li><b>'+html.escape(method.upper())+'</b> '+html.escape(path)+'</li>' for path,methods in schema['paths'].items() for method in methods if method in ['get','post'])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Local API documentation</title><style>body{font:16px/1.7 system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4ef;padding:20px}</style><h1>'+html.escape(schema['info']['title'])+' API</h1><p>Offline documentation. <a href="/api/v1/openapi.json">OpenAPI JSON</a></p><ul>'+rows+'</ul><h2>Request and response schemas</h2><pre>'+html.escape(json.dumps(schema.get('components',{}),indent=2))+'</pre></html>'
'''
    ap.write_text(s,encoding='utf8')
print('Contrast and offline API documentation updated')
