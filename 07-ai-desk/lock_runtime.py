"""Capture the installed dependency closure, excluding unrelated global packages."""
from importlib.metadata import distribution
from packaging.requirements import Requirement
from pathlib import Path
root=Path(__file__).parent;queue=[];seen={}
for line in (root/'requirements.txt').read_text().splitlines():
 if line.strip() and not line.startswith('-'):queue.append(Requirement(line).name)
while queue:
 name=queue.pop();key=name.lower().replace('_','-')
 if key in seen:continue
 d=distribution(name);seen[key]=d.version
 for text in d.requires or []:
  r=Requirement(text)
  if r.marker is None or r.marker.evaluate({'extra':''}):queue.append(r.name)
(root/'requirements-runtime.txt').write_text('--extra-index-url https://download.pytorch.org/whl/cpu\n'+'\n'.join(f'{n}=={v}' for n,v in sorted(seen.items()))+'\n')
print(len(seen),'runtime dependencies locked')
