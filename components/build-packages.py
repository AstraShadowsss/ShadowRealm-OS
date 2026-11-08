#!/usr/bin/env python3
"""Build the current ShadowRealm-OS desktop and Terminal from editable sources.
Run on Debian 13 with build-essential, pkg-config, libgtk-3-dev,
libvte-2.91-dev and dpkg-dev installed. No account or desktop is modified.
"""
import argparse, os, shutil, subprocess, tempfile, sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(src))
from panel_defaults import seed_panel
version=(src/'VERSION').read_text().strip()
arch=subprocess.check_output(['dpkg','--print-architecture'],text=True).strip()
def run(*args):subprocess.run(args,check=True)
def write(root,name,text,mode=0o644):
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);path.chmod(mode)
def control(root,name,depends,description):
 write(root,f'usr/share/doc/{name}/copyright',(src/'LICENSE').read_text())
 write(root,'DEBIAN/control',f'Package: {name}\nVersion: {version}\nSection: x11\nPriority: optional\nArchitecture: {arch}\nMaintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>\nDepends: {depends}\nDescription: {description}\n')
def build(root,name):
 run('dpkg-deb','--root-owner-group','--build',str(root),str(out/f'{name}_{version}_{arch}.deb'))
with tempfile.TemporaryDirectory(prefix='shadowrealm-os-packages-') as td:
 root=Path(td)/'desktop';root.mkdir()
 run('tar','-xzf',str(src/'shadowrealm-os-desktop-defaults-source.tar.gz'),'-C',str(root))
 seed_panel(root)
 # Seed the complete first-login appearance before xfwm/settings start.
 # Both themes are installed system-wide, so provisioning order cannot cause fallback.
 import xml.etree.ElementTree as ET
 profiles=root/'etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml'
 for channel,values in {
  'xfwm4':{'general/theme':('string','ShadowRealm-OS-Neon'),'general/title_font':('string','DejaVu Sans Bold 10'),'general/use_compositing':('bool','true')},
 }.items():
  target=profiles/(channel+'.xml');target.parent.mkdir(parents=True,exist_ok=True)
  tree=ET.parse(target) if target.exists() else ET.ElementTree(ET.Element('channel',name=channel,version='1.0'))
  for name,(kind,value) in values.items():
   node=tree.getroot()
   for part in name.split('/'):
    child=next((x for x in node if x.get('name')==part),None)
    if child is None:child=ET.SubElement(node,'property',name=part,type='empty')
    node=child
   node.set('type',kind);node.set('value',value)
  tree.write(target,encoding='utf-8',xml_declaration=True)
 write(root,'usr/share/glib-2.0/schemas/90-shadowrealm-os.gschema.override',"[org.gnome.desktop.interface]\ncolor-scheme='prefer-dark'\n")
 runtime=root/'usr/share/shadowrealm-os/desktop/runtime/bin'
 runtime.mkdir(parents=True,exist_ok=True)
 names='shadow-account shadow_account_preflight.py shadow_airplane.py shadow-appearance shadow-appearance-apply shadow_appearance_desktop.py shadow-audio-panel shadow-browser shadow-dock-settings shadow_effects.py shadow-files shadow_network_tools.py shadow-notes shadow-screenshot shadow-software shadow-system-panels shadow-terminal shadow-trash shadow_whole_theme.py'.split()
 for name in names:
  target=runtime/name
  shutil.copyfile(src/name,target);target.chmod(0o644 if target.suffix=='.py' else 0o755)
 native=src
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','gio-unix-2.0'],text=True).split()
 run('cc','-O2',str(native/'shadow-link-dock.c'),'-o',str(runtime/'shadow-link'),*flags,'-lm')
 for name in ('shadow-backgrounds','shadow_flatpak_exports.py','shadow-xfce-session'):
  shutil.copyfile(src/name,runtime/name);(runtime/name).chmod(0o755)
 shutil.copyfile(src/'shadowrealm-os-desktop.py',root/'usr/bin/shadowrealm-os-desktop')
 (root/'usr/bin/shadowrealm-os-desktop').chmod(0o755)
 write(root,'etc/skel/.config/shadowrealm-os/transparency.ini','[Appearance]\nterminal-opacity=84\nwidget-opacity=88\nwindow-opacity=100\nmenu-opacity=100\npanel-opacity=100\ndock-opacity=0\n')
 write(root,'etc/xdg/autostart/shadow-link.desktop','[Desktop Entry]\nType=Application\nName=ShadowRealm-OS Widgets\nExec=shadowrealm-os-desktop widgets\nOnlyShowIn=XFCE;\nNoDisplay=true\n')
 write(root,'etc/xdg/autostart/shadowrealm-os-session.desktop','[Desktop Entry]\nType=Application\nName=ShadowRealm-OS Desktop Session\nExec=shadowrealm-os-desktop session\nOnlyShowIn=XFCE;\nNoDisplay=true\n')
 # The current wrapper launches the separately built, system-owned Terminal.
 shutil.copyfile(src/'shadow-terminal',runtime/'shadow-terminal');(runtime/'shadow-terminal').chmod(0o755)
 (runtime/'shadow-terminal-gtk-v3').unlink(missing_ok=True)
 control(root,'shadowrealm-os-desktop','shadowrealm-os-artwork, shadowrealm-os-terminal, shadowrealm-os-panel, python3, python3-apt, python3-gi, python3-pil, gir1.2-gtk-3.0, gir1.2-gdkpixbuf-2.0, libgtk-3-0t64, xfconf, thunar, accountsservice, flatpak, network-manager, network-manager-gnome, pulseaudio-utils','ShadowRealm-OS desktop controls, appearance and account defaults')
 shutil.copytree(src/'vendor-notices',root/'usr/share/doc/shadowrealm-os-desktop/vendor-notices')
 (root/'usr/share/doc/shadowrealm-os-desktop/vendor-notices').chmod(0o755)
 for notice in (root/'usr/share/doc/shadowrealm-os-desktop/vendor-notices').rglob('*'):
  notice.chmod(0o755 if notice.is_dir() else 0o644)
 build(root,'shadowrealm-os-desktop')
 root=Path(td)/'terminal';binary=root/'usr/lib/shadowrealm-os/shadow-terminal-gtk-v3';binary.parent.mkdir(parents=True)
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk+-3.0','vte-2.91'],text=True).split()
 run('cc','-O2',str(src/'shadow-terminal.c'),'-o',str(binary),*flags)
 shutil.copyfile(src/'shadowrealm-os-terminal',root/'usr/bin/shadowrealm-os-terminal') if (root/'usr/bin').exists() else None
 write(root,'usr/bin/shadowrealm-os-terminal',(src/'shadowrealm-os-terminal').read_text(),0o755)
 assets=root/'usr/share/shadowrealm-os/terminal';assets.mkdir(parents=True)
 run('tar','-xzf',str(src/'shadowrealm-os-terminal-assets.tar.gz'),'-C',str(assets))
 for f in assets.iterdir():f.chmod(0o644)
 write(root,'usr/share/xfce4/helpers/shadowrealm-os-terminal.desktop','[Desktop Entry]\nVersion=1.0\nType=X-XFCE-Helper\nName=Terminal\nIcon=utilities-terminal\nStartupNotify=false\nX-XFCE-Binaries=shadowrealm-os-terminal;\nX-XFCE-Category=TerminalEmulator\nX-XFCE-Commands=%B;\nX-XFCE-CommandsWithParameter=%B -e %s;\n')
 write(root,'etc/skel/.config/xfce4/helpers.rc','TerminalEmulator=shadowrealm-os-terminal\n')
 write(root,'DEBIAN/postinst','''#!/bin/sh
set -e
if [ "$1" = configure ]; then update-alternatives --install /usr/bin/x-terminal-emulator x-terminal-emulator /usr/bin/shadowrealm-os-terminal 70; fi
''',0o755)
 write(root,'DEBIAN/postrm','''#!/bin/sh
set -e
if [ "$1" = remove ]; then update-alternatives --remove x-terminal-emulator /usr/bin/shadowrealm-os-terminal; fi
''',0o755)
 control(root,'shadowrealm-os-terminal','libgtk-3-0t64, libvte-2.91-0, bash, fonts-dejavu-core','ShadowRealm-OS GTK and VTE Terminal with secure TLS support')
 build(root,'shadowrealm-os-terminal')
print('Built source packages:',out)
