"""Single vector plate master. Native symbols use a gradient; vendor art keeps its colors."""
from pathlib import Path
import base64, re, json, xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image, ImageColor
HERE=Path(__file__).resolve().parent

def valid_color(s):
    return '#%02x%02x%02x'%ImageColor.getrgb(s)[:3]

def art_png(data,crop=True):
    with Image.open(BytesIO(data)) as img:
        img=img.convert('RGBA'); box=img.getchannel('A').getbbox()
        if not box: raise ValueError('transparent artwork')
        img=img.crop(box) if crop else img; img.thumbnail((256,256), Image.Resampling.LANCZOS)
        b=BytesIO();img.save(b,format='PNG');return b.getvalue()

def image_element(data, boxed):
    b64=base64.b64encode(art_png(data,crop=boxed)).decode('ascii'); p=27 if boxed else 0; s=74 if boxed else 128
    return f'<image x="{p}" y="{p}" width="{s}" height="{s}" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{b64}"/>'

def glyph_element(role):
    root=ET.fromstring((HERE/'glyphs'/(role+'.svg')).read_text()); vb=root.attrib['viewBox']; assert vb=='0 0 64 64',vb
    parts=[]
    for child in root:
        for node in child.iter():
            node.tag=node.tag.split('}')[-1]
            for k in ('stroke','fill'):
                if re.fullmatch(r'#[0-9a-fA-F]{3,8}',node.get(k,'')):node.set(k,'url(#ink)')
        parts.append(ET.tostring(child,encoding='unicode'))
    x0,y0,x1,y1=json.loads((HERE/'glyph-bounds.json').read_text())[role]; scale=74/max(x1-x0,y1-y0); x=64-(x0+x1)*scale/2; y=64-(y0+y1)*scale/2
    return f'<g transform="translate({x:.4f} {y:.4f}) scale({scale:.4f})">'+''.join(parts)+'</g>'

PLATE={'dark':('#15232a','#070a10','#07060b','#1b0c21'),
       'light':('#f2f5f3','#ffffff','#ffffff','#e9eeec')}

def icon(mode,role=None,logo=None,game=False):
    a=valid_color(mode['accent']); b=valid_color(mode['secondary']);
    # Professional variants sit on light wallpapers and use a light plate,
    # matching the restyled Professional icon themes.
    p=PLATE['light' if mode.get('unbranded') else 'dark']
    header='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="128" height="128" viewBox="0 0 128 128">'
    if game:return (header+image_element(logo,False)+'</svg>').encode()
    defs=f'''<defs>
      <linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{a}"/><stop offset=".32" stop-color="{a}"/><stop offset=".62" stop-color="{b}"/><stop offset="1" stop-color="{b}"/></linearGradient>
      <linearGradient id="ink" x1="0" y1="0" x2=".85" y2="1"><stop stop-color="{a}"/><stop offset=".38" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
      <linearGradient id="plate" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="{p[0]}"/><stop offset=".33" stop-color="{p[1]}"/><stop offset=".70" stop-color="{p[2]}"/><stop offset="1" stop-color="{p[3]}"/></linearGradient>
      <radialGradient id="top" cx=".05" cy=".03" r=".83"><stop stop-color="{a}" stop-opacity=".95"/><stop offset=".3" stop-color="{a}" stop-opacity=".32"/><stop offset=".7" stop-color="{a}" stop-opacity="0"/></radialGradient>
      <radialGradient id="bottom" cx=".98" cy=".99" r=".78"><stop stop-color="{b}" stop-opacity=".85"/><stop offset=".34" stop-color="{b}" stop-opacity=".25"/><stop offset=".72" stop-color="{b}" stop-opacity="0"/></radialGradient>
      <linearGradient id="shine" x1="0" y1="0" x2=".75" y2="1"><stop stop-color="#fff" stop-opacity=".9"/><stop offset=".23" stop-color="#fff" stop-opacity=".24"/><stop offset=".58" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <clipPath id="shape"><rect x="7" y="7" width="114" height="114" rx="27"/></clipPath>
    </defs>'''
    plate='''<rect x="4" y="4" width="120" height="120" rx="30" fill="none" stroke="url(#rim)" stroke-width="4" opacity=".22"/>
    <rect x="7" y="7" width="114" height="114" rx="27" fill="url(#plate)" stroke="url(#rim)" stroke-width="3.6"/>
    <g clip-path="url(#shape)"><rect x="7" y="7" width="114" height="114" rx="27" fill="url(#top)"/><rect x="7" y="7" width="114" height="114" rx="27" fill="url(#bottom)"/>
    <rect x="11" y="11" width="106" height="106" rx="24" fill="none" stroke="url(#rim)" stroke-width="1.4" opacity=".7"/>
    <path d="M13 37Q12 13 39 12L71 12Q42 17 26 31L13 46Z" fill="url(#shine)" opacity=".55"/>
    <path d="M16 31Q20 13 39 12H69" fill="none" stroke="url(#shine)" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M58 117H92Q117 116 118 90" fill="none" stroke="url(#rim)" stroke-width="2" opacity=".9"/></g>'''
    art=glyph_element(role) if role else image_element(logo,True)
    return (header+defs+plate+art+'</svg>').encode()
