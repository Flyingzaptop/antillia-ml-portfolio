from pathlib import Path
from importlib.metadata import version
import sys
p=Path(sys.argv[1]).resolve();names=[line.split('==')[0] for line in (p/'requirements.txt').read_text().splitlines() if line and not line.startswith(('#','-'))]
if p.name=='05-basketwise':names=[n for n in names if n not in ['torch','matplotlib']]
prefix='--extra-index-url https://download.pytorch.org/whl/cpu\n' if 'torch' in names else ''
(p/'requirements.txt').write_text(prefix+'\n'.join(n+'=='+version(n) for n in names)+'\n',encoding='utf8')
print('Updated direct pins:',p.name)
