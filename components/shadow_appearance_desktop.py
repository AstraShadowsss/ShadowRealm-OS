from pathlib import Path
import re
import subprocess

def query(channel,prop):
    result=subprocess.run(['xfconf-query','-c',channel,'-p',prop],capture_output=True,text=True)
    return result.stdout.strip() if result.returncode==0 else None

def set_property(channel,prop,value,kind='string'):
    args=['xfconf-query','-c',channel,'-p',prop,'-s',str(value)]
    if subprocess.run(args,capture_output=True).returncode:
        subprocess.run(args+['-n','-t',kind],check=True)

def wallpaper_properties():
    command=['xfconf-query','-c','xfce4-desktop','-l']
    result=subprocess.run(command,capture_output=True,text=True,check=True)
    properties={line.strip() for line in result.stdout.splitlines()
                if re.fullmatch(r'/backdrop/screen\d+/monitor[^/]+/workspace\d+/last-image',line.strip())}
    monitors=subprocess.run(['xrandr','--listactivemonitors'],capture_output=True,text=True)
    workspaces=query('xfwm4','/general/workspace_count') or '1'
    for line in monitors.stdout.splitlines()[1:]:
        output=line.split()[-1]
        for index in range(int(workspaces)):
            properties.add(f'/backdrop/screen0/monitor{output}/workspace{index}/last-image')
    if not properties:
        raise RuntimeError('No active desktop display was found.')
    return sorted(properties)

def matching_wallpaper(mode,properties):
    for prop in properties:
        current=query('xfce4-desktop',prop)
        if not current or '/Pictures/Backgrounds/' not in current:
            continue
        match=re.search(r'-(full-artwork|logo-focused|Circuit-Walker|seated-city|circuit-corridor)\.png$',current)
        if match:
            candidate=Path.home()/'Pictures/Backgrounds'/f"ShadowRealm-OS-{mode['wallpaper_palette']}-{match[1]}.png"
            if candidate.is_file():
                return candidate
    return Path(mode['wallpaper'])

def set_wallpaper(path,properties=None):
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    for prop in properties or wallpaper_properties():
        set_property('xfce4-desktop',prop,path)
        style=prop.removesuffix('last-image')+'image-style'
        if query('xfce4-desktop',style) is None:
            set_property('xfce4-desktop',style,4,'int')
    subprocess.run(['xfdesktop','--reload'],capture_output=True,check=True)
