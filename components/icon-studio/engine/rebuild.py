#!/usr/bin/python3
"""ShadowRealm clean icon-theme rebuild; user overlay, no package deletes."""
from pathlib import Path
import argparse, configparser, fcntl, hashlib, json, os, re, subprocess, tempfile
import legacy_helpers as old
from gi.repository import Gio, Gtk, GdkPixbuf, GLib
from render import icon, art_png
H,B,U,S,A=old.H,old.B,old.U,old.S,old.A
HERE=Path(__file__).resolve().parent
STATE=H/'.local/state/shadowrealm-os/icon-rebuild-v3';STATE.mkdir(parents=True,exist_ok=True)
SIZES=(16,24,32,48,64,96,128,256)
VALID=re.compile(r'[A-Za-z0-9_.+-]+\Z')
ROLES=dict(old.ROLE_BY_NAME);ROLES.update({'login, sounds & screensaver':'login','user account':'users','user accounts':'users','shadow messenger':'email','shadow link':'app-menu','shadow messenger ...':'email','shadow task manager':'task-manager','shadow files':'files','shadow terminal':'terminal'})
ROLE_FIX={'menu':'app-menu','messenger':'email'}
EXTRA={'home':('folder-home','user-home','go-home','gnome-fs-home'),'disk':('drive-harddisk-system','drive-harddisk','filesystem-root','computer','system','my-computer'),'trash':('user-trash','gnome-fs-trash-empty','trashcan_empty'),'trash-full':('user-trash-full','gnome-fs-trash-full','trashcan_full'),'files':('system-file-manager','folder','folder-open'),'terminal':('utilities-terminal','shadow-terminal','shadowos-terminal','shadowrealm-os-terminal'),'browser':('web-browser','shadow-browser'),'login':('shadowrealm-os-experience',),'users':('shadow-account',),'email':('orbital-dock-messenger','shadow-messenger','shadow-messenger-app','shadowrealm-os-release-orbital-dock-messenger','shadowrealm-os-app-messenger','orbital-dock-email','shadow-email'),'app-menu':('orbital-dock-menu',),'theme':('shadow-appearance',),'updates':('shadow-software','orbital-dock-software'),'search':('shadow-search','system-search')}
# Names of launchers, not individual games. Keep actual games' native art unframed.
GAME_LAUNCHERS={'com.valvesoftware.Steam','net.lutris.Lutris','com.heroicgameslauncher.hgl','com.github.Matoking.protontricks','org.prismlauncher.PrismLauncher','org.polymc.PolyMC','org.libretro.RetroArch','org.DolphinEmu.dolphin-emu','net.pcsx2.PCSX2','org.ppsspp.PPSSPP','com.usebottles.bottles'}

def log(*x):print(*x,flush=True)
def run(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
def valid(s):return isinstance(s,str) and bool(VALID.fullmatch(s)) and s not in ('.','..')
def key(id):return old.appkey(id)
def source_art(name,fallback):
    if not name:return None
    img=old.native_image(name)
    if img is None and name and not name.startswith('/'):
        try:
            inf=fallback.lookup_icon(name,128,0);img=old.piximage(inf.load_icon()) if inf else None
        except Exception:pass
    return old.png(img) if img is not None and img.getchannel('A').getbbox() else None

def read_fields(p):
    try:return old.fields(p.read_text(encoding='utf-8'))
    except (OSError,UnicodeError):return {}

def role_of(f,id):
    if id=='shadowrealm-icon-studio.desktop':return 'image-viewer'
    owned=id.startswith(('org.shadowrealm_os.','shadowrealm-os-','shadow-'))
    r=old.role_of(f,owned)
    if not r and owned:r=ROLES.get(f.get('Name','').casefold())
    if not r and 'shadowrealm-os-experience' in f.get('Exec',''):r='login'
    if not r and 'shadow-account' in f.get('Exec',''):r='users'
    return ROLE_FIX.get(r,r)

def game(f,id):return ('Game' in f.get('Categories','').split(';') or any(x in id.lower().replace('-','') for x in ('circuitchase','neonascent'))) and id.removesuffix('.desktop') not in GAME_LAUNCHERS

def raster(svg,n):
    loader=GdkPixbuf.PixbufLoader.new_with_type('svg');loader.set_size(n,n);loader.write(svg);loader.close();return old.png(old.piximage(loader.get_pixbuf()))

def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

def put(root,name,data,rasters=None):
    if not valid(name):return
    write(root/'scalable/apps'/(name+'.svg'),data)
    if rasters:
        for n,d in rasters.items():write(root/f'{n}x{n}/apps'/(name+'.png'),d)

def aliases_for(role):
    a={f'orbital-dock-{role}',f'shadowrealm-os-release-orbital-dock-{role}',f'shadowrealm-os-app-{role}',f'shadowrealm-os-dock-{role}',*old.ROLE_ALIASES.get(role,()),*EXTRA.get(role,())}
    return a

def panel_name(name):return ('shadow-panel-' in name or name.endswith('-symbolic') or name in ('shadow-dock-launcher','shadow-menu','distributor-logo','shadowrealm-os-logo','shadowrealm-os-app-menu','shadowrealm-os-dock-menu','shadowrealm-os-release-shadow-menu'))

# Production refresh: no web requests, no development menu wrapper, no bulk rebuild.
def digest(data):
    return hashlib.sha256(data).hexdigest()

def atomic(path,data):
    path=Path(path)
    if not path.parent.resolve().is_relative_to(H.resolve()):
        raise RuntimeError('Refusing write outside home: '+str(path))
    if path.is_symlink():raise RuntimeError('Refusing symlink: '+str(path))
    if path.is_file() and path.read_bytes()==data:return
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.sr-icon-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.replace(tmp,path)
    finally:Path(tmp).unlink(missing_ok=True)

def load_state():
    p=STATE/'installed.json'
    if not p.exists():return {}
    data=json.loads(p.read_text())
    if not isinstance(data,dict):raise ValueError('Invalid icon state')
    return data

def configure():
    os.environ.setdefault('XDG_CURRENT_DESKTOP','XFCE')
    dirs=[str(B/'share'),str(H/'.local/share/flatpak/exports/share'),'/var/lib/flatpak/exports/share']
    dirs+=os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')
    os.environ['XDG_DATA_DIRS']=':'.join(dict.fromkeys(dirs))

def vendor_launchers():
    roots=[Path(d)/'applications' for d in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if d and Path(d).is_absolute()]
    found={}
    for root in roots:
        if root.is_dir():
            for p in sorted(root.rglob('*.desktop')):
                if p.is_file():found.setdefault(str(p.relative_to(root)).replace('/','-'),p)
    return found

def render_launcher(text, aid, original):
    # Only icon and our ownership marker change. Other groups, Exec, actions and translations survive.
    changed=old.set_icon(text,key(aid))
    changed=changed.replace('[Desktop Entry]', '[Desktop Entry]\nX-ShadowRealm-OS-OriginalIcon='+original.replace('\n','').replace('\r',''),1)
    return changed.encode()

def native_setup():
    paths=[str(H/'.local/share/icons'),str(H/'.icons'),'/usr/share/icons','/usr/local/share/icons',str(H/'.local/share/flatpak/exports/share/icons'),'/var/lib/flatpak/exports/share/icons','/usr/share/pixmaps']
    old.native=Gtk.IconTheme.new();old.native.set_custom_theme('hicolor');old.native.set_search_path(paths)
    fallback=Gtk.IconTheme.new();fallback.set_custom_theme('Adwaita');fallback.set_search_path(paths);return fallback

def plan_apps(previous,fallback):
    vendors=vendor_launchers();owned=previous.get('managed_launchers',{});saved=previous.get('original_icons',{});apps={};missing=[];visible=set()
    for app in Gio.AppInfo.get_all():
        if not isinstance(app,Gio.DesktopAppInfo) or not app.should_show():continue
        aid=app.get_id();filename=app.get_filename()
        if not valid(aid) or not aid.endswith('.desktop') or not filename:continue
        visible.add(aid);p=Path(filename)
        try:text=p.read_text(encoding='utf-8')
        except (OSError,UnicodeError):continue
        fields=old.fields(text);local=A/aid
        managed=local.is_file() and not local.is_symlink() and owned.get(aid)==digest(local.read_bytes())
        # Never overwrite a user-owned launcher. Follow vendor updates only for copies we own.
        if managed:
            vendor=vendors.get(aid)
            if vendor is None:continue
            text=vendor.read_text(encoding='utf-8');fields=old.fields(text)
            if fields.get('Hidden','').lower()=='true' or fields.get('NoDisplay','').lower()=='true':continue
        original=fields.get('Icon','')
        if original.startswith('sr-unified-') or not original:
            original=fields.get('X-ShadowRealm-OS-OriginalIcon','') or saved.get(aid,'')
        if not original or original.startswith('sr-unified-'):
            vendor=vendors.get(aid)
            if vendor:
                try:original=old.fields(vendor.read_text(encoding='utf-8')).get('Icon','')
                except (OSError,UnicodeError):original=''
        role=role_of(fields,aid)
        if role or game(fields,aid):continue # core artwork is factory-owned; games stay native
        art=source_art(original,fallback)
        custom=STATE/'custom-logos'/(aid+'.png')
        if custom.is_file() and not custom.is_symlink():art=art_png(custom.read_bytes())
        if not art:missing.append(aid);continue
        can_copy=managed or (aid in vendors and not os.path.lexists(local))
        apps[aid]={'original':original,'art':art,'launcher':render_launcher(text,aid,original) if can_copy else None}
    return apps,visible,vendors,missing

def ensure_index(root):
    root.mkdir(parents=True,exist_ok=True)
    path=root/'index.theme';source=path if path.is_file() else S/root.name/'index.theme'
    cfg=configparser.ConfigParser(interpolation=None,strict=False);cfg.optionxform=str;cfg.read(source)
    if not cfg.has_section('Icon Theme'):raise RuntimeError('Missing icon index: '+str(source))
    dirs=[x for x in cfg['Icon Theme'].get('Directories','').split(',') if x]
    for n in SIZES:
        directory=f'{n}x{n}/apps'
        if (root/directory).is_dir() and directory not in dirs:
            dirs.append(directory)
            if not cfg.has_section(directory):cfg[directory]={'Size':str(n),'Context':'Applications','Type':'Fixed'}
    if 'scalable/apps' not in dirs:dirs.append('scalable/apps')
    cfg['Icon Theme']['Directories']=','.join(dirs)
    if not cfg.has_section('scalable/apps'):cfg['scalable/apps']={'Size':'128','MinSize':'8','MaxSize':'512','Type':'Scalable','Context':'Applications'}
    from io import StringIO
    out=StringIO();cfg.write(out,space_around_delimiters=False);atomic(path,out.getvalue().encode())

def refresh_panel():
    for cmd in (['/opt/shadowrealm-os-xfce-panel/bin/xfce4-panel','-r'],['xfdesktop','--reload']):
        try:subprocess.run(cmd,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except (OSError,subprocess.TimeoutExpired):pass

def refresh_installed():
    if os.geteuid()==0:raise RuntimeError('Run as the logged-in user')
    configure()
    if not (B/'appearance-modes.json').is_file():raise RuntimeError('Desktop provisioning has not completed; retry after login')
    modes=json.loads((B/'appearance-modes.json').read_text())
    expected=json.loads((HERE/'palettes.json').read_text())
    if set(modes)!=set(expected) or any(modes[k]['icons']!=expected[k]['icons'] for k in expected):raise RuntimeError('Unexpected palette manifest')
    with (STATE/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        previous=load_state()
        pending_file=STATE/'pending-launchers.json'
        pending=json.loads(pending_file.read_text()) if pending_file.is_file() else {}
        managed=dict(previous.get('managed_launchers',{}))
        # Recover a partially committed launcher transaction without adopting arbitrary files.
        for aid,record in pending.items():
            if not valid(aid):continue
            p=A/aid
            if p.is_file() and not p.is_symlink():
                actual=digest(p.read_bytes())
                if actual in (record.get('before'),record.get('after')):managed[aid]=actual
        previous['managed_launchers']=managed
        apps,visible,vendors,missing=plan_apps(previous,native_setup())
        if not visible:raise RuntimeError('No visible desktop applications; refusing to change state')
        current={};managed=dict(previous.get('managed_launchers',{}));changed=0;changed_roots=set()
        # Process files before replacing the launcher; retry safely if interrupted.
        for aid,entry in apps.items():
            sig=digest(entry['art']+json.dumps(modes,sort_keys=True).encode());current[aid]=sig
            for m in modes.values():
                root=U/m['icons'];target=root/'scalable/apps'/(key(aid)+'.svg')
                data=icon(m,logo=entry['art'])
                if not target.is_file() or target.read_bytes()!=data:
                    if root not in changed_roots:ensure_index(root);changed_roots.add(root)
                    if target.is_file() and not target.is_symlink():
                        backup=STATE/'first-replaced-generated-icons'/target.relative_to(U)
                        if not backup.exists():atomic(backup,target.read_bytes())
                    atomic(target,data);changed+=1
            if entry['launcher'] is not None:
                dest=A/aid;new=entry['launcher'];prior=managed.get(aid)
                if not os.path.lexists(dest) or (dest.is_file() and not dest.is_symlink() and digest(dest.read_bytes())==prior):
                    if not dest.is_file() or dest.read_bytes()!=new:
                        pending[aid]={'before':prior,'after':digest(new)}
                        atomic(pending_file,json.dumps(pending).encode())
                        atomic(dest,new);changed+=1
                    managed[aid]=digest(new)
        for aid,sha in list(managed.items()):
            if not valid(aid):continue
            p=A/aid
            if aid not in apps or aid not in vendors:
                if p.is_file() and not p.is_symlink() and digest(p.read_bytes())==sha:p.unlink();changed+=1
                managed.pop(aid,None)
            elif not p.is_file() or p.is_symlink() or digest(p.read_bytes())!=sha:managed.pop(aid,None)
        for root in changed_roots:run(['gtk-update-icon-cache','-f','-t',str(root)],stdout=subprocess.DEVNULL)
        state={'fingerprint':digest(json.dumps(current,sort_keys=True).encode()),'original_icons':{aid:a['original'] for aid,a in apps.items()},'per_app':current,'managed_launchers':managed}
        atomic(STATE/'installed.json',(json.dumps(state,sort_keys=True,indent=2)+'\n').encode())
        pending_file.unlink(missing_ok=True)
        log('LOCAL_ICON_SCAN_COMPLETE',len(apps),'MISSING',len(missing),'FILES_CHANGED',changed)
        if missing:log('MISSING_ARTWORK',','.join(missing))
    if changed:refresh_panel()

def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true',required=True);p.parse_args()
    configure()
    result=Gtk.init_check()
    if not (result[0] if isinstance(result,tuple) else result):raise SystemExit('Graphical session unavailable; retry after login')
    refresh_installed()

if __name__=='__main__':main()
