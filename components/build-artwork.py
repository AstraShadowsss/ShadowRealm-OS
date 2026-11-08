#!/usr/bin/python3
"""Build editable theme, logo, wallpaper and boot/login assets."""
from pathlib import Path
import argparse, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
version=(a.source/'VERSION').read_text().strip()
def write(root,name,text,mode=0o644):
 f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text);f.chmod(mode)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);subprocess.run(['tar','-xzf',str(a.source/'shadowrealm-os-artwork-source.tar.gz'),'-C',str(root)],check=True)
 # Keep vendor application icons supplied by their own packages.
 vendors=('proton-*','protonvpn*','thunar','Thunar','org.xfce.Thunar','org.xfce.thunar','org.xfce.filemanager','xfce4-terminal','org.xfce.terminal','xfce4-taskmanager','org.xfce.taskmanager','librewolf','io.gitlab.librewolf-community','thunderbird','org.mozilla.Thunderbird','vlc','net.jami.Jami','jami','libreoffice-*','io.github.Hexchat','hexchat','org.keepassxc.KeePassXC','keepassxc','org.gnome.Snapshot','com.belmoussaoui.Authenticator','guvcview','org.xfce.mousepad','mousepad','org.xfce.ristretto','ristretto','org.xfce.notes','atril','shutter','timeshift','sirikali','gparted','seahorse','org.gnome.clocks','org.gnome.Clocks','xarchiver','galculator','torbrowser-launcher','tor-browser','onboard')
 for theme in (root/'usr/share/icons').glob('ShadowRealm-OS-*'):
  for directory in theme.glob('*/apps'):
   for pattern in vendors:
    for icon in directory.glob(pattern+'.*'):
     if icon.is_file() or icon.is_symlink():icon.unlink()
 for cache in (root/'usr/share/icons').glob('ShadowRealm-OS-*/icon-theme.cache'):cache.unlink()
 write(root,'etc/lightdm/lightdm-gtk-greeter.conf.d/92-shadowrealm-os-clock.conf','[greeter]\nclock-format=%a, %-I:%M %p\n')
 write(root,'usr/local/libexec/shadowrealm-os-brand-sync',(a.source/'shadowrealm-os-brand-sync.py').read_text(),0o755)
 write(root,'usr/lib/systemd/system/shadowrealm-os-brand-sync.service','''[Unit]
Description=Match shared ShadowRealm-OS boot and login branding to the active desktop
After=systemd-logind.service
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/shadowrealm-os-brand-sync
TimeoutStartSec=6min
''')
 write(root,'usr/lib/systemd/system/shadowrealm-os-brand-sync.timer','''[Unit]
Description=Synchronize approved ShadowRealm-OS palette assets
[Timer]
OnBootSec=45s
OnUnitInactiveSec=30s
[Install]
WantedBy=timers.target
''')
 # Script themes must present an encrypted-disk passphrase prompt, not just a logo.
 script=root/'usr/share/plymouth/themes/shadowrealm-os/shadowrealm-os.script'
 script.write_text(script.read_text()+'''
prompt_sprite = Sprite();
prompt_sprite.SetOpacity(0);
fun password_prompt(prompt, bullets) {
 value = prompt + "  ";
 for (i = 0; i < bullets; i++) value += "*";
 image = Image.Text(value, 0.94, 0.94, 0.96, 1, "DejaVu Sans 14");
 prompt_sprite.SetImage(image);
 prompt_sprite.SetPosition(Window.GetWidth()/2-image.GetWidth()/2, Window.GetHeight()/2+180, 5);
 prompt_sprite.SetOpacity(1);
}
fun normal_display() { prompt_sprite.SetOpacity(0); }
Plymouth.SetDisplayPasswordFunction(password_prompt);
Plymouth.SetDisplayNormalFunction(normal_display);
message_active = 0;
fun display_message(text) {
 if (text != "") { message_active = 1; show_status(text); }
}
fun hide_message(text) {
 message_active = 0;
 if (mode == "shutdown") show_status("Shutting down...");
 else if (mode == "reboot") show_status("Restarting...");
 else show_status("Starting ShadowRealm-OS...");
}
fun service_status(text) {
 if (!message_active && text != "") show_status(text);
}
Plymouth.SetDisplayMessageFunction(display_message);
Plymouth.SetHideMessageFunction(hide_message);
Plymouth.SetUpdateStatusFunction(service_status);
''')
 write(root,'usr/share/doc/shadowrealm-os-artwork/copyright','Original ShadowRealm-OS artwork and theme code: MIT; see LICENSE.\nGNOME-derived icons are recolored/adapted from GNOME Project artwork.\nhttps://www.gnome.org\nTheir upstream license terms and credits are preserved in gnome-icon-copyright.\n')
 write(root,'usr/share/doc/shadowrealm-os-artwork/LICENSE',(a.source/'LICENSE').read_text())
 write(root,'usr/share/doc/shadowrealm-os-artwork/gnome-icon-copyright',(a.source/'adwaita-COPYRIGHT').read_text())
 write(root,'DEBIAN/control',f'''Package: shadowrealm-os-artwork
Version: {version}
Section: x11
Priority: optional
Architecture: all
Maintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>
Depends: python3, libgtk-3-bin, plymouth, plymouth-themes, lightdm-gtk-greeter, adwaita-icon-theme, fonts-dejavu-core, initramfs-tools, systemd, init-system-helpers
Description: ShadowRealm-OS themes, icons, wallpapers and boot/login branding
''')
 write(root,'DEBIAN/postinst','''#!/bin/sh
set -e
if [ "$1" = configure ]; then
 deb-systemd-helper enable shadowrealm-os-brand-sync.timer >/dev/null
 for theme in /usr/share/icons/ShadowRealm-OS-*; do
  if [ -f "$theme/index.theme" ]; then gtk-update-icon-cache -f "$theme"; fi
 done
fi
''',0o755)
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'shadowrealm-os-artwork_{version}_all.deb')],check=True)
