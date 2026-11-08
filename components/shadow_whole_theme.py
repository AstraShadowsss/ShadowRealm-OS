from pathlib import Path
import hashlib,io,os,re,subprocess
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gio,GLib,Gtk,GdkPixbuf
from PIL import Image,ImageColor,ImageOps

def matching_icons(mode,base,files):
    home=Path.home()
    original_theme=Gtk.IconTheme.new()
    original_theme.set_custom_theme('Adwaita')
    original_theme.append_search_path(str(home/'.local/share/flatpak/exports/share/icons'))
    original_theme.append_search_path('/var/lib/flatpak/exports/share/icons')
    icon_dir=home/'.local/share/icons'/mode['icons']/'48x48/apps'
    icon_dir.mkdir(parents=True,exist_ok=True)
    neutral=mode.get('unbranded',False)
    def source(name):
        if name.startswith('/'):
            return Path(name) if Path(name).is_file() else None
        match=original_theme.lookup_icon(name,48,0)
        return Path(match.get_filename()) if match and match.get_filename() else None
    def paint(name,target,overwrite=False):
        if target.exists() and not overwrite:return True
        src=source(name)
        if src is None:return False
        try:
            pixbuf=GdkPixbuf.Pixbuf.new_from_file_at_scale(str(src),48,48,True)
            im=Image.open(io.BytesIO(pixbuf.save_to_bufferv('png',[],[])[1])).convert('RGBA')
        except (OSError,ValueError,TypeError,GLib.Error):
            return False
        if neutral and 'bluetooth' in name:
            ink=Image.new('RGBA',im.size,mode['foreground'])
            ink.putalpha(im.getchannel('A'))
            im=ink
        if not neutral:
            dark=ImageColor.getrgb(mode['background'])
            accent=ImageColor.getrgb(mode['accent'])
            light=ImageColor.getrgb(mode['foreground'])
            mid=tuple(round(a*.8+b*.2) for a,b in zip(accent,light))
            tint=ImageOps.colorize(ImageOps.grayscale(im),dark,light,mid=mid)
            tint.putalpha(im.getchannel('A'))
            im=tint
        canvas=Image.new('RGBA',(48,48))
        canvas.alpha_composite(im,((48-im.width)//2,(48-im.height)//2))
        temp=target.with_suffix('.tmp')
        canvas.save(temp,format='PNG')
        temp.replace(target)
        return True
    role_names={
        'terminal':'utilities-terminal','files':'system-file-manager','browser':'web-browser',
        'control-center':'preferences-system','shield':'security-high','network':'network-wired',
        'music':'multimedia-player','bluetooth':'bluetooth-active-symbolic','audio':'audio-volume-high',
        'task-manager':'utilities-system-monitor','menu':'view-app-grid','logo':'applications-other',
        'clock':'preferences-system-time','calendar':'office-calendar','screenshot':'camera-photo',
        'appearance':'preferences-desktop-theme','wallpaper':'preferences-desktop-wallpaper',
        'software':'system-software-install','calculator':'accessories-calculator','trash':'user-trash',
        'email':'internet-mail','editor':'accessories-text-editor','launcher':'view-app-grid'}
    brand_icons={'shadow-dock-launcher','shadowrealm-os-dock-menu','shadowrealm-os-release-shadow-menu','shadowrealm-os-app-menu','shadow-menu','distributor-logo','shadowrealm-os-logo'}
    if neutral:
        for path in icon_dir.glob('*.png'):
            if path.stem.startswith('shadow-switch-') or path.stem in brand_icons:continue
            role=path.stem.removeprefix('shadowrealm-os-release-').removeprefix('shadowrealm-os-app-').removeprefix('orbital-dock-').removeprefix('shadow-panel-').removeprefix('shadow-')
            original=role_names.get(role,path.stem)
            if not paint(original,path,True):paint('application-x-executable',path,True)
        for directory,pattern in [('status','*.png'),('actions','*.png'),('devices','*.png')]:
            for path in (icon_dir.parent/directory).glob(pattern):
                role=path.stem.removeprefix('shadowrealm-os-release-').removeprefix('shadow-panel-').removeprefix('shadow-')
                if not paint(role_names.get(role,path.stem),path,True):
                    paint('application-x-executable',path,True)
    palette=base/'icons'/mode['id']
    for path in files:
        text=path.read_text()
        icon_match=re.search(r'^Icon=(.*)$',text,re.M)
        if not icon_match:continue
        metadata=re.search(r'^X-ShadowRealm-OS-OriginalIcon=(.*)$',text,re.M)
        original=metadata[1] if metadata else icon_match[1]
        old=Path(original)
        branded=old.is_relative_to(base/'icons') and (palette/old.name).is_file()
        dock='/xfce4/panel/' in str(path)
        native_icon=old.is_absolute() and not original.startswith(str(base))
        if not branded:
            if metadata and (not old.is_absolute() or old.is_file()):
                restored=re.sub(r"^Icon=.*$",lambda _: "Icon="+original,text,count=1,flags=re.M)
                restored=re.sub(r"^X-ShadowRealm-OS-OriginalIcon=.*\n","",restored,count=1,flags=re.M)
                path.write_text(restored)
            continue
        if branded and (not neutral or old.stem in brand_icons):
            icon=str(palette/old.name)
        else:
            name=original
            if branded:
                role=old.stem.removeprefix('orbital-dock-').removeprefix('shadow-')
                name=role_names.get(role,'application-x-executable')
            token='shadow-switch-'+hashlib.sha256(original.encode()).hexdigest()[:16]
            target=icon_dir/(token+'.png')
            icon=str(target) if paint(name,target) or paint('application-x-executable',target) else original
        updated=re.sub(r'^Icon=.*$',lambda m:'Icon='+icon,text,count=1,flags=re.M)
        if not metadata:
            updated=updated.replace('[Desktop Entry]\n','[Desktop Entry]\nX-ShadowRealm-OS-OriginalIcon='+original+'\n',1)
        if updated!=text:path.write_text(updated)
    subprocess.run(['gtk-update-icon-cache','-f','-t',str(icon_dir.parent.parent)],stdout=subprocess.DEVNULL,check=True)

def set_widgets(professional,base):
    entry=Path.home()/'.config/autostart/shadow-link.desktop'
    if not entry.exists():
        system=Path('/etc/xdg/autostart/shadow-link.desktop')
        if not system.is_file():return
        entry.parent.mkdir(parents=True,exist_ok=True)
        entry.write_text(system.read_text())
    original=entry.read_text()
    updated=re.sub(r'^Hidden=.*\n','',original,flags=re.M)
    if professional:
        updated=updated.replace('[Desktop Entry]\n','[Desktop Entry]\nHidden=true\n',1)
    if updated!=original:entry.write_text(updated)
    binary=str(base/'bin/shadow-link')
    running=[]
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args=proc.read_bytes().rstrip(b'\0').split(b'\0')
            if args==[os.fsencode(binary),b'--widgets']:
                running.append(int(proc.parent.name))
        except (OSError,ValueError):continue
    if professional:
        for pid in running:
            try:os.kill(pid,15)
            except ProcessLookupError:pass
    elif not running:
        subprocess.Popen([binary,'--widgets'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
