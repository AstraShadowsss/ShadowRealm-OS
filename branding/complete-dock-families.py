#!/usr/bin/python3
"""Complete the shipped dock/glyph families while preserving installed role art."""
from pathlib import Path
from PIL import Image,ImageOps
import tarfile,tempfile,subprocess,json,re,io,argparse,shutil,base64
p=argparse.ArgumentParser();p.add_argument('source',type=Path);base=p.parse_args().source;c=base/'components'
with tempfile.TemporaryDirectory() as td:
 roots={}
 for kind in ['desktop-defaults','artwork']:
  root=Path(td)/kind;root.mkdir();roots[kind]=root
  with tarfile.open(c/f'shadowrealm-os-{kind}-source.tar.gz') as t:t.extractall(root,filter='data')
 desktop=roots['desktop-defaults']/'usr/share/shadowrealm-os/desktop';art=roots['artwork'];modes=json.loads((desktop/'appearance-modes.json').read_text());catalog=json.loads((desktop/'icon-catalog.json').read_text())
 def mono(im):
  im=im.convert('RGBA');g=ImageOps.grayscale(im);return Image.merge('RGBA',(g,g,g,im.getchannel('A')))
 def gray(match):
  v=match.group()[1:];g=round(sum(int(v[i:i+2],16)*w for i,w in zip((0,2,4),(.2126,.7152,.0722))));return '#'+format(g,'02x')*3
 # The retired light palette must not leak white beveled tiles into the new dark style.
 src=roots['desktop-defaults']/'usr/share/icons/ShadowRealm-OS-Neon';dst=roots['desktop-defaults']/'usr/share/icons/ShadowRealm-OS-BlackWhite'
 for f in src.rglob('*.png'):
  target=dst/f.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);mono(Image.open(f)).save(target)
 for f in (art/'usr/share/themes/ShadowRealm-OS-BlackWhite').rglob('*.xpm'):
  f.write_text(re.sub(r'#[0-9a-fA-F]{6}\b',gray,f.read_text()))
 brand={'start-here','start-here-symbolic','distributor-logo','shadowrealm-os-logo','shadow-menu','shadowrealm-os-release-shadow-menu','shadowrealm-os-dock-menu','shadow-dock-launcher'}
 brand_image=Image.open(desktop/'runtime/icons/black-white/orbital-logo.png').convert('RGBA')
 for f in dst.rglob('*.png'):
  if f.stem in brand:brand_image.resize(Image.open(f).size,Image.Resampling.LANCZOS).save(f)
 # Release launcher aliases belong to the desktop package, not artwork.
 for accidental in (art/'usr/share/icons').rglob('shadowrealm-os-release-*.png'):accidental.unlink()
 for mode,m in modes.items():
  runtime=desktop/'runtime/icons'/mode;theme=roots['desktop-defaults']/'usr/share/icons'/m['icons'];accent=m['accent'];secondary=m['secondary']
  if mode=='professional':accent='#9dbbd1';secondary='#b5c9db'
  for role in catalog[mode]:
   vector=runtime/f'shadow-{role}.svg';svg=vector.read_text();at=svg.find('<g fill=');body=svg[at:svg.rfind('</svg>')] if at>=0 else ''
   existing=theme/'48x48/apps'/f'shadowrealm-os-release-orbital-dock-{role}.png'
   if existing.exists():
    # Exact installed PNG takes precedence over the smaller runtime fallback.
    shutil.copyfile(existing,runtime/f'orbital-dock-{role}.png')
   else:
    frame=f'''<defs><linearGradient id="rim" x2="1" y2="1"><stop stop-color="{accent}"/><stop offset=".45" stop-color="#ecfaff"/><stop offset="1" stop-color="{secondary}"/></linearGradient><linearGradient id="plate" x2="0" y2="1"><stop stop-color="#252525"/><stop offset=".45" stop-color="#090909"/><stop offset="1" stop-color="#111111"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="1.2"/></filter></defs><rect x="4" y="4" width="56" height="56" rx="12" fill="none" stroke="url(#rim)" stroke-width="4" opacity=".65" filter="url(#glow)"/><rect x="5" y="5" width="54" height="54" rx="10" fill="url(#plate)" stroke="url(#rim)" stroke-width="2"/><path d="M16 8h31" stroke="#ffffff" stroke-opacity=".32" stroke-width="2"/>'''
    image='<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'+frame+'<g transform="translate(8 8) scale(.75)">'+body+'</g></svg>'
    out=runtime/f'orbital-dock-{role}.svg';out.write_text(image)
    subprocess.run(['rsvg-convert','-w','64','-h','64','-o',str(out.with_suffix('.png')),str(out)],check=True)
    for size in [16,24,32,48,64]:
     target=theme/f'{size}x{size}/apps'/f'shadowrealm-os-release-orbital-dock-{role}.png';target.parent.mkdir(parents=True,exist_ok=True)
     Image.open(out.with_suffix('.png')).resize((size,size),Image.Resampling.LANCZOS).save(target)
   for size in [16,24,32,48,64]:
    target=theme/f'{size}x{size}/status'/f'shadowrealm-os-release-shadow-panel-{role}.png'
    if target.exists():continue
    source=theme/'48x48/apps'/f'shadowrealm-os-release-shadow-panel-{role}.png'
    if not source.exists():source=runtime/f'shadow-panel-{role}.png'
    elif role=='bluetooth':
     shutil.copyfile(source,runtime/f'shadow-panel-{role}.png')
     (runtime/f'shadow-panel-{role}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><image width="24" height="24" href="data:image/png;base64,'+base64.b64encode(source.read_bytes()).decode()+'"/></svg>')
    if source.exists():target.parent.mkdir(parents=True,exist_ok=True);Image.open(source).resize((size,size),Image.Resampling.LANCZOS).save(target)
 for kind,root in roots.items():
  file=c/f'shadowrealm-os-{kind}-source.tar.gz'
  with tarfile.open(str(file)+'.new','w:gz') as t:
   for item in sorted(root.iterdir()):t.add(item,arcname='./'+item.name)
  Path(str(file)+'.new').replace(file)
print('Completed dock families; retained shipped dock PNGs; corrected monochrome tiles and decorations')
