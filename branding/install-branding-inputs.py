#!/usr/bin/python3
"""Replace owned branding entries inside the editable package source archives."""
from pathlib import Path
from PIL import Image
import argparse,tarfile,io,gzip,subprocess,json
p=argparse.ArgumentParser();p.add_argument('components',type=Path);p.add_argument('assets',type=Path);a=p.parse_args()
palettes={'woodland':'Woodland','white-silver-gold':'WhiteSilverGold','red-black':'RedBlack','professional':'Professional','neon':'Neon','hacker':'Hacker','blue-white':'BlueWhite','black-blue':'BlackBlue'}
def palette(name):
 for key,value in palettes.items():
  if key in name.lower() or value.lower() in name.lower():return value
 return 'Neon'
cache={}
def logo(data,theme,kind='SR'):
 try:w,h=Image.open(io.BytesIO(data)).size
 except Exception:w,h=256,256
 key=(theme,w,h,kind)
 if key not in cache:
  f=a.assets/f'{kind}-{theme}-{w}x{h}.png'
  subprocess.run(['rsvg-convert','--keep-aspect-ratio','-w',str(w),'-h',str(h),'-o',str(f),str(a.assets/f'{kind}-{theme}.svg')],check=True)
  cache[key]=f.read_bytes()
 return cache[key]
changes=[]
# Render existing vector role masters directly; preserve vendor icon files.
vector_cache={}
def vector_png(archive,name,data):
 stem=Path(name).stem
 role=stem
 for prefix in ('orbital-dock-','shadow-panel-','shadowrealm-os-app-','shadowrealm-os-release-','shadow-'):
  if role.startswith(prefix):role=role[len(prefix):];break
 aliases={'appearance':'theme','launcher':'app-menu','software':'updates','power-off':'power','volume':'audio','home':'files'}
 role=aliases.get(role,role)
 parent=str(Path(name).parent)
 candidates=[parent+'/'+stem+'.svg',parent+'/shadow-'+role+'.svg']
 theme=palette(name)
 # Runtime SVGs are the authoritative palette-specific role geometry.
 for member in archive.getnames():
  if member.endswith('/shadow-'+role+'.svg') and palette(member)==theme:
   candidates.append(member)
 for candidate in candidates:
  try:entry=archive.getmember(candidate)
  except KeyError:continue
  key=(filename,candidate,Image.open(io.BytesIO(data)).size)
  if key not in vector_cache:
   w,h=key[-1]
   result=subprocess.run(['rsvg-convert','--keep-aspect-ratio','-w',str(w),'-h',str(h)],input=archive.extractfile(entry).read(),stdout=subprocess.PIPE,check=True)
   vector_cache[key]=result.stdout
  return vector_cache[key]
 return None

for filename in ('shadowrealm-os-artwork-source.tar.gz','shadowrealm-os-desktop-defaults-source.tar.gz','shadowrealm-os-terminal-assets.tar.gz'):
 f=a.components/filename;temp=f.with_suffix('.new')
 with tarfile.open(f) as old,temp.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as out:
  for m in old:
   if Path(m.name).name.startswith('proton-'):
    continue
   if filename=='shadowrealm-os-artwork-source.tar.gz' and '/branding/Wordmark-' in m.name:
    continue
   data=old.extractfile(m).read() if m.isfile() else None
   name=m.name;stem=Path(name).stem;theme=palette(name);replacement=None
   if data is not None and name.endswith('.png'):
    # Wallpaper collection and fixed boot/login variants share one rendered master.
    for family in ('logo-focused','circuit-corridor','full-artwork','seated-city'):
     if family in name and theme!='Professional':
      candidate=a.assets/f'ShadowRealm-OS-{theme}-{family}.png'
      if candidate.is_file():replacement=candidate.read_bytes()
    # The dedicated monochrome login wallpaper must not retain the old S.
    if 'Login-BlackGrey' in name:replacement=(a.assets/'ShadowRealm-OS-BlackBlue-logo-focused.png').read_bytes()
    if replacement is None and (stem in ('logo','orbital-logo','term','start-here','start-here-symbolic','distributor-logo','shadowrealm-os-logo','shadow-dock-launcher','shadow-menu','shadowrealm-os-release-shadow-menu','shadowrealm-os-app-menu','shadowrealm-os-dock-menu') or stem.startswith('ShadowRealm-OS-Circular-')):
     replacement=logo(data,theme,'Dock-SR' if stem in ('shadow-dock-launcher','shadowrealm-os-dock-menu') else 'SR')
   if data is not None and name.endswith('.png') and replacement is None:
    if stem.startswith(('shadow-','orbital-dock-')):
     replacement=vector_png(old,name,data)
   if replacement is not None:
    data=replacement;changes.append(name)
   if data is not None:m.size=len(data)
   out.addfile(m,io.BytesIO(data) if data is not None else None)
  if filename=='shadowrealm-os-artwork-source.tar.gz':
   for theme in palettes.values():
    extra=a.assets/f'Wordmark-{theme}.png'
    m=tarfile.TarInfo('./usr/share/shadowrealm-os/branding/'+extra.name)
    data=extra.read_bytes();m.size=len(data);m.mode=0o644
    out.addfile(m,io.BytesIO(data))
 temp.replace(f)
(a.assets/'archive-replacements.json').write_text(json.dumps(changes,indent=2))
print('Updated',len(changes),'owned archive branding entries')
