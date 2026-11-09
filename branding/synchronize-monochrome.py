#!/usr/bin/python3
"""Keep the monochrome runtime assets on the dark, current tile geometry."""
from pathlib import Path
from PIL import Image,ImageOps
import tarfile,tempfile,re,argparse
p=argparse.ArgumentParser();p.add_argument('components',type=Path);a=p.parse_args()
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 file=a.components/'shadowrealm-os-desktop-defaults-source.tar.gz'
 with tarfile.open(file) as t:t.extractall(root,filter='data')
 icons=root/'usr/share/shadowrealm-os/desktop/runtime/icons';bw=icons/'black-white'
 def gray(match):
  v=match.group()[1:];v=v if len(v)==6 else ''.join(c*2 for c in v);rgb=[int(v[i:i+2],16) for i in (0,2,4)];g=round(sum(c*w for c,w in zip(rgb,(.2126,.7152,.0722))));return '#'+format(g,'02x')*3
 for src in (icons/'neon').iterdir():
  if not src.is_file():continue
  dest=bw/src.name
  if src.suffix=='.png':
   im=Image.open(src).convert('RGBA');g=ImageOps.grayscale(im);Image.merge('RGBA',(g,g,g,im.getchannel('A'))).save(dest)
  elif src.suffix=='.svg':dest.write_text(re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',gray,src.read_text()))
 with tarfile.open(str(file)+'.new','w:gz') as t:
  for f in sorted(root.iterdir()):t.add(f,arcname='./'+f.name)
 Path(str(file)+'.new').replace(file)
print('Dark monochrome runtime geometry synchronized')
