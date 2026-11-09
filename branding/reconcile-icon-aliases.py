#!/usr/bin/python3
from pathlib import Path
import tarfile,tempfile,shutil,subprocess,json,io,re
import argparse
args=argparse.ArgumentParser();args.add_argument('source',type=Path);p=args.parse_args().source;components=p/'components'
with tempfile.TemporaryDirectory() as td:
 roots={}
 for name in ['desktop-defaults','artwork']:
  root=Path(td)/name;root.mkdir();roots[name]=root
  with tarfile.open(components/f'shadowrealm-os-{name}-source.tar.gz') as t:t.extractall(root,filter='data')
 desktop=roots['desktop-defaults']/'usr/share/shadowrealm-os/desktop';modes=json.loads((desktop/'appearance-modes.json').read_text());art=roots['artwork'];catalog={}
 for mode,m in modes.items():
  folder=desktop/'runtime/icons'/mode
  for f in folder.glob('shadow-*.svg'):
   if f.stem.startswith('shadow-panel-'):continue
   s=f.read_text();role=f.stem.removeprefix('shadow-');catalog.setdefault(mode,[]).append(role)
   dock=folder/f'orbital-dock-{role}.png'
   if not dock.exists():shutil.copyfile(f.with_suffix('.png'),dock)
   # Preserve existing panel glyphs; derive missing ones from the role stroke.
   panel=folder/f'shadow-panel-{role}.svg'
   if not panel.exists():
    at=s.find('<g fill=');body=s[at:s.rfind('</svg>')] if at>=0 else ''
    if body:panel.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 64 64">'+body+'</svg>')
   if panel.exists() and not panel.with_suffix('.png').exists():subprocess.run(['rsvg-convert','-w','24','-h','24','-o',str(panel.with_suffix('.png')),str(panel)],check=True)
  theme=art/'usr/share/icons'/m['icons'];count=0
  aliases={'appearance':'theme','software':'updates','power-off':'power','home':'files','volume':'audio','wallpaper':'image-viewer'}
  for f in theme.rglob('*.png'):
   stem=f.stem;role=None
   for prefix in ['shadowrealm-os-system-','shadowrealm-os-release-shadow-','shadowrealm-os-app-','shadowrealm-os-dock-','orbital-dock-','shadow-']:
    if stem.startswith(prefix):role=stem[len(prefix):];break
   if role is None or role.startswith(('panel-','switch-')) or role in ('menu','logo','dock-launcher'):continue
   role=aliases.get(role,role);src=folder/f'orbital-dock-{role}.png'
   if not src.exists():src=folder/f'shadow-{role}.png'
   if not src.exists():continue
   from PIL import Image
   im=Image.open(src).convert('RGBA');size=Image.open(f).size;im.resize(size,Image.Resampling.LANCZOS).save(f);count+=1
  print(mode,len(catalog[mode]),'roles, reconciled',count,'custom aliases',flush=True)
 for fn,root in [('shadowrealm-os-artwork-source.tar.gz',art),('shadowrealm-os-desktop-defaults-source.tar.gz',roots['desktop-defaults'])]:
  with tarfile.open(components/(fn+'.new'),'w:gz') as t:
   for f in sorted(root.iterdir()):t.add(f,arcname='./'+f.name)
  (components/(fn+'.new')).replace(components/fn)
print('Catalog and alias reconciliation complete')
