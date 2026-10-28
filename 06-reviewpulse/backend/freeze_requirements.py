"""Freeze this project's runtime dependency closure, excluding unrelated global packages."""
import importlib.metadata as md
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from pathlib import Path
import json
roots=['fastapi','uvicorn','python-multipart','sentence-transformers','transformers','httpx','pytest','torch','scikit-learn','numpy','scipy','joblib','pydantic','huggingface-hub','safetensors','tokenizers','starlette','pillow']
todo=roots[:]; result={}
while todo:
 name=canonicalize_name(todo.pop())
 if name in result:continue
 dist=md.distribution(name);result[name]=dist.version.split('+')[0]
 for item in dist.requires or []:
  req=Requirement(item)
  if req.marker is None or req.marker.evaluate({'extra':''}):todo.append(req.name)
p=Path(__file__).resolve().parents[1]
(p/'requirements.txt').write_text('\n'.join(f'{k}=={v}' for k,v in sorted(result.items()))+'\n',encoding='utf-8')
(p/'reports/runtime-environment.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(f'Pinned {len(result)} dependencies')
