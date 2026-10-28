"""Freeze only this application's installed dependency closure, not unrelated system packages."""
from pathlib import Path
from importlib.metadata import distribution
from packaging.requirements import Requirement
import sys
root=Path(sys.argv[1]).resolve();pending=[]
for line in (root/'requirements.txt').read_text().splitlines():
    if line.strip() and not line.startswith(('#','-')):pending.append(Requirement(line))
seen={}
while pending:
    req=pending.pop();key=req.name.lower().replace('_','-')
    if key in seen:continue
    if req.marker and not req.marker.evaluate():continue
    d=distribution(req.name);seen[key]=(d.metadata['Name'],d.version)
    pending.extend(Requirement(r) for r in d.requires or [])
out='\n'.join(f'{n}=={v}' for _,(n,v) in sorted(seen.items()))+'\n'
(root/'requirements.lock').write_text(out,encoding='utf8')
print(f'Frozen {len(seen)} packages for {root.name}')
