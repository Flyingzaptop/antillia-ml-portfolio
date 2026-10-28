"""Local process owner; no global services or unrelated processes are stopped."""
from pathlib import Path
import argparse,json,os,socket,subprocess,sys,time,urllib.request
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'.runtime';STATE.mkdir(exist_ok=True)
PROJECTS=['01-demandcast','02-intentroute','03-terravision','04-machinesentinel','05-basketwise','06-reviewpulse','07-ai-desk']
def port_free(port):
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',port));return True
        except OSError:return False
def process_info(pid):
    script=f'Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}" | Select-Object ProcessId,ExecutablePath,CreationDate | ConvertTo-Json -Compress'
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except ValueError:return None
def start(slug):
    index=PROJECTS.index(slug);port=8101+index;p=ROOT/slug;python=p/'.venv/Scripts/python.exe'
    if not python.exists():raise RuntimeError(f'{slug}: run setup.ps1 first')
    if not port_free(port):print(f'{slug}: port {port} already in use; not starting another process.');return
    args=['serve.py'] if index==6 else ['-m','uvicorn','app:app' if index in (2,3) else 'backend.app:app','--host','127.0.0.1','--port',str(port)]
    env=os.environ.copy();env.update(PORT=str(port),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONUNBUFFERED='1')
    with (STATE/f'{slug}.stdout.log').open('ab') as out,(STATE/f'{slug}.stderr.log').open('ab') as err:
        proc=subprocess.Popen([str(python),*args],cwd=p,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    info=process_info(proc.pid);(STATE/f'{slug}.process.json').write_text(json.dumps({'pid':proc.pid,'python':str(python),'creation':info.get('CreationDate') if info else None,'port':port}),encoding='utf8')
    for _ in range(90):
        if proc.poll() is not None:raise RuntimeError(f'{slug}: process exited; inspect .runtime/{slug}.stderr.log')
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=2) as r:
                if r.status==200:print(f'{slug}: http://127.0.0.1:{port}');return
        except Exception:pass
        time.sleep(1)
    raise RuntimeError(f'{slug}: startup timed out; inspect logs')
def stop(slug):
    record=STATE/f'{slug}.process.json'
    if not record.exists():print(f'{slug}: no owned process');return
    r=json.loads(record.read_text());info=process_info(r['pid'])
    if info and info.get('ExecutablePath','').lower()==r['python'].lower() and info.get('CreationDate')==r['creation']:
        script='function Stop-OwnedTree([int]$taskPid) { $children=@(Get-CimInstance Win32_Process -Filter "ParentProcessId=$taskPid"); foreach($child in $children) { Stop-OwnedTree $child.ProcessId }; Stop-Process -Id $taskPid -ErrorAction SilentlyContinue }; Stop-OwnedTree '+str(int(r['pid']))
        subprocess.run(['powershell.exe','-NoProfile','-Command',script],check=True)
        for _ in range(30):
            if port_free(r['port']):break
            time.sleep(.2)
        if not port_free(r['port']):raise RuntimeError(f'{slug}: port still occupied after stopping owned process tree')
        print(f'{slug}: stopped')
    else:print(f'{slug}: original process absent; no process stopped')
    record.unlink()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','stop','status']);parser.add_argument('project',nargs='?',default='all',choices=['all',*PROJECTS]);a=parser.parse_args()
    selected=PROJECTS if a.project=='all' else [a.project]
    for slug in selected:
        if a.action=='start':start(slug)
        elif a.action=='stop':stop(slug)
        else:print(slug,'listening' if not port_free(8101+PROJECTS.index(slug)) else 'stopped')
if __name__=='__main__':main()
