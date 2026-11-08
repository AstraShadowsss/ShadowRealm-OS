from pathlib import Path
import json,os,shutil,subprocess,tempfile,sys
h=Path.home();base=h/'.local/share/shadow-link'
state=h/'.local/state/shadowrealm-os/release-preflight'
root=Path(tempfile.mkdtemp(prefix='desktop-package-',dir=state))
sys.path.insert(0,str(state/'desktop-src'))
from panel_defaults import seed_panel
seed_panel(root)
data=root/'usr/share/shadowrealm-os/desktop'
runtime=data/'runtime'
bin=runtime/'bin';bin.mkdir(parents=True)
def copy(src,dst,mode=0o644):
 dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dst)
 dst.chmod(mode)
commands='shadow-link shadow-appearance shadow-appearance-apply shadow-audio-panel shadow-system-panels shadow-browser shadow-account shadow-software shadow-terminal shadow-terminal-gtk-v3 shadow-files shadow-trash shadow-notes shadow-screenshot shadow-dock-settings'.split()
modules='shadow_account_preflight.py shadow_appearance_desktop.py shadow_effects.py shadow_network_tools.py shadow_airplane.py shadow_whole_theme.py'.split()
for name in commands+modules:
 copy(base/'bin'/name,bin/name,0o755 if name in commands else 0o644)
copy(base/'terminal.v3.bashrc',runtime/'terminal.v3.bashrc')
modes=json.loads((base/'appearance-modes.json').read_text())
for key,record in modes.items():
 palette=base/'icons'/key
 for path in palette.iterdir():
  if path.is_file() and not path.is_symlink() and path.suffix in ('.svg','.png'):
   copy(path,runtime/'icons'/key/path.name)
 wallpaper_names = (
  ['Professional-Coastal-Layers.png', 'Professional-Dune-Contours.png', 'Professional-Misty-Ridges.png']
  if key=='professional' else
  [f"ShadowRealm-OS-{record['wallpaper_palette']}-{variant}.png" for variant in
   ('circuit-corridor', 'Circuit-Walker', 'full-artwork', 'logo-focused', 'seated-city')]
 )
 for name in wallpaper_names:
  path=h/'Pictures/Backgrounds'/name
  if path.is_file() and not path.is_symlink():
   copy(path,data/'wallpapers'/name)
 for field in ('logo','wallpaper'):
  record[field]=Path(record[field]).name
for name in ('orbital-logo.png','term.png'):
 copy(base/'icons/neon'/name,runtime/('logo.png' if name=='orbital-logo.png' else name))
for path in (base/'icons').iterdir():
 if path.suffix in ('.svg','.png') and path.is_file() and not path.is_symlink():
  copy(path,runtime/'icons'/path.name)
copy(base/'sounds/test-tone.wav',runtime/'sounds/test-tone.wav')
(data/'appearance-modes.json').write_text(json.dumps(modes,indent=2)+'\n')
copy(state/'desktop-src/shadowrealm-os-desktop.py',root/'usr/bin/shadowrealm-os-desktop',0o755)
def write(path,text):
 path=root/path
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
for key,name,icon in [('control-center','Shadow Control Center','preferences-system'),
 ('appearance','Shadow Appearance','preferences-desktop-theme'),('network','Shadow Network','network-wired'),
 ('audio','Shadow Audio','audio-volume-high'),('account','User Account','system-users'),
 ('software','Software & Updates','system-software-update'),('terminal','Terminal','utilities-terminal')]:
 category='System;TerminalEmulator;' if key=='terminal' else 'Settings;'
 write(f'usr/share/applications/org.shadowrealm_os.{key}.desktop',
       f'[Desktop Entry]\nType=Application\nName={name}\nExec=shadowrealm-os-desktop {key}\nIcon={icon}\nCategories={category}\nTerminal=false\n')
write('etc/xdg/autostart/shadowrealm-os-first-login.desktop',"""[Desktop Entry]
Type=Application
Name=ShadowRealm-OS first login setup
Exec=shadowrealm-os-desktop prepare
OnlyShowIn=XFCE;
NoDisplay=true
""")
write('DEBIAN/control',"""Package: shadowrealm-os-desktop
Version: 0.1.1
Section: x11
Priority: optional
Architecture: amd64
Maintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>
Depends: shadowrealm-os-artwork, python3, python3-apt, python3-gi, python3-pil, gir1.2-gtk-3.0, gir1.2-gdkpixbuf-2.0, libgtk-3-0t64, libvte-2.91-0, xfce4-terminal, xfconf, thunar, accountsservice, flatpak, network-manager, network-manager-gnome, pulseaudio-utils, xfce4-pulseaudio-plugin
Description: ShadowRealm-OS desktop applications and first login setup
 Seed the ShadowRealm-OS desktop for a regular Debian Xfce user.
""")
for p in root.rglob('*'):
 if p.is_file():
  content=p.read_bytes()
  assert b'/home/example-owner' not in content and b'/home/shadowrealm-os' not in content,p
subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(state/'shadowrealm-os-desktop_0.1.1_amd64.deb')],check=True)
print(root)

