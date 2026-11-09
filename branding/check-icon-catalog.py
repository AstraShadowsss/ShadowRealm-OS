#!/usr/bin/python3
"""Check the packaged catalog and coordinated theme assets without installation."""
from pathlib import Path
import argparse,tarfile,json,io,xml.etree.ElementTree as ET
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('components',type=Path);a=p.parse_args()
with tarfile.open(a.components/'shadowrealm-os-desktop-defaults-source.tar.gz') as t:
 names=set(t.getnames());prefix='./usr/share/shadowrealm-os/desktop/'
 modes=json.load(t.extractfile(prefix+'appearance-modes.json'));catalog=json.load(t.extractfile(prefix+'icon-catalog.json'))
 assert len(modes)==8 and 'black-white' in modes and 'blue-white' not in modes
 assert not any('BlueWhite' in n or 'blue-white' in n for n in names)
 assert set(modes)==set(catalog)
 for mode,roles in catalog.items():
  assert len(roles)>=80
  for role in roles:
   base=prefix+'runtime/icons/'+mode+'/shadow-'+role
   ET.fromstring(t.extractfile(base+'.svg').read())
   image=Image.open(t.extractfile(base+'.png'));assert image.width>=24 and image.mode=='RGBA'
   assert image.getpixel((0,0))[3]==0,(mode,role,'opaque corner')
 print('PASS: eight themes; complete role catalogs; valid vectors; transparent icon corners')
with tarfile.open(a.components/'shadowrealm-os-artwork-source.tar.gz') as t:
 names=set(t.getnames());assert not any('BlueWhite' in n or 'blue-white' in n for n in names)
 assert not any(n.endswith('/logo-focused/ShadowRealm-OS-Professional.png') for n in names)
 for mode,record in modes.items():
  theme='./usr/share/icons/'+record['icons']
  for role in catalog[mode]:assert theme+'/scalable/apps/shadowrealm-os-system-'+role+'.svg' in names
 print('PASS: theme lookup vectors present; retired palette and old Professional logo wallpaper absent')
