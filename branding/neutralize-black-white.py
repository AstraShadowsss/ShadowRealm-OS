#!/usr/bin/python3
"""Remove chromatic remnants from the monochrome theme and its owned assets."""
from pathlib import Path
from PIL import Image,ImageOps
import argparse,tarfile,tempfile,re
p=argparse.ArgumentParser();p.add_argument('components',type=Path);a=p.parse_args()
def gray(m):
 v=m.group()[1:];g=round(sum(int(v[i:i+2],16)*w for i,w in zip((0,2,4),(.2126,.7152,.0722))));return '#'+format(g,'02x')*3
def rgb(m):
 g=round(sum(int(m[i])*w for i,w in zip((2,3,4),(.2126,.7152,.0722))));return m[1]+'('+','.join([str(g)]*3)+(m[5] or '')+')'
with tempfile.TemporaryDirectory() as td:
 for kind in ['desktop-defaults','artwork']:
  root=Path(td)/kind;root.mkdir();file=a.components/f'shadowrealm-os-{kind}-source.tar.gz'
  with tarfile.open(file) as t:t.extractall(root,filter='data')
  count=0
  for f in root.rglob('*'):
   if not f.is_file() or not any('BlackWhite' in x or x=='black-white' for x in f.parts):continue
   if f.suffix=='.png':
    im=Image.open(f).convert('RGBA');g=ImageOps.grayscale(im);Image.merge('RGBA',(g,g,g,im.getchannel('A'))).save(f);count+=1
   elif f.suffix in ('.svg','.css','.xpm','.theme') or f.name in ('themerc','gtkrc'):
    text=re.sub(r'#[0-9a-fA-F]{6}\b',gray,f.read_text());text=re.sub(r'(rgba?)\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,\s*[\d.]+)?\)',rgb,text);f.write_text(text)
  with tarfile.open(str(file)+'.new','w:gz') as t:
   for item in sorted(root.iterdir()):t.add(item,arcname='./'+item.name)
  Path(str(file)+'.new').replace(file)
  print(kind,'monochrome PNGs',count)
