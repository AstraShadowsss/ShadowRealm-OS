#!/usr/bin/python3
"""Store walking wallpapers once, outside the two larger source archives."""
from pathlib import Path
import argparse,tarfile,io
p=argparse.ArgumentParser();p.add_argument('components',type=Path);p.add_argument('rendered',type=Path);a=p.parse_args()
images=list(a.rendered.glob('ShadowRealm-OS-*-Circuit-Walker.png'));assert len(images)==8
with tarfile.open(a.components/'shadowrealm-os-walker-wallpapers.tar.gz','w:gz') as t:
 for f in sorted(images):t.add(f,arcname=f.name)
for name in ['shadowrealm-os-desktop-defaults-source.tar.gz','shadowrealm-os-artwork-source.tar.gz']:
 file=a.components/name
 with tarfile.open(file) as old,tarfile.open(str(file)+'.new','w:gz') as out:
  for member in old:
   if member.isfile() and ('circuit-walker' in member.name.lower()) and member.name.endswith('.png'):continue
   data=old.extractfile(member).read() if member.isfile() else None
   out.addfile(member,io.BytesIO(data) if data is not None else None)
 Path(str(file)+'.new').replace(file)
print('Replaced the entire old walking-wallpaper family with the shared SR set')
