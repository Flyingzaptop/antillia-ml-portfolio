"""Create factual delivery ledger only after every acceptance gate below is evidenced."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,re,urllib.request
from package_portfolio import PROJECTS,ROOT,digest
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
clean={};relocated={}
for report in sorted((ROOT/'reports/packaging').glob('portable-*.json')):
    for row in read(report):
        if row.get('passed'):
            entry={**row,'evidence_file':str(report.relative_to(ROOT))}
            relocated[row['project']]=entry
            if row.get('clean_install'):clean[row['project']]=entry
missing=set(PROJECTS)-set(clean)
if missing:raise SystemExit('Clean installations not yet verified: '+', '.join(sorted(missing)))
results=[]
for index,slug in enumerate(PROJECTS):
    p=ROOT/slug;view=read(p/'reports/screenshots/browser-evidence.json')
    assert len(view)==6 and {(x['requestedWidth'],x['language']) for x in view}=={(w,l) for w in [390,768,1440] for l in ['pl','en']}
    assert not any(x['overflow'] or x['lang']!=x['language'] or abs(x['width']-x['requestedWidth'])>20 for x in view)
    npm=next((q for q in [p/'reports/npm-audit.json',p/'npm-audit.json'] if q.exists()),None)
    if npm is None:raise RuntimeError('Missing npm audit '+slug)
    assert read(npm)['metadata']['vulnerabilities']['total']==0
    audit=next((q for q in [p/'security-runtime.json',p/'reports/pip-audit.json',p/'reports/python-audit.json'] if q.exists()),None)
    if audit is None:raise RuntimeError('Missing Python audit '+slug)
    ad=read(audit);deps=ad.get('dependencies',ad if isinstance(ad,list) else [])
    assert not any(x.get('vulns') for x in deps)
    testpath=p/('evaluation-tests.txt' if slug=='07-ai-desk' else 'reports/tests.txt');testtext=testpath.read_text(encoding='utf-8-sig',errors='replace')
    if slug=='07-ai-desk':
        count=int(re.search(r'Ran (\d+) tests?',testtext).group(1));assert '\nOK' in testtext
    else:count=int(re.search(r'(\d+) passed',testtext).group(1))
    url=f'http://127.0.0.1:{8101+index}';path='/api/v1/readiness' if slug=='07-ai-desk' else '/api/v1/health'
    with urllib.request.urlopen(url+path,timeout=90) as response:assert response.status==200;readiness=json.load(response)
    archive=ROOT/'dist/final-20261028'/f'{slug}.zip';assert archive.exists()
    sha=digest(archive);assert (archive.with_suffix('.sha256')).read_text().split()[0]==sha
    package_evidence=[x for x in relocated.values() if x['project']==slug and 'source_verification' not in x]
    assert package_evidence,'Missing extracted-ZIP smoke: '+slug
    results.append({'project':slug,'url':url,'clean_install_passed':True,'clean_install_evidence':clean[slug]['evidence_file'],'extracted_zip_smoke_passed':True,'extracted_zip_evidence':relocated[slug]['evidence_file'],'backend_tests_passed':count,'responsive_checks':6,'npm_known_vulnerabilities':0,'python_known_vulnerabilities':0,'readiness':readiness,'archive':str(archive.relative_to(ROOT)),'archive_bytes':archive.stat().st_size,'sha256':sha})
live=read(ROOT/'07-ai-desk/evaluation/live-results.json');security=[x for x in live['results'] if x['category'] in ['access_denied','injection','document_injection']]
assistant={'live_scenarios':live['count'],'completed_transport':sum(x.get('transport_pass',False) for x in live['results']),'retrieval_checks_passed':live['retrieval_pass'],'forbidden_text_checks_passed':sum(x.get('security_pass',False) for x in security),'forbidden_text_cases':len(security),'semantic_citation_imprecision_observed':True,'limitations':'See README.md and 07-ai-desk/evaluation/qualitative-review.md; not independent certification.'}
result={'verified_at':datetime.now(ZoneInfo('Europe/Warsaw')).isoformat(),'status':'local_demonstrators_verified_and_packaged','scope':'Windows/Python3.12; CPU ML inference, local Ollama generation; no public deployment','all_seven_clean_installations':True,'all_seven_extracted_archive_smokes':True,'backend_tests_total':sum(x['backend_tests_passed'] for x in results),'browser_viewports_and_languages_total':42,'projects':results,'assistant':assistant,'remaining_limits':['Model quality differs by task; MachineSentinel recall29.4%, DemandCast seasonal baseline wins.','Small authored Polish NLP controls are not independent benchmarks.','AI retrieval67/70; individual citations can be semantically imprecise.','No conversational context passed to LLM; history stored for browsing only.','Buffered SSE after citation checks.','First installation needs package network access and separate Ollama model setup.','No external security certification, load testing, physical mobile testing or public hosting.']}
(ROOT/'FINAL_STATUS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
summary={'generated_at':result['verified_at'],'all_seven_relocation_passed':True,'clean_install_verified':PROJECTS,'all_seven_extracted_archive_smokes':True,'archives_created':True,'clean_install_evidence':clean,'archive_evidence':relocated}
(ROOT/'reports/packaging/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':result['status'],'tests':result['backend_tests_total'],'archives':len(results),'responsive_checks':42},ensure_ascii=False))
