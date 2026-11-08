#!/usr/bin/python3
"""Build original desktop experience tools on Debian 13."""
from pathlib import Path
import tempfile,subprocess,shutil,sys
src=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as td:
 r=Path(td)
 def write(n,s,mode=0o644):
  f=r/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s);f.chmod(mode)
 for name in ['shadowrealm-os-experience','shadowrealm-os-saver','shadowrealm-os-session-sound','shadowrealm-os-login-background']:
  write(('usr/bin/' if name.endswith('experience') else ('usr/libexec/xfce4-screensaver/' if name.endswith('-saver') else 'usr/libexec/'))+name,(src/name).read_text(),0o755)
 subprocess.run([sys.executable,str(src/'generate-sounds.py'),str(r/'usr/share/sounds/ShadowRealm-OS/stereo')],check=True)
 write('usr/share/sounds/ShadowRealm-OS/index.theme','[Sound Theme]\nName=ShadowRealm-OS\nInherits=freedesktop\nDirectories=stereo\n[stereo]\nOutputProfile=stereo\n')
 write('usr/share/applications/shadowrealm-os-experience.desktop','[Desktop Entry]\nType=Application\nName=Login, Sounds & Screensaver\nExec=shadowrealm-os-experience\nIcon=preferences-desktop\nCategories=Settings;DesktopSettings;\n')
 write('usr/share/applications/screensavers/shadowrealm-os.desktop','[Desktop Entry]\nType=Application\nName=ShadowRealm-OS\nComment=Original bouncing logo, circuit or digital rain\nExec=/usr/libexec/xfce4-screensaver/shadowrealm-os-saver\nTryExec=/usr/libexec/xfce4-screensaver/shadowrealm-os-saver\nCategories=Screensaver;\nOnlyShowIn=XFCE;\nHidden=true\n')
 write('usr/lib/systemd/user/shadowrealm-os-session-sound.service','[Unit]\nDescription=ShadowRealm-OS optional session chimes\nAfter=pipewire-pulse.service\nWants=pipewire-pulse.service\n[Service]\nType=oneshot\nRemainAfterExit=yes\nExecStart=/usr/libexec/shadowrealm-os-session-sound login\nExecStop=/usr/libexec/shadowrealm-os-session-sound logout\nTimeoutStopSec=5\n[Install]\nWantedBy=default.target\n')
 link=r/'etc/systemd/user/default.target.wants/shadowrealm-os-session-sound.service';link.parent.mkdir(parents=True,exist_ok=True);link.symlink_to('/usr/lib/systemd/user/shadowrealm-os-session-sound.service')
 write('usr/share/polkit-1/actions/org.shadowrealm_os.login-background.policy','''<?xml version="1.0" encoding="UTF-8"?><policyconfig><action id="org.shadowrealm_os.login-background"><description>Change the system login background</description><message>Authentication is required to change the login screen background</message><defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>auth_admin_keep</allow_active></defaults><annotate key="org.freedesktop.policykit.exec.path">/usr/libexec/shadowrealm-os-login-background</annotate></action></policyconfig>''')
 # Fresh accounts inherit the approved SR image; existing custom pictures are preserved.
 avatar=Path('/usr/share/pixmaps/shadowrealm-os-avatar.png')
 source=src.parent/'branding/sr-logo-neon.png'
 for n in ['usr/share/pixmaps/shadowrealm-os-avatar.png']:
  target=r/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 write('etc/lightdm/lightdm-gtk-greeter.conf.d/92-shadowrealm-os-avatar.conf','[greeter]\ndefault-user-image=/usr/share/pixmaps/shadowrealm-os-avatar.png\n')
 write('etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-screensaver.xml','''<?xml version="1.0"?><channel name="xfce4-screensaver" version="1.0"><property name="saver" type="empty"><property name="enabled" type="bool" value="true"/><property name="mode" type="int" value="2"/><property name="idle-activation" type="empty"><property name="enabled" type="bool" value="true"/><property name="delay" type="int" value="10"/></property><property name="themes" type="empty"><property name="list" type="array"><value type="string" value="screensavers-shadowrealm-os"/></property></property></property><property name="lock" type="empty"><property name="enabled" type="bool" value="true"/></property></channel>''')
 write('DEBIAN/postinst',"#!/bin/sh\nset -e\nif [ \"$1\" = configure ]; then\n dpkg-divert --package shadowrealm-os-experience --add --rename --divert /etc/skel/.face.debian-default /etc/skel/.face\n cp /usr/share/pixmaps/shadowrealm-os-avatar.png /etc/skel/.face\n chmod 644 /etc/skel/.face\nfi\n",0o755)
 write('DEBIAN/postrm',"#!/bin/sh\nset -e\nif [ \"$1\" = remove ]; then\n rm -f /etc/skel/.face\n dpkg-divert --package shadowrealm-os-experience --remove --rename --divert /etc/skel/.face.debian-default /etc/skel/.face\nfi\n",0o755)
 write('usr/share/doc/shadowrealm-os-experience/copyright',(src/'LICENSE').read_text())
 write('DEBIAN/control','Package: shadowrealm-os-experience\nVersion: 0.2.0\nArchitecture: all\nSection: x11\nPriority: optional\nMaintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>\nDepends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, gir1.2-gdkpixbuf-2.0, polkitd, pkexec, pulseaudio-utils, xfce4-screensaver, gnome-clocks, drawing\nDescription: ShadowRealm-OS login artwork, original chimes and screensaver preferences\n')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(r),str(out/'shadowrealm-os-experience_0.2.0_all.deb')],check=True)

