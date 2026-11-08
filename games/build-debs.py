#!/usr/bin/python3
"""Build nine independently removable native Linux game packages from source."""
import argparse, shutil, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
source=Path(__file__).resolve().parent
GAMES=[('shadow-pinball','Shadow Pinball','0.3.3','pinball'),('skull-invaders','Skull Invaders','0.1.0','arcade'),('shadow-runner','Shadow Runner','0.1.1','arcade'),('circuit-chase','Circuit Chase','0.1.1','classic'),('marble-reactor','Marble Reactor','0.2.0','classic'),('neon-ascent','Neon Ascent','0.1.0','classic'),('neon-breaker','Neon Breaker','0.1.0','classic'),('shadow-snake','Shadow Snake','0.1.1','classic'),('shadow-solitaire','Shadow Spider Solitaire','0.2.0','classic')]
def put(root,name,data,mode=0o644):
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data);path.chmod(mode)
for identity,title,upstream_version,kind in GAMES:
 version=upstream_version+'-1'
 with tempfile.TemporaryDirectory(prefix='shadowrealm-os-game-') as temp:
  root=Path(temp);assets=root/'usr/share/games'/identity;assets.mkdir(parents=True)
  if kind=='pinball':
   files=[source/'shadow-pinball/shadow-pinball.py'];command=f'/usr/bin/python3 /usr/share/games/{identity}/shadow-pinball.py'
   icon=source/'shadow-pinball'/f'{identity}.svg'
  else:
   files=[source/'shadow-arcade/arcade.py',source/'shadow-arcade/arcade-sound.py']
   if kind=='classic':files.append(source/'shadow-classics/classics.py')
   entry='classics.py' if kind=='classic' else 'arcade.py'
   command=f'/usr/bin/python3 /usr/share/games/{identity}/{entry} {identity}'
   icon=source/('shadow-classics' if kind=='classic' else 'shadow-arcade')/f'{identity}.svg'
  for f in files:shutil.copyfile(f,assets/f.name)
  put(root,f'usr/bin/{identity}',f'#!/bin/sh\nexec {command} "$@"\n',0o755)
  dest=root/'usr/share/icons/hicolor/scalable/apps'/icon.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(icon,dest)
  put(root,f'usr/share/applications/{identity}.desktop',f'[Desktop Entry]\nType=Application\nName={title}\nComment=Original offline ShadowRealm-OS arcade game\nExec={identity}\nIcon={identity}\nCategories=Game;ArcadeGame;\nTerminal=false\n')
  put(root,f'usr/share/doc/{identity}/copyright',(source/'LICENSE').read_text())
  put(root,'DEBIAN/control',f'Package: {identity}\nVersion: {version}\nSection: games\nPriority: optional\nArchitecture: all\nMaintainer: ShadowRealm-OS contributors <packages@shadowrealm-os.invalid>\nDepends: python3, python3-cairo, python3-gi, gir1.2-gtk-3.0, pulseaudio-utils\nDescription: {title}, an original offline ShadowRealm-OS game\n')
  subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'{identity}_{version}_all.deb')],check=True)
