#!/usr/bin/python3
"""Extend the shipped role geometry and migrate BlueWhite to monochrome.
Existing role files remain byte-identical in the seven retained palettes.
"""
from pathlib import Path
import argparse,tarfile,tempfile,subprocess,json,re,io,hashlib
from PIL import Image,ImageOps
p=argparse.ArgumentParser();p.add_argument('components',type=Path);a=p.parse_args()
# Common desktop, privacy, connectivity, device and session roles. Vendor apps
# are intentionally not aliased: they keep the icon shipped by their publisher.
shapes={
'vpn':'<path d="M14 15l18-7 18 7v16c0 12-18 23-18 23S14 43 14 31z"/><rect x="25" y="27" width="14" height="13" rx="2"/><path d="M28 27v-5a4 4 0 018 0v5"/>',
'firewall':'<path d="M12 17h40v32H12z M12 28h40 M12 39h40 M25 17v11 M39 28v11 M25 39v10"/>',
'dns':'<circle cx="32" cy="32" r="21"/><ellipse cx="32" cy="32" rx="9" ry="21"/><path d="M12 25h40 M12 39h40"/>',
'airplane':'<path d="M30 10h4l3 18 17 10v5l-18-5-1 12 6 4H23l6-4-1-12-18 5v-5l17-10z"/>',
'ethernet':'<rect x="14" y="20" width="36" height="26" rx="2"/><path d="M21 20v-6 M28 20v-6 M36 20v-6 M43 20v-6 M24 46v8h16v-8"/>',
'wifi-off':'<path d="M9 24c12-11 34-11 46 0 M18 34c8-7 20-7 28 0 M27 44c3-3 7-3 10 0 M11 10l42 44"/>',
'bluetooth-off':'<path d="M30 9l15 12-24 22 9 10V9l15 32-15 12 M10 10l44 44"/>',
'audio-muted':'<path d="M11 26h9l12-10v32L20 38h-9z M42 25l12 14 M54 25L42 39"/>',
'microphone':'<rect x="25" y="10" width="14" height="29" rx="7"/><path d="M18 29v4a14 14 0 0028 0v-4 M32 47v9 M23 56h18"/>',
'headphones':'<path d="M12 36v-5a20 20 0 0140 0v5"/><rect x="10" y="31" width="11" height="20" rx="4"/><rect x="43" y="31" width="11" height="20" rx="4"/>',
'camera':'<path d="M10 21h12l4-7h12l4 7h12v31H10z"/><circle cx="32" cy="36" r="10"/>',
'printer':'<path d="M20 24V10h24v14 M20 45H10V24h44v21H44 M20 37h24v18H20z M45 30h2"/>',
'disk':'<rect x="12" y="14" width="40" height="37" rx="4"/><path d="M12 39h40 M20 45h3 M29 45h3"/>',
'usb':'<path d="M32 54V10l-5 7h10l-5-7 M32 40l-12-9V20 M32 32l13-9v-9"/><circle cx="20" cy="17" r="3"/><rect x="42" y="9" width="6" height="6"/>',
'keyboard-layout':'<rect x="8" y="17" width="48" height="31" rx="4"/><path d="M16 25h4m5 0h4m5 0h4m5 0h5 M16 33h4m5 0h4m5 0h4m5 0h5 M21 41h22"/>',
'battery':'<rect x="9" y="20" width="43" height="25" rx="3"/><path d="M52 28h4v9h-4 M16 27v11 M23 27v11 M30 27v11 M37 27v11"/>',
'battery-charging':'<rect x="8" y="20" width="45" height="26" rx="3"/><path d="M53 29h4v8h-4 M35 10L23 34h12l-7 20"/>',
'battery-low':'<rect x="9" y="20" width="43" height="25" rx="3"/><path d="M52 28h4v9h-4 M16 27v11"/>',
'users':'<circle cx="26" cy="21" r="9"/><path d="M9 53v-9a17 17 0 0134 0v9 M43 13a8 8 0 010 16 M48 37a14 14 0 017 12v4"/>',
'accessibility':'<circle cx="32" cy="12" r="5"/><path d="M12 25h40 M32 19v19 M32 38L20 55 M32 38l12 17"/>',
'passwords':'<circle cx="22" cy="25" r="12"/><path d="M31 34l19 19 M41 44l6-6 M46 49l6-6"/>',
'encryption':'<rect x="15" y="27" width="34" height="28" rx="4"/><path d="M22 27V18a10 10 0 0120 0v9 M32 38v7"/>',
'backup':'<path d="M12 28a21 21 0 112 19 M12 12v16h16"/><path d="M32 20v14l9 6"/>',
'restore':'<path d="M12 28a21 21 0 112 19 M12 12v16h16 M24 35h17 M24 35l8-8 M24 35l8 8"/>',
'certificate':'<path d="M15 8h34v36H15z M23 17h18 M23 25h18"/><circle cx="32" cy="39" r="9"/><path d="M25 45l-3 12 10-5 10 5-3-12"/>',
'notifications':'<path d="M16 43V28a16 16 0 0132 0v15l6 7H10z M26 55h12"/>',
'help':'<circle cx="32" cy="32" r="22"/><path d="M24 24a8 8 0 1112 7l-4 3v5 M32 46h.1"/>',
'error':'<path d="M32 9L57 54H7z M32 24v13 M32 45h.1"/>',
'check':'<circle cx="32" cy="32" r="22"/><path d="M20 32l8 9 17-19"/>',
'add':'<path d="M32 12v40 M12 32h40"/>',
'remove':'<path d="M12 32h40"/>',
'close':'<path d="M16 16l32 32 M48 16L16 48"/>',
'refresh':'<path d="M12 28a21 21 0 0140-7 M52 10v14H38 M52 37a21 21 0 01-40 7 M12 54V40h14"/>',
'copy':'<rect x="22" y="22" width="31" height="32" rx="3"/><path d="M42 22V10H10v32h12"/>',
'paste':'<rect x="14" y="16" width="36" height="39" rx="3"/><rect x="24" y="9" width="16" height="13" rx="2"/>',
'cut':'<circle cx="17" cy="46" r="8"/><circle cx="47" cy="46" r="8"/><path d="M21 39L48 10 M43 39L16 10"/>',
'save':'<path d="M11 10h35l8 8v36H11z M20 10v17h23V10 M21 54V36h24v18"/>',
'folder-new':'<path d="M8 19h19l6 7h23v27H8z M39 32v15 M32 39h15"/>',
'file-new':'<path d="M15 9h24l12 13v33H15z M39 9v13h12 M32 31v15 M25 38h14"/>',
'launcher':'<path d="M32 10L10 52l22-11 22 11z M32 10v31"/>',
'suspend':'<path d="M43 10a23 23 0 10 11 34A21 21 0 0143 10z"/>',
'restart':'<path d="M51 24a22 22 0 10 1 17 M51 10v16H35"/>',
'shutdown':'<path d="M32 8v24 M20 15a22 22 0 1024 0"/>',
'logout':'<path d="M28 10H11v44h17 M23 32h31 M43 21l11 11-11 11"/>',
'login':'<path d="M36 10h17v44H36 M10 32h31 M30 21l11 11-11 11"/>',
'workspace':'<rect x="9" y="11" width="46" height="42" rx="4"/><path d="M32 11v42 M9 32h46"/>',
'privacy':'<path d="M8 32s10-17 24-17 24 17 24 17-10 17-24 17S8 32 8 32z M10 9l44 46"/><circle cx="32" cy="32" r="8"/>',
'location':'<path d="M32 56S14 37 14 25a18 18 0 0136 0c0 12-18 31-18 31z"/><circle cx="32" cy="25" r="6"/>',
'power-profile':'<path d="M35 8L15 35h15l-3 21 22-29H34z"/>',
'storage':'<rect x="10" y="10" width="44" height="44" rx="4"/><path d="M10 25h44 M10 40h44 M18 18h2 M18 33h2 M18 47h2"/>',
'processes':'<path d="M10 12v40h45 M15 40l9-12 10 7 15-18"/>',
'alarm':'<circle cx="32" cy="34" r="19"/><path d="M32 22v13l9 6 M10 17l10-9 M44 8l10 9 M17 50l-5 7 M47 50l5 7"/>',
'timer':'<circle cx="32" cy="36" r="19"/><path d="M25 7h14 M32 7v10 M32 25v12l9 5 M47 18l5-5"/>',
}
rename=lambda s:s.replace('BlueWhite','BlackWhite').replace('blue-white','black-white').replace('Blue & White','Black & White')
all_roots=[]
with tempfile.TemporaryDirectory() as td:
 for fn in ['shadowrealm-os-artwork-source.tar.gz','shadowrealm-os-desktop-defaults-source.tar.gz','shadowrealm-os-terminal-assets.tar.gz']:
  root=Path(td)/fn.split('-source')[0];root.mkdir();all_roots.append((fn,root))
  with tarfile.open(a.components/fn) as t:t.extractall(root,filter='data')
  # Rename children before parents, preserving every unrelated file.
  for f in sorted(root.rglob('*'),key=lambda f:len(f.parts),reverse=True):
   if f.is_file():
    bw='BlueWhite' in str(f) or 'blue-white' in str(f)
    if bw and f.suffix.lower()=='.png':
     im=Image.open(f).convert('RGBA');gray=ImageOps.grayscale(im);out=Image.merge('RGBA',(gray,gray,gray,im.getchannel('A')));out.save(f)
    elif f.suffix in ('.svg','.css','.theme','.json','.xml','.rc','.conf') or f.name in ('themerc','gtkrc'):
     try:s=f.read_text()
     except UnicodeError:continue
     s=rename(s)
     if bw:
      def color(m):
       v=m.group()[1:];v=v if len(v)==6 else ''.join(c*2 for c in v);rgb=[int(v[i:i+2],16) for i in (0,2,4)];g=round(sum(c*w for c,w in zip(rgb,(.2126,.7152,.0722))));return '#'+format(g,'02x')*3
      s=re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',color,s)
     f.write_text(s)
   n=rename(f.name)
   if n!=f.name:f.rename(f.with_name(n))
 desktop=all_roots[1][1]/'usr/share/shadowrealm-os/desktop';mfile=desktop/'appearance-modes.json';modes=json.loads(mfile.read_text());m=modes['black-white'];m.update(accent='#eeeeee',secondary='#a8a8a8',background='#101010',foreground='#f5f5f5',light=False);mfile.write_text(json.dumps(modes,indent=2)+'\n')
 # Black/White GTK uses the shipped dark Neon geometry and behavior, with
 # neutral colors; no light GTK CSS accidentally left below a dark title bar.
 artwork=all_roots[0][1]
 src=artwork/'usr/share/themes/ShadowRealm-OS-Neon';dst=artwork/'usr/share/themes/ShadowRealm-OS-BlackWhite'
 import shutil
 shutil.rmtree(dst);shutil.copytree(src,dst)
 for f in dst.rglob('*'):
  if f.is_file() and f.suffix in ('.css','.svg','.theme','.xpm') or f.is_file() and f.name in ('themerc','gtkrc'):
   s=f.read_text().replace('Neon','BlackWhite')
   def gray(m):
    v=m.group()[1:];v=v if len(v)==6 else ''.join(c*2 for c in v);rgb=[int(v[i:i+2],16) for i in (0,2,4)];g=round(sum(c*w for c,w in zip(rgb,(.2126,.7152,.0722))));return '#'+format(g,'02x')*3
   f.write_text(re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',gray,s))
 # Monochrome is a dark style: keep the dark tile geometry from Neon,
 # rather than leaving white tiles from the retired light palette.
 runtime=desktop/'runtime/icons'
 bw=runtime/'black-white'
 for original in (runtime/'neon').iterdir():
  if not original.is_file():continue
  target=bw/original.name
  if original.suffix=='.png':
   im=Image.open(original).convert('RGBA');gray=ImageOps.grayscale(im)
   Image.merge('RGBA',(gray,gray,gray,im.getchannel('A'))).save(target)
  elif original.suffix=='.svg':
   text=original.read_text()
   def neutral(match):
    value=match.group()[1:];value=value if len(value)==6 else ''.join(c*2 for c in value)
    rgb=[int(value[i:i+2],16) for i in (0,2,4)];g=round(sum(c*w for c,w in zip(rgb,(.2126,.7152,.0722))))
    return '#'+format(g,'02x')*3
   target.write_text(re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',neutral,text))
 # Existing PNG/SVG roles are never overwritten. Extend their same 64px tile.
 catalog={}
 for mode,record in modes.items():
  folder=desktop/'runtime/icons'/mode;folder.mkdir(parents=True,exist_ok=True)
  example=folder/'shadow-network.svg'
  template=example.read_text() if example.exists() else (desktop/'runtime/icons/neon/shadow-network.svg').read_text()
  tile=template[:template.index('<g fill=')]
  accent=record['accent'];match=re.search(r'<g fill="none" stroke="([^"]+)"',template);stroke=match.group(1) if match else accent
  for role,glyph in shapes.items():
   file=folder/f'shadow-{role}.svg'
   if file.exists():continue
   body=f'<g fill="none" stroke="{stroke}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">{glyph}</g>'
   file.write_text(tile+body+'</svg>')
   subprocess.run(['rsvg-convert','-w','64','-h','64','-o',str(file.with_suffix('.png')),str(file)],check=True)
   # New dock icons use precisely the same existing dock tile language.
   shutil.copyfile(file.with_suffix('.png'),folder/f'orbital-dock-{role}.png')
   panel=folder/f'shadow-panel-{role}.svg'
   if not panel.exists():panel.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 64 64">'+body+'</svg>')
   subprocess.run(['rsvg-convert','-w','24','-h','24','-o',str(panel.with_suffix('.png')),str(panel)],check=True)
  catalog[mode]=sorted({f.stem.removeprefix('shadow-') for f in folder.glob('shadow-*.svg') if not f.stem.startswith('shadow-panel-')})
  theme=artwork/'usr/share/icons'/record['icons']
  for role in catalog[mode]:
   vector=folder/f'shadow-{role}.svg'
   if not vector.exists():continue
   for size in (16,24,32,48,64):
    target=theme/f'{size}x{size}/apps'/f'shadowrealm-os-system-{role}.png';target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['rsvg-convert','-w',str(size),'-h',str(size),'-o',str(target),str(vector)],check=True)
  # Scalable vectors provide crisp rendering beyond the fixed raster sizes.
  scalable=theme/'scalable/apps';scalable.mkdir(parents=True,exist_ok=True)
  for role in catalog[mode]:shutil.copyfile(folder/f'shadow-{role}.svg',scalable/f'shadowrealm-os-system-{role}.svg')
  index=theme/'index.theme';s=index.read_text();s=re.sub(r'^Directories=(.*)$',lambda m:'Directories='+','.join(dict.fromkeys(m.group(1).split(',')+['scalable/apps','64x64/apps'])),s,flags=re.M)
  
  if '[scalable/apps]' not in s:s+='\n[scalable/apps]\nSize=48\nMinSize=16\nMaxSize=512\nType=Scalable\nContext=Applications\n'
  if '[64x64/apps]' not in s:s+='\n[64x64/apps]\nSize=64\nType=Fixed\nContext=Applications\n'
  index.write_text(s)
 (desktop/'icon-catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
 for fn,root in all_roots:
  temporary=a.components/(fn+'.new')
  with tarfile.open(temporary,'w:gz') as t:
   for f in sorted(root.iterdir()):t.add(f,arcname='./'+f.name)
  temporary.replace(a.components/fn)
print(json.dumps({k:len(v) for k,v in catalog.items()}))
