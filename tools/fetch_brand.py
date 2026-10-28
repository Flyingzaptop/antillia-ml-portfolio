from pathlib import Path
from urllib.parse import urljoin
import requests
root=Path(__file__).resolve().parents[1];dest=root/'case-study-assets';dest.mkdir(exist_ok=True)
for source,name in [('site.css?v=antillia-6','antillia-site.css'),('showcase.css?v=antillia-6','antillia-showcase.css'),('antillia.svg','antillia.svg'),('fonts/manrope-latin.woff2','manrope-latin.woff2')]:
    r=requests.get(urljoin('https://antillia.tech/',source),timeout=30);r.raise_for_status();(dest/name).write_bytes(r.content);print(name,len(r.content))
for name in ['manrope-latin.woff2','manrope-latin-ext.woff2','dm-sans-latin.woff2','dm-sans-latin-ext.woff2']:
    (dest/'fonts').mkdir(exist_ok=True);r=requests.get('https://antillia.tech/fonts/'+name,timeout=30);r.raise_for_status();(dest/'fonts'/name).write_bytes(r.content)
for family in ['manrope','dmsans']:
    r=requests.get(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{family}/OFL.txt',timeout=30);r.raise_for_status();(dest/'fonts'/f'{family}-OFL.txt').write_bytes(r.content)
