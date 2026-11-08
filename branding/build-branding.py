#!/usr/bin/python3
"""Render the shared SR brand through native SVG palette/composition templates.
Image masters are approved/generated inputs, never regenerated per theme.
"""
from pathlib import Path
import argparse,base64,subprocess,json,hashlib
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
palettes=json.loads((a.source/'palettes.json').read_text())

def uri(name):return 'data:image/png;base64,'+base64.b64encode(((a.source/name) if (a.source/name).is_file() else (a.output/name)).read_bytes()).decode()
def image(name,x,y,w,h):return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="{uri(name)}"/>'
def matrix(cyan,magenta):
 c=[int(cyan[i:i+2],16)/255 for i in (1,3,5)];m=[int(magenta[i:i+2],16)/255 for i in (1,3,5)]
 return ' '.join(' '.join(map(str,[1-c[i],1-m[i],c[i]+m[i]-1,0,0])) for i in range(3))+' 0 0 0 1 0'
def render(name,w,h,content,palette,overlay=''):
 c,m=palettes[palette]
 # The raster wordmark and monogram keep exactly the same geometry across palettes.
 filt='' if palette=='Neon' else f'filter="url(#palette)"'
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><filter id="palette" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="{matrix(c,m)}"/></filter></defs><g {filt}>{content}</g>{overlay}</svg>'
 path=a.output/(name+'.svg');path.write_text(svg)
 subprocess.run(['rsvg-convert','-o',str(a.output/(name+'.png')),str(path)],check=True)
for palette in palettes:
 # Individual icon/terminal/splash assets use alpha, with no opaque black rectangle.
 render('SR-'+palette,512,512,image('sr-logo-neon.png',0,0,512,512),palette)
 tile_bg='#f0efeb' if palette in ('WhiteSilverGold','BlueWhite') else '#10101b'
 tile=f'<rect x="10" y="10" width="492" height="492" rx="85" fill="{tile_bg}" stroke="{palettes[palette][0]}" stroke-width="12"/>'
 render('Dock-SR-'+palette,512,512,'','Neon',f'<image x="38" y="38" width="436" height="436" href="data:image/png;base64,{base64.b64encode((a.output/("SR-"+palette+".png")).read_bytes()).decode()}"/>')
 # Color the wordmark by alpha rather than remapping its blue pixels to a dark hue.
 # Both clips use the same unmodified master: no per-theme font or spacing drift.
 accent=palettes[palette][1]
 colored=' '.join(str(int(accent[i:i+2],16)/255) for i in (1,3,5))
 red,green,blue=colored.split()
 content=f'<defs><filter id="white"><feColorMatrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"/></filter><filter id="accent"><feColorMatrix values="0 0 0 0 {red} 0 0 0 0 {green} 0 0 0 0 {blue} 0 0 0 1 0"/></filter><clipPath id="prefix"><rect width="975" height="180"/></clipPath><clipPath id="os"><rect x="975" width="225" height="180"/></clipPath></defs><g clip-path="url(#prefix)" filter="url(#white)">{image("wordmark.png",0,-105,1200,400)}</g><g clip-path="url(#os)" filter="url(#accent)">{image("wordmark.png",0,-105,1200,400)}</g>'
 render('Wordmark-'+palette,1200,180,'','Neon',content)
 if palette=='Professional':continue
 for family,bg in [('logo-focused','focused'),('circuit-corridor','corridor'),('full-artwork','artwork'),('seated-city','seated')]:
  body=image('background-'+bg+'.png',0,0,1920,1080)
  if family in ('logo-focused','circuit-corridor'):
   body+=image('sr-logo-neon.png',645,155,630,630)
   overlay=image('Wordmark-'+palette+'.png',525,750,870,131)
  elif family=='full-artwork':
   overlay=image('Wordmark-'+palette+'.png',430,645,1060,159)
  else:overlay=''
  render('ShadowRealm-OS-'+palette+'-'+family,1920,1080,body,palette,overlay)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.output.glob('*.png'))}
(a.output/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2))
print('Rendered',len(manifest),'shared-geometry branding assets')
