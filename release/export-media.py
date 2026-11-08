#!/usr/bin/python3
"""Export current factory artwork by purpose, without owner profiles or old aliases."""
from pathlib import Path
import argparse,hashlib,io,json,tarfile
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=a.root.resolve();base=r/'usr/share/shadowrealm-os/desktop';modes=json.loads((base/'appearance-modes.json').read_text());seen={};count=0
with tarfile.open(a.output,'w:gz') as out:
 def add(file,name):
  global count
  target=file.resolve()
  if not target.is_relative_to(r):target=(r/str(target).lstrip('/')).resolve()
  if not target.is_relative_to(r) or not target.is_file():return
  key=name.casefold();digest=hashlib.sha256(target.read_bytes()).hexdigest()
  if key in seen:
   if seen[key]!=digest:raise ValueError('Conflicting Windows filename: '+name)
   return
  seen[key]=digest;info=out.gettarinfo(str(target),arcname=name);info.uid=info.gid=0;info.uname=info.gname='root';info.mode=0o644
  with target.open('rb') as stream:out.addfile(info,stream)
  count+=1
 def tree(folder,name):
  for f in sorted(folder.rglob('*')):
   if f.is_file() and f.name!='icon-theme.cache':add(f,name+'/'+str(f.relative_to(folder)))
 for mode,record in modes.items():
  tree(r/'usr/share/themes'/record['theme'],'Desktop Themes/'+record['theme'])
  tree(r/'usr/share/icons'/record['icons'],'Icon Packs/'+record['icons'])
  folder=base/'runtime/icons'/mode
  for f in sorted(folder.rglob('*')):
   if not f.is_file():continue
   if f.name=='term.png':name='Terminal/'+mode+'/Header.png'
   elif 'logo' in f.name:name='Logos/'+mode+'/'+str(f.relative_to(folder))
   else:name='Launcher and Dock Icons/'+mode+'/'+str(f.relative_to(folder))
   add(f,name)
 tree(base/'wallpapers','Wallpapers');tree(base/'runtime/sounds','Sounds')
 tree(r/'usr/share/sounds/ShadowRealm-OS','Sounds/Session and Alarm Chimes')
 tree(r/'usr/share/plymouth/themes/shadowrealm-os','Boot and Shutdown/Plymouth')
 tree(r/'usr/share/backgrounds/shadowrealm-os/logo-focused','Boot and Shutdown/Theme Backgrounds')
 tree(r/'usr/share/shadowrealm-os/branding','Logos/Boot and Login')
 add(r/'usr/share/doc/shadowrealm-os-artwork/LICENSE','Licenses/Original ShadowRealm-OS MIT.txt')
 add(r/'usr/share/doc/shadowrealm-os-artwork/gnome-icon-copyright','Licenses/GNOME icon notices.txt')
 summary={mode:{k:v for k,v in record.items() if k in ['label','theme','icons','wm','accent','secondary','background','foreground','light','unbranded']} for mode,record in modes.items()}
 data=(json.dumps(summary,indent=2)+'\n').encode();info=tarfile.TarInfo('Theme index.json');info.size=len(data);info.mode=0o644;out.addfile(info,io.BytesIO(data))
print('Exported',count,'current factory assets across',len(modes),'themes; case-collision checks passed.')
