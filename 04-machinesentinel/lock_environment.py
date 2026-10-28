import importlib.metadata as md
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from pathlib import Path
root=Path(__file__).resolve().parent
pending=['fastapi','starlette','uvicorn','python-multipart','numpy','pandas','scikit-learn','torch','Pillow','requests','httpx','pytest','matplotlib']
if 'terra' in root.name:pending+=['torchvision']
seen={}
while pending:
 name=canonicalize_name(pending.pop())
 if name in seen:continue
 dist=md.distribution(name);seen[name]=dist.version.split('+')[0]
 for raw in dist.requires or []:
  r=Requirement(raw)
  if r.marker is None or r.marker.evaluate({'extra':''}):pending.append(r.name)
(root/'requirements.txt').write_text('\n'.join(n+'=='+v for n,v in sorted(seen.items()))+'\n')
