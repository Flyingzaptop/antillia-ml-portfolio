"""Restore trusted release model/data assets after cloning this repository."""
from pathlib import Path
import hashlib,json,zipfile,urllib.request,shutil,argparse
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='all');args=parser.parse_args();manifest=json.loads((ROOT/'release-assets.json').read_text());cache=ROOT/'.runtime/downloads';cache.mkdir(parents=True,exist_ok=True)
    projects=[x for x in manifest['projects'] if args.project=='all' or x['project']==args.project]
    if not projects:raise SystemExit('Unknown project')
    for p in projects:
        target=cache/(p['project']+'.zip')
        if not target.exists() or sha(target)!=p['sha256']:
            urllib.request.urlretrieve(p['url'],target)
        if sha(target)!=p['sha256']:raise RuntimeError('Release checksum mismatch')
        with zipfile.ZipFile(target) as z:
            for info in z.infolist():
                parts=Path(info.filename).parts
                if len(parts)<3 or parts[0]!=p['project'] or parts[1] not in {'artifacts','data','models'}:continue
                dest=(ROOT/info.filename).resolve()
                if not dest.is_relative_to((ROOT/p['project']).resolve()):raise RuntimeError('Unsafe archive path')
                if info.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(info) as source,dest.open('wb') as output:shutil.copyfileobj(source,output)
        print(p['project']+': model/data assets restored')
if __name__=='__main__':main()
