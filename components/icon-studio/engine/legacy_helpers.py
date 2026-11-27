#!/usr/bin/python3
"""ShadowRealm icon integration development preview; no package-owned files changed."""
from pathlib import Path
from io import BytesIO
import os, re, json, hashlib, shutil, subprocess, time, tempfile, base64, shlex
from collections import Counter, defaultdict
from PIL import Image, ImageDraw, ImageChops, ImageOps, ImageColor, ImageFilter
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gio, GLib, GdkPixbuf
H=Path.home(); B=H/'.local/share/shadow-link'; U=H/'.local/share/icons'; S=Path('/usr/share/icons'); A=H/'.local/share/applications'; HERE=Path(__file__).resolve().parent
BACK=H/'shadowrealm-checkpoints'/('unified-icon-source-'+time.strftime('%Y%m%d-%H%M%S'))
SIZE=(16,24,32,48,64); RES=192; changes=0
NAMES={
'Terminal':'terminal','Shadow Calendar':'calendar','Shadow Calculator':'calculator','Shadow Clock':'clock','Shadow Widgets':'widgets','Shadow Network':'network','Shadow Audio':'audio','Shadow Bluetooth':'bluetooth','Shadow Media':'media','Files':'files','Shadow Control Center':'control-center','Shadow Shield':'shield','Text Editor':'editor','Screenshot':'screenshot','Trash':'trash','Appearance':'theme','Software & Updates':'updates','Choose Default Browser':'browser-alt','Task manager':'task-manager','Web browser':'browser','Browser':'browser','Local Search':'search','Shadow Messenger':'email','Shadow Link':'menu'}
ROLE_BY_NAME={k.casefold():v for k,v in NAMES.items()}
CORE=('browser','terminal','files','control-center','shield','task-manager')
ROLES=sorted(set(NAMES.values())|set(CORE))
BUILTINS={'folder-home':('folder-home','user-home','go-home','gnome-fs-home'),'user-trash':('user-trash','gnome-fs-trash-empty','trashcan_empty'),'user-trash-full':('user-trash-full','gnome-fs-trash-full','trashcan_full'),'drive-harddisk-system':('drive-harddisk-system','drive-harddisk','filesystem-root','computer','system','my-computer'),'computer':()}
ROLE_ALIASES={'terminal':('shadow-terminal','shadowrealm-os-terminal','shadowos-terminal','utilities-terminal'),'files':('shadow-files','system-file-manager'),'browser':('shadow-browser','web-browser'),'control-center':('shadow-control-center',),'shield':('shadow-shield',),'task-manager':('shadow-task-manager',),'theme':('shadow-appearance','shadowrealm-os-app-appearance','shadowrealm-os-dock-appearance'),'updates':('shadow-software','shadowrealm-os-app-software','shadowrealm-os-dock-software','orbital-dock-software'),'search':('shadow-search','system-search'),'email':('orbital-dock-email','shadow-email','shadowrealm-os-release-orbital-dock-email','shadowrealm-os-app-email','shadow-messenger','shadow-messenger-app')}

def run(args,**kw):return subprocess.run(args,check=True,**kw)
def load(path):
 with Image.open(path) as im:return im.convert('RGBA')
def png(im):
 o=BytesIO();im.save(o,format='PNG');return o.getvalue()
def square(im,n):
 im=im.copy();im.thumbnail((n,n),Image.Resampling.LANCZOS)
 # Upscale masters consistently when necessary, without changing aspect ratio.
 if max(im.size)<n:
  f=n/max(im.size);im=im.resize((max(1,round(im.width*f)),max(1,round(im.height*f))),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(n,n));canvas.alpha_composite(im,((n-im.width)//2,(n-im.height)//2));return canvas

def save(path,data,mode=None):
 global changes
 path=Path(path)
 if not path.parent.resolve().is_relative_to(H.resolve()):raise RuntimeError('Refusing path outside account: '+str(path))
 if path.is_file() and not path.is_symlink() and path.read_bytes()==data:return
 rel=path.relative_to(H);dest=BACK/'original'/rel
 if os.path.lexists(path):
  dest.parent.mkdir(parents=True,exist_ok=True)
  if not os.path.lexists(dest):
   if path.is_symlink():dest.symlink_to(os.readlink(path))
   else:shutil.copy2(path,dest)
 else:
  with (BACK/'new-files.txt').open('a') as f:f.write(str(rel)+'\n')
 path.parent.mkdir(parents=True,exist_ok=True)
 oldmode=(path.stat().st_mode&0o777) if path.is_file() else 0o644
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.sr-icon-')
 try:
  with os.fdopen(fd,'wb') as f:f.write(data)
  os.chmod(tmp,mode if mode is not None else oldmode);os.replace(tmp,path)
 finally:Path(tmp).unlink(missing_ok=True)
 changes+=1

def colors(m):
 return [ImageColor.getrgb(m[k]) for k in ('accent','secondary','foreground','background')]
def mix(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))
def plate(logo,m):
 n=RES;ac,se,fg,bg=colors(m);im=Image.new('RGBA',(n,n));mask=Image.new('L',(n,n));d=ImageDraw.Draw(mask);d.rounded_rectangle((8,8,n-9,n-9),radius=39,fill=255)
 rim=Image.new('RGBA',(n,n));p=rim.load()
 for y in range(n):
  for x in range(n):
   t=(x+y)/(2*(n-1));rgb=mix(ac,fg,t*2) if t<.5 else mix(fg,se,(t-.5)*2);p[x,y]=(*rgb,255)
 glow=Image.new('RGBA',(n,n));glow.paste(rim,(0,0),mask.filter(ImageFilter.GaussianBlur(5)));im.alpha_composite(glow)
 rim.putalpha(mask);d=ImageDraw.Draw(rim);d.rounded_rectangle((15,15,n-16,n-16),radius=33,fill=(*mix(bg,(5,7,13),.40),255));im.alpha_composite(rim)
 logo=logo.convert('RGBA');bbox=logo.getchannel('A').getbbox()
 if bbox:logo=logo.crop(bbox)
 logo=square(logo,122);alpha=logo.getchannel('A');lum=ImageOps.grayscale(logo)
 # Recolor the actual logo silhouette and its internal tonal detail, not a category glyph.
 ink=ImageOps.colorize(lum,black=mix(ac,(0,0,0),.42),mid=ac,white=fg).convert('RGBA');ink.putalpha(alpha)
 im.alpha_composite(ink,((n-122)//2,(n-122)//2));return im

def chamfer(im):
 # The supplied 48px desktop assets have an octagonal border but opaque exterior.
 # Clip only the exterior geometry, never flood-fill interior dark pixels.
 im=im.convert('RGBA');w,h=im.size;mask=Image.new('L',(w*4,h*4));d=ImageDraw.Draw(mask)
 pts=[(.015,.15),(.15,.015),(.85,.015),(.985,.15),(.985,.85),(.85,.985),(.15,.985),(.015,.85)]
 d.polygon([(round(x*(w*4-1)),round(y*(h*4-1))) for x,y in pts],fill=255)
 im.putalpha(ImageChops.multiply(im.getchannel('A'),mask.resize(im.size,Image.Resampling.LANCZOS)));return im

def is_chamfered(im):
 # These are the known original black-backed desktop assets, not arbitrary app art.
 w,h=im.size;return all(im.getpixel((x,y))[3]>150 for x,y in [(2,2),(w-3,2),(2,h-3),(w-3,h-3)])

def write_alias(root,name,im):
 if not re.fullmatch(r'[A-Za-z0-9_.+-]+',name):return
 variants={n:png(square(im,n)) for n in SIZE};raster=png(square(im,128));encoded=base64.b64encode(raster).decode('ascii')
 svg=('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="128" height="128" viewBox="0 0 128 128"><image width="128" height="128" xlink:href="data:image/png;base64,'+encoded+'"/></svg>').encode()
 for n in SIZE:save(root/f'{n}x{n}/apps'/f'{name}.png',variants[n])
 save(root/'scalable/apps'/f'{name}.svg',svg)
 # Replace alternate contexts/resolutions too, so Gtk never selects an older design.
 for p in list(root.glob('*/'+name+'.png'))+list(root.glob('*/*/'+name+'.png'))+list(root.glob('*/*/'+name+'.svg')):
  if p.suffix=='.svg':save(p,svg)
  else:
   m=re.search(r'/([0-9]+)x[0-9]+/',str(p));n=int(m[1]) if m else 48
   save(p,variants.get(n) or png(square(im,n)))

def fields(text):
 main=text.split('[Desktop Entry]',1)
 if len(main)!=2:return {}
 body=re.split(r'(?m)^\[',main[1],maxsplit=1)[0]
 return dict(re.findall(r'(?m)^([A-Za-z0-9-]+)=(.*)$',body))
def set_icon(text,key):
 a=text.index('[Desktop Entry]')+len('[Desktop Entry]');rest=text[a:];m=re.search(r'(?m)^\[',rest);i=m.start() if m else len(rest);head,tail=rest[:i],rest[i:]
 head=re.sub(r'(?m)^X-ShadowRealm-OS-OriginalIcon=.*\n?','',head)
 if re.search(r'(?m)^Icon=',head):head=re.sub(r'(?m)^Icon=.*$',lambda _: 'Icon='+key,head,count=1)
 else:head='\nIcon='+key+head
 return text[:a]+head+tail

def role_of(f,owned=False):
 name=f.get('Name','').casefold();cmd=f.get('Exec','').lower();first=''
 try:first=Path(shlex.split(cmd)[0]).name
 except (IndexError,ValueError):pass
 if first in ('shadow-terminal','shadowrealm-os-terminal','shadowos-terminal'):return 'terminal'
 if first=='shadowrealm-os-desktop':
  a=cmd.split();r=a[1] if len(a)>1 else ''
  if r in ROLES:return r
  if r in ('software','appearance','search'):return {'software':'updates','appearance':'theme','search':'search'}[r]
 if first=='shadow-link':
  for flag,r in {'--control-center':'control-center','--shield':'shield','--network':'network','--audio':'audio','--bluetooth':'bluetooth','--widget-settings':'widgets','--calendar':'calendar','--clock':'clock','--calculator':'calculator'}.items():
   if flag in cmd.split():return r
 if first in ('shadow-appearance','shadow-software','shadow-browser','shadow-files','shadow-messenger','shadow-screenshot'):
  return {'shadow-appearance':'theme','shadow-software':'updates','shadow-browser':'browser-alt' if '--settings' in cmd else 'browser','shadow-files':'files','shadow-messenger':'email','shadow-screenshot':'screenshot'}[first]
 if owned:return ROLE_BY_NAME.get(name)
 return None

def appkey(id):return 'sr-unified-'+hashlib.sha256(id.encode()).hexdigest()[:20]

def native_image(icon):
 if not icon:return None
 if icon.startswith('/'):
  try:return load(icon) if icon.lower().endswith('.png') else piximage(GdkPixbuf.Pixbuf.new_from_file_at_scale(icon,128,128,True))
  except Exception:return None
 try:
  info=native.lookup_icon(icon,128,0)
  if info:return piximage(info.load_icon())
 except Exception:pass
 # Some native app icons are installed directly in pixmaps.
 for ext in ('.png','.svg','.xpm'):
  p=Path('/usr/share/pixmaps')/(icon+ext)
  if p.is_file():
   try:return piximage(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p),128,128,True))
   except Exception:pass
 return None

def piximage(p):return Image.open(BytesIO(bytes(p.save_to_bufferv('png',[],[])[1]))).convert('RGBA')

def main():
 global native
 # Complete preflight and compilation before modifying account files.
 modefile=B/'appearance-modes.json';modes=json.loads(modefile.read_text());assert len(modes)==12, f'Expected 12 palettes, found {len(modes)}'
 globe=S/'ShadowRealm-OS-Neon/48x48/apps/shadowrealm-os-release-orbital-dock-browser.png'
 assert hashlib.sha256(globe.read_bytes()).hexdigest()=='ac396d9dbc75af4772354934d21948ee26713f0e1f93b18351072d0e528e597c','Original globe source mismatch'
 for m in modes.values():
  assert (U/m['icons']/'index.theme').is_file(),m['icons'];colors(m)
 for name in ('shadow-link','shadow-appearance-apply','shadow_whole_theme.py','shadow_icon_style.py'):
  assert (B/'bin'/name).is_file(),name
 flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','gio-unix-2.0'],text=True))
 with tempfile.TemporaryDirectory() as td:
  compiled=Path(td)/'shadow-link-unified-menu'
  print('Compiling actual Shadow Menu source...',flush=True)
  run(['cc','-O2',str(HERE/'native/shadow-link-dock.c'),'-o',str(compiled),*flags,'-lm'])
  binary=compiled.read_bytes()
 # Use original native artwork only, not the previously overwritten aliases.
 native=Gtk.IconTheme.new();native.set_custom_theme('Adwaita');native.set_search_path(['/usr/share/icons','/usr/local/share/icons',str(H/'.local/share/flatpak/exports/share/icons'),'/var/lib/flatpak/exports/share/icons','/usr/share/pixmaps'])
 os.environ['XDG_DATA_DIRS']=str(B/'share')+':'+str(H/'.local/share/flatpak/exports/share')+':/var/lib/flatpak/exports/share:'+os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
 system_dirs=[B/'share/applications',Path('/usr/local/share/applications'),Path('/usr/share/applications'),H/'.local/share/flatpak/exports/share/applications',Path('/var/lib/flatpak/exports/share/applications')]
 original={}
 for directory in system_dirs:
  if directory.is_dir():
   for p in directory.rglob('*.desktop'):original.setdefault(str(p.relative_to(directory)).replace('/','-'),p)
 apps={};missing=[];byexec={};byname=defaultdict(set)
 os.environ['PATH']=str(B/'bin')+':'+os.environ.get('PATH','/usr/bin:/bin')
 for app in Gio.AppInfo.get_all():
  if not app.should_show() or not isinstance(app,Gio.DesktopAppInfo):continue
  id=app.get_id();filename=app.get_filename()
  if not id or not filename or '/' in id:continue
  p=Path(filename);text=p.read_text(encoding='utf-8',errors='replace');f=fields(text);raw=fields(original[id].read_text(encoding='utf-8',errors='replace')) if id in original else f
  owned=id.startswith(('org.shadowrealm_os.','shadowrealm-os-'))
  role=role_of(f,owned) or role_of(raw,owned)
  if role:key='orbital-dock-'+role;im=None
  else:
   key=appkey(id);im=native_image(raw.get('Icon',''))
   if im is None:
    missing.append((id,raw.get('Icon','')));continue
  apps[id]=(p,text,key,im,raw.get('Icon',''));byexec[f.get('Exec','')]=key;byname[f.get('Name','').casefold()].add(key)
 print('Applications with distinct native artwork:',sum(a[3] is not None for a in apps.values()),flush=True)
 print('Missing native artwork:',len(missing),flush=True)
 # Preflight core original role files in every palette.
 for m in modes.values():
  for r in CORE:assert (S/m['icons']/'48x48/apps'/f'shadowrealm-os-release-orbital-dock-{r}.png').is_file(),(m['icons'],r)
 BACK.mkdir(parents=True,exist_ok=False);print('Backup:',BACK,flush=True)
 for mid,m in modes.items():
  t=m['icons'];root=U/t;sysapps=S/t/'48x48/apps';palette=B/'icons'/mid
  # Restore clean role masters. Keep the verified six artworks exact at 48px.
  for role in ROLES:
   candidates=[sysapps/f'shadowrealm-os-release-orbital-dock-{role}.png',sysapps/f'shadowrealm-os-dock-{role}.png',sysapps/f'shadowrealm-os-app-{role}.png']
   if role=='menu':candidates.insert(0,sysapps/'shadowrealm-os-release-shadow-menu.png')
   if role=='messenger':candidates += [sysapps/'shadowrealm-os-release-orbital-dock-email.png']
   candidates.append(HERE/'dock-originals'/t/({'menu':'app-menu','messenger':'email'}.get(role,role)+'.png'))
   source=next((p for p in candidates if p.is_file()),None)
   if source is None:
    # Keep a theme-appropriate distinct standard icon for a missing built-in role.
    native_names={'updates':'system-software-update','theme':'preferences-desktop-theme','menu':'view-app-grid','messenger':'internet-chat'}
    art=native_image(native_names.get(role,role))
    if art is None:print('MISSING_ROLE',t,role,flush=True);continue
    im=plate(art,m)
   else:im=load(source)
   if role not in CORE and is_chamfered(im):im=chamfer(im)
   aliases={f'orbital-dock-{role}',f'shadowrealm-os-release-orbital-dock-{role}',f'shadowrealm-os-app-{role}',f'shadowrealm-os-dock-{role}',*ROLE_ALIASES.get(role,())}
   for alias in aliases:write_alias(root,alias,im)
   for alias in [f'orbital-dock-{role}',f'shadow-{role}']:
    save(palette/f'{alias}.png',source.read_bytes() if role in CORE and source and source.suffix=='.png' else png(square(im,64)))
  # Known desktop built-ins: use original archive masters, clip octagonal exteriors.
  for name,aliases in BUILTINS.items():
   if not aliases:continue
   src=HERE/'desktop-originals'/t/(name+'.png')
   if not src.is_file():continue
   im=load(src)
   if is_chamfered(im):im=chamfer(im)
   elif t.startswith('ShadowRealm-OS-Professional'):
    # The archived professional desktop assets are neutral glyphs. Retain their shape.
    pass
   for alias in aliases:write_alias(root,alias,im)
  # Distinct vendor icons: canonical IDs plus unique native aliases (not generic category names).
  aliases=Counter(a[4] for a in apps.values() if a[3] is not None)
  for id,(p,text,key,art,oldicon) in apps.items():
   if art is None:continue
   im=plate(art,m);write_alias(root,key,im)
   if aliases[oldicon]==1 and re.fullmatch(r'[A-Za-z0-9_.+-]+',oldicon) and oldicon not in {x for group in ROLE_ALIASES.values() for x in group} and oldicon not in {x for group in BUILTINS.values() for x in group} and not oldicon.startswith(('shadow','orbital-dock-','application-','preferences-','system-','folder-','utilities-')):write_alias(root,oldicon,im)
  run(['gtk-update-icon-cache','-f','-t',str(root)],stdout=subprocess.DEVNULL)
  print('THEME_READY',t,flush=True)
 # Use same canonical icon names for effective menu entries, pinned and desktop launchers.
 for id,(p,text,key,art,oldicon) in apps.items():
  target=A/id
  # Only modify the Icon entry; preserve commands, actions, visibility and other metadata.
  save(target,set_icon(text,key).encode())
 for root in (H/'.config/xfce4/panel',H/'Desktop',H/'.cache/shadowrealm-os/launchers'):
  if not root.is_dir():continue
  for p in root.rglob('*.desktop'):
   text=p.read_text(encoding='utf-8',errors='replace');f=fields(text)
   if not f:continue
   r=role_of(f, f.get('Name','').startswith('Shadow') or f.get('Name','').casefold() in ROLE_BY_NAME)
   key='orbital-dock-'+r if r else byexec.get(f.get('Exec',''))
   if not key:
    keys=byname.get(f.get('Name','').casefold(),set());key=next(iter(keys)) if len(keys)==1 else None
   if key:
    save(p,set_icon(text,key).encode())
    # Leave XFCE trust decisions to the user; never mark arbitrary existing shortcuts trusted.
 # Prevent the theme switcher from restoring old icon paths or regenerating the six wrong images.
 script=B/'bin/shadow_icon_style.py';s=script.read_text();a=s.index('def repair_dock_family(');b=s.index('def repair_icons(',a)
 s=s[:a]+'''def repair_dock_family(mode, base):
    # Unified assets are already rendered per palette; do not overwrite them.
    return


'''+s[b:];compile(s,str(script),'exec');save(script,s.encode(),0o644)
 script=B/'bin/shadow_whole_theme.py';s=script.read_text();a=s.index('def matching_icons(');b=s.index('def set_widgets(',a)
 s=s[:a]+'''def matching_icons(mode, base, files):
    # Icon names remain stable. Appearance changes select a theme, not a new path.
    from shadow_icon_style import repair_panel_glyphs
    repair_panel_glyphs(mode, base)


'''+s[b:];compile(s,str(script),'exec');save(script,s.encode(),0o644)
 # Execute the appearance script as a real local file so Python imports local overrides.
 script=B/'bin/shadow-appearance-apply';save(script,script.read_bytes(),0o755)
 marker=H/'.local/state/shadowrealm-os/icon-families-v1';save(marker,b'1\n')
 # Install a menu-only development binary. Keep the existing widgets/settings executable.
 local=B/'bin/shadow-link';original_bin=B/'bin/shadow-link-pre-unified';menu_bin=B/'bin/shadow-link-unified-menu'
 if not original_bin.is_file():save(original_bin,local.read_bytes(),0o755)
 save(menu_bin,binary,0o755)
 wrapper='''#!/bin/sh
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
  --menu) exec "$base/shadow-link-unified-menu" "$@" ;;
  *) exec "$base/shadow-link-pre-unified" "$@" ;;
esac
'''
 save(local,wrapper.encode(),0o755)
 # Verify all core role identities and every installed app icon in the selected theme.
 active=subprocess.check_output(['xfconf-query','-c','xsettings','-p','/Net/IconThemeName'],text=True).strip()
 gtk=Gtk.IconTheme.new();gtk.set_custom_theme(active);failures=[]
 for key in sorted({a[2] for a in apps.values()}|{'orbital-dock-'+r for r in CORE}):
  for size in (24,48,64):
   info=gtk.lookup_icon(key,size,0)
   if not info or not info.get_filename() or not Path(info.get_filename()).is_relative_to(U/active):failures.append((key,size))
 # Menu process must be relaunched (it is a separate GTK application).
 env=os.environ.copy();env.update(DISPLAY=':0',DBUS_SESSION_BUS_ADDRESS=f'unix:path=/run/user/{os.getuid()}/bus')
 subprocess.run(['pkill','-TERM','-x','Shadow Menu'],env=env,check=False)
 for cmd in ([str(Path('/opt/shadowrealm-os-xfce-panel/bin/xfce4-panel')),'-r'],['xfdesktop','--reload']):
  try:r=subprocess.run(cmd,env=env,timeout=20,check=False);print('REFRESH',cmd[0],r.returncode,flush=True)
  except Exception as e:print('REFRESH_WARNING',e,flush=True)
 print('FILES_CHANGED:',changes,'APPLICATIONS_MAPPED:',len(apps),'MISSING_NATIVE_ART:',len(missing),'LOOKUP_FAILURES:',len(failures),'BACKUP:',BACK,sep='\n',flush=True)
 if failures:print('LOOKUP_FAILURE_DETAILS:',failures[:25]);raise SystemExit(2)
 print('MENU_SOURCE_PATCH_INSTALLED; open menu and drag Terminal to verify visually.',flush=True)
if __name__=='__main__':main()
