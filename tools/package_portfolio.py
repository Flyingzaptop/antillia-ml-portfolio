"""Build standalone archives. No environment, secrets, live databases or external links escape."""
from __future__ import annotations
import argparse,hashlib,json,os,stat,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
PROJECTS=['01-demandcast','02-intentroute','03-terravision','04-machinesentinel','05-basketwise','06-reviewpulse','07-ai-desk']
EXCLUDED_DIRS={'.venv','node_modules','__pycache__','.pytest_cache','.git','.runtime','logs','.mypy_cache','.ruff_cache','.cache'}
EXCLUDED_FILES={'.env','.local-secret','demo-credentials.json','.DS_Store','Thumbs.db'}
MODEL_PREFIXES=('artifacts/encoder/','artifacts/models/','models/encoder/')
KNOWN_MODEL_ROOTS=[Path.home()/'.cache/huggingface/hub',*[ROOT/p/'artifacts/encoder' for p in PROJECTS]]
def digest(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def excluded(rel:Path)->bool:
 low=rel.name.lower()
 return bool(set(rel.parts)&EXCLUDED_DIRS) or low in EXCLUDED_FILES or low.startswith('.env.') and low!='.env.example' or low.endswith(('.log','.pid','.pyc','.pyo','.sqlite3','.sqlite3-wal','.sqlite3-shm','.sqlite','.db','.tmp')) or low.startswith(('malicious-','malicious_','outside.','traversal-','traversal_'))
def files_for(project:Path):
 """Flatten allowed model links; reject other external links and cycles."""
 project=project.resolve();pending=[(project,Path())]
 while pending:
  current,rel=pending.pop()
  for child in sorted(current.iterdir(),key=lambda p:p.name):
   rp=rel/child.name
   if excluded(rp):continue
   resolved=child.resolve(strict=True)
   external=not resolved.is_relative_to(project)
   if external and (not any(rp.as_posix().startswith(pre) or rp.as_posix()==pre.rstrip('/') for pre in MODEL_PREFIXES) or not any(resolved.is_relative_to(p.resolve()) for p in KNOWN_MODEL_ROOTS)):raise ValueError(f'External link outside known model roots: {rp}')
   if child.is_dir():
    if resolved==project or resolved in [project.joinpath(*rp.parts[:i]).resolve() for i in range(len(rp.parts))]:raise ValueError(f'Directory link cycle: {rp}')
    pending.append((resolved,rp))
   elif child.is_file():
    if external and child.suffix.lower() not in {'.json','.safetensors','.bin','.txt','.model','.pt','.pth','.npy','.npz'}:raise ValueError(f'Unexpected external model file: {rp}')
    yield resolved,rp,external
   else:raise ValueError(f'Unsupported file type: {rp}')
def verify_recorded_hashes(project:Path)->dict:
 checked=[]
 for filename in ['artifact-checksums.json','artifact_hashes.json','checksums.json']:
  path=project/'reports'/filename
  if path.exists():
   for rel,expected in json.loads(path.read_text(encoding='utf-8-sig')).items():
    candidate=project/rel if '/' in rel or '\\' in rel else project/'artifacts'/rel
    if not candidate.resolve().is_relative_to(project.resolve()):raise ValueError('Unsafe manifest path')
    actual=digest(candidate)
    if actual!=expected:raise ValueError(f'Artifact hash mismatch: {candidate}')
    checked.append(str(candidate.relative_to(project)))
 source_names={'01-demandcast':'bike-sharing.zip','03-terravision':'source.zip','04-machinesentinel':'source.zip','05-basketwise':'online-retail.zip'}
 for path in [project/'artifacts/config.json',project/'artifacts/split_manifest.json']:
  if path.exists():
   data=json.loads(path.read_text(encoding='utf-8-sig'));expected=data.get('source_sha256')
   if expected and project.name in source_names:
    source=project/'data'/source_names[project.name]
    if digest(source)!=expected:raise ValueError(f'Dataset source hash mismatch: {source}')
    checked.append(str(source.relative_to(project)))
 return {'verified_against_recorded_hashes':checked,'note':'All packaged files additionally receive SHA256 entries; encoder weights without prior manifest are inventoried, not claimed independently authenticated.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--projects',nargs='+',choices=PROJECTS,default=PROJECTS);ap.add_argument('--output',type=Path,default=ROOT/'dist');ap.add_argument('--dry-run',action='store_true');args=ap.parse_args()
 out=args.output.resolve()
 if not out.is_relative_to(ROOT):raise SystemExit('Output must remain inside Portfolio')
 if not args.dry_run:out.mkdir(parents=True,exist_ok=True)
 results=[]
 for slug in args.projects:
  project=ROOT/slug;verification=verify_recorded_hashes(project);entries=list(files_for(project));manifest={'project':slug,'created_utc':datetime.now(timezone.utc).isoformat(),'exclusions':sorted(EXCLUDED_DIRS|EXCLUDED_FILES),'source_verification':verification,'files':{}}
  archive=out/(slug+'.zip')
  if archive.exists() and not args.dry_run:raise FileExistsError(f'Archive already exists; select a fresh --output directory: {archive}')
  z=None if args.dry_run else zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)
  try:
   for path,rel,external in entries:
    before=path.stat();checksum=digest(path);manifest['files'][rel.as_posix()]={'sha256':checksum,'bytes':before.st_size,'external_model_link_materialized':external}
    if z:z.write(path,slug+'/'+rel.as_posix())
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError(f'File changed during packaging: {rel}')
   if z:z.writestr(slug+'/PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2,ensure_ascii=False))
  finally:
   if z:z.close()
  if not args.dry_run:
   with zipfile.ZipFile(archive) as check:
    if check.testzip():raise RuntimeError('ZIP integrity check failed')
   archive_hash=digest(archive);(out/(slug+'.sha256')).write_text(archive_hash+'  '+archive.name+'\n',encoding='utf-8')
  else:archive_hash=None
  results.append({'project':slug,'files':len(entries),'uncompressed_bytes':sum(v['bytes'] for v in manifest['files'].values()),'archive':str(archive),'sha256':archive_hash,'source_verification':verification});print(json.dumps(results[-1]),flush=True)
 reportdir=ROOT/'reports/packaging';reportdir.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');(reportdir/('inventory-'+stamp+'.json')).write_text(json.dumps({'dry_run':args.dry_run,'results':results},indent=2),encoding='utf-8')
if __name__=='__main__':main()
