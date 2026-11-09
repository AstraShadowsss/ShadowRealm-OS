#!/usr/bin/python3
"""Render one cleaned walking-figure plate with the exact approved SR insert."""
from pathlib import Path
import argparse,base64,json,subprocess
p=argparse.ArgumentParser();p.add_argument('branding',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
def uri(file):return 'data:image/png;base64,'+base64.b64encode(file.read_bytes()).decode()
def matrix(cyan,magenta):
 c=[int(cyan[i:i+2],16)/255 for i in (1,3,5)];m=[int(magenta[i:i+2],16)/255 for i in (1,3,5)]
 return ' '.join(' '.join(map(str,[1-c[i],1-m[i],c[i]+m[i]-1,0,0])) for i in range(3))+' 0 0 0 1 0'
for theme,(c,m) in json.loads((a.branding/'palettes.json').read_text()).items():
 body='<image width="1672" height="941" href="'+uri(a.branding/'background-walker.png')+'"/>'
 if theme!='Professional':body+='<g transform="matrix(.94 -.04 .08 1 489 438)"><image width="43.5" height="43.5" href="'+uri(a.branding/'sr-logo-neon.png')+'"/></g>'
 filt='' if theme=='Neon' else ' filter="url(#palette)"'
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="1672" height="941" viewBox="0 0 1672 941"><defs><filter id="palette" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'+matrix(c,m)+'"/></filter></defs><g'+filt+'>'+body+'</g></svg>'
 name='ShadowRealm-OS-'+theme+'-Circuit-Walker';source=a.output/(name+'.svg');source.write_text(svg)
 subprocess.run(['rsvg-convert','-o',str(a.output/(name+'.png')),str(source)],check=True)
print('Rendered eight walking-figure variants; exact SR geometry on the seven branded palettes')
