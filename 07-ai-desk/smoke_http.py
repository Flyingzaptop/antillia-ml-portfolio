"""Live same-origin auth + CSRF + SSE test against the running local server."""
import json,time
from pathlib import Path
import requests
root=Path(__file__).parent;base='http://127.0.0.1:8107/api/v1';s=requests.Session()
credentials=next(x for x in json.loads((root/'demo-credentials.json').read_text()) if x['username']=='user')
csrf=s.get(base+'/session',timeout=10).json()['csrf']
r=s.post(base+'/login',json={'username':credentials['username'],'password':credentials['password']},headers={'X-CSRFToken':csrf},timeout=10);r.raise_for_status();csrf=r.json()['csrf'];headers={'X-CSRFToken':csrf}
r=s.post(base+'/chats',headers=headers,timeout=10);r.raise_for_status();chat=r.json()['id'];start=time.perf_counter()
try:
 r=s.post(f'{base}/chats/{chat}/ask',json={'text':'How many days in advance should I request annual leave?','language':'en'},headers=headers,stream=True,timeout=(10,180));r.raise_for_status();events=[json.loads(line.decode()[6:]) for line in r.iter_lines() if line.startswith(b'data: ')];answer=''.join(e.get('text','') for e in events if e['type']=='token');done=any(e['type']=='done' for e in events);assert done and answer
 result={'passed':True,'seconds':round(time.perf_counter()-start,3),'answer':answer,'events':[e['type'] for e in events],'checks':['session','CSRF login','create own chat','real Ollama terminal SSE','delete own chat']}
finally:
 r=s.delete(f'{base}/chats/{chat}',headers=headers,timeout=10);r.raise_for_status()
(root/'evaluation/http-smoke.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('HTTP auth/CSRF/live SSE smoke passed')
