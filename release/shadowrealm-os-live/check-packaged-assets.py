#!/usr/bin/python3
from pathlib import Path
import sys,json
root=Path(sys.argv[1]);desktop=root/'usr/share/shadowrealm-os/desktop'
modes=json.loads((desktop/'appearance-modes.json').read_text());catalog=json.loads((desktop/'icon-catalog.json').read_text())
assert len(modes)==8 and 'black-white' in modes and 'blue-white' not in modes
for mode,record in modes.items():
 assert (root/'usr/share/themes'/record['theme']/'gtk-3.0/gtk.css').is_file()
 assert (root/'usr/share/icons'/record['icons']/'index.theme').is_file()
 assert len(catalog[mode])==89
 for role in catalog[mode]:
  for prefix in ['shadow-','orbital-dock-','shadow-panel-']:
   assert (desktop/'runtime/icons'/mode/(prefix+role+'.png')).is_file(),(mode,role,prefix)
for f in list((desktop/'runtime/bin').iterdir())+[root/'usr/bin/shadowrealm-os-desktop']:
 if not f.is_file() or f.is_symlink():continue
 with f.open('rb') as stream:line=stream.readline(256)
 if line.startswith(b'#!'):assert b'\r' not in line,('Windows shebang',str(f))
assert not (root/'usr/share/icons/ShadowRealm-OS-BlueWhite').exists()
print('PASS packaged assets: eight themes, 89 roles each in all three families, Linux launchers, no retired theme')

import hashlib
for record in modes.values():
 palette=record['wallpaper_palette']
 one=desktop/'wallpapers'/('ShadowRealm-OS-'+palette+'-Circuit-Walker.png')
 two=root/'usr/share/backgrounds/shadowrealm-os/circuit-walker'/('ShadowRealm-OS-'+palette+'.png')
 assert one.is_file() and two.is_file(),palette
 assert hashlib.sha256(one.read_bytes()).digest()==hashlib.sha256(two.read_bytes()).digest(),palette
print('PASS walking wallpapers: all eight palettes share the verified new master')
