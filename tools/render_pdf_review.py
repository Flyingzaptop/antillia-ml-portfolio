from pathlib import Path
import subprocess,json
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'.runtime/pdf-review/all';out.mkdir(parents=True,exist_ok=True)
poppler=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
images=[]
for p in sorted(ROOT.glob('0[1-6]-*/reports/experiment-report.pdf')):
    prefix=out/p.parents[1].name
    subprocess.run([str(poppler),'-scale-to','1000','-png',str(p),str(prefix)],check=True,capture_output=True)
    for image in sorted(out.glob(prefix.name+'-*.png')):images.append(image)
thumbs=[]
for p in images:
    im=Image.open(p).convert('RGB');im.thumbnail((270,400));tile=Image.new('RGB',(290,430),'#e5e8e1');tile.paste(im,((290-im.width)//2,15));ImageDraw.Draw(tile).text((10,414),p.stem,fill='#203c39');thumbs.append(tile)
cols=4;rows=(len(thumbs)+cols-1)//cols;sheet=Image.new('RGB',(cols*290,rows*430),'white')
for i,tile in enumerate(thumbs):sheet.paste(tile,((i%cols)*290,(i//cols)*430))
sheet.save(out/'contact-sheet.png');(out/'pages.json').write_text(json.dumps([str(p) for p in images],indent=2));print('Rendered',len(images),'pages')
