#!/usr/bin/python3
"""Build ShadowRealm-OS identity while retaining the Debian base-files identity."""
from pathlib import Path
import argparse, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
def put(root,name,text,mode=0o644):
 f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text);f.chmod(mode)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 put(root,'usr/lib/os-release','''PRETTY_NAME="ShadowRealm-OS (Debian 13)"
NAME="ShadowRealm-OS"
VERSION_ID="13"
VERSION="2026.11 (Debian 13 base)"
VERSION_CODENAME=trixie
ID=debian
VARIANT="ShadowRealm-OS desktop"
VARIANT_ID=shadowrealm-os
BUILD_ID=20261108.1
''')
 put(root,'etc/default/grub.d/10-shadowrealm-os.cfg','''GRUB_DISTRIBUTOR=ShadowRealm-OS
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
case " $GRUB_CMDLINE_LINUX_DEFAULT " in
 *" splash "*) ;;
 *) GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT quiet splash" ;;
esac
if [ -f /boot/grub/shadowrealm-os-background.png ]; then
 GRUB_BACKGROUND=/boot/grub/shadowrealm-os-background.png
fi
''')
 put(root,'etc/NetworkManager/conf.d/90-shadowrealm-os-privacy.conf','[connectivity]\nenabled=false\n')
 put(root,'etc/default/grub.d/20-shadowrealm-os-virtualbox.cfg','''# Stable early boot on VirtualBox/Windows hypervisors, including encrypted root.
if grep -q VirtualBox /sys/class/dmi/id/product_name 2>/dev/null; then
 for option in clocksource=acpi_pm tsc=unstable; do
  case " $GRUB_CMDLINE_LINUX_DEFAULT " in
   *" $option "*) ;;
   *) GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT $option" ;;
  esac
 done
fi
''')
 put(root,'etc/initramfs-tools/hooks/shadowrealm-os-vbox-clock','''#!/bin/sh
set -e
case "$1" in prereqs) exit 0;; esac
. /usr/share/initramfs-tools/hook-functions
copy_exec /usr/local/libexec/shadowrealm-os-vbox-clock /sbin/shadowrealm-os-vbox-clock
manual_add_modules btrfs
''',0o755)
 put(root,'etc/initramfs-tools/scripts/init-top/shadowrealm-os-vbox-clock','''#!/bin/sh
case "$1" in prereqs) exit 0;; esac
if [ -x /sbin/shadowrealm-os-vbox-clock ]; then /sbin/shadowrealm-os-vbox-clock; fi
''',0o755)
 put(root,'etc/xdg/mimeapps.list','''[Default Applications]
x-scheme-handler/http=librewolf.desktop
x-scheme-handler/https=librewolf.desktop
text/html=librewolf.desktop
application/pdf=atril.desktop
text/plain=org.xfce.mousepad.desktop
audio/mpeg=vlc.desktop
audio/flac=vlc.desktop
audio/ogg=vlc.desktop
video/mp4=vlc.desktop
video/x-matroska=vlc.desktop
video/webm=vlc.desktop
''')
 put(root,'usr/local/libexec/shadowrealm-os-first-boot','''#!/bin/sh
set -eu
umask 077
if command -v make-ssl-cert >/dev/null && [ ! -s /etc/ssl/private/ssl-cert-snakeoil.key ]; then
 make-ssl-cert generate-default-snakeoil --force-overwrite
fi
if [ -x /usr/sbin/sshd ]; then ssh-keygen -A; fi
mkdir -p /var/lib/shadowrealm-os
touch /var/lib/shadowrealm-os/first-boot-complete
''',0o755)
 put(root,'usr/lib/systemd/system/shadowrealm-os-first-boot.service','''[Unit]
Description=Initialize unique ShadowRealm-OS machine credentials
After=local-fs.target systemd-random-seed.service
Before=network-pre.target cups.service ssh.service systemd-user-sessions.service
ConditionPathExists=!/var/lib/shadowrealm-os/first-boot-complete
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/shadowrealm-os-first-boot
[Install]
WantedBy=multi-user.target
''')
 put(root,'usr/local/libexec/shadowrealm-os-vbox-clock','''#!/bin/sh
# VirtualBox on some Windows hosts exposes a TSC that stops advancing.
# Select its ACPI timer only in VirtualBox; physical hardware keeps its default.
set -eu
case "$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)" in
 *VirtualBox*) ;;
 *) exit 0 ;;
esac
clock=/sys/devices/system/clocksource/clocksource0
if grep -qw acpi_pm "$clock/available_clocksource"; then
 echo acpi_pm > "$clock/current_clocksource"
fi
# Some VirtualBox/Windows combinations stall the first RAID6/XOR filesystem
# selftests when more than one vCPU is online. Initialize that driver before
# desktop storage probing, temporarily retaining only the boot CPU. Restore
# exactly the CPUs we offlined, including on module-load failure.
if ! grep -Fq 'shadowrealm.vbox_preload=off' /proc/cmdline && [ ! -d /sys/module/btrfs ] && command -v modprobe >/dev/null; then
 offline=""
 restore_cpus() {
  for cpu in $offline; do echo 1 > "$cpu" 2>/dev/null || true; done
 }
 trap restore_cpus EXIT
 ready=yes
 for cpu in /sys/devices/system/cpu/cpu[1-9]*/online; do
  [ -f "$cpu" ] || continue
  [ "$(cat "$cpu")" = 1 ] || continue
  if echo 0 > "$cpu" 2>/dev/null; then offline="$offline $cpu"; else ready=no; break; fi
 done
 if [ "$ready" = yes ]; then modprobe btrfs || true; fi
fi
''',0o755)
 put(root,'usr/lib/systemd/system/shadowrealm-os-vbox-clock.service','''[Unit]
Description=Use the stable timer on VirtualBox Windows hosts
DefaultDependencies=no
After=systemd-remount-fs.service
Before=sysinit.target
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/shadowrealm-os-vbox-clock
RemainAfterExit=yes
[Install]
WantedBy=sysinit.target
''')
 put(root,'DEBIAN/postinst','''#!/bin/sh
set -e
if [ "$1" = configure ]; then
 deb-systemd-helper enable shadowrealm-os-first-boot.service shadowrealm-os-vbox-clock.service >/dev/null
 if command -v update-initramfs >/dev/null; then update-initramfs -u -k all; fi
fi
''',0o755)
 put(root,'usr/share/doc/shadowrealm-os-release/copyright' ,(Path(__file__).resolve().parent/'LICENSE').read_text())
 put(root,'DEBIAN/control','''Package: shadowrealm-os-release
Version: 2026.11-4
Section: misc
Priority: optional
Architecture: all
Maintainer: ShadowRealm-OS contributors <packages@shadowrealm-os.invalid>
Depends: base-files, dpkg, network-manager, systemd, init-system-helpers, ssl-cert, kmod, initramfs-tools
Description: ShadowRealm-OS identity and transparent desktop defaults
''')
 put(root,'DEBIAN/preinst','''#!/bin/sh
set -e
if [ "$1" = install ] || [ "$1" = upgrade ]; then
 dpkg-divert --package shadowrealm-os-release --add --rename --divert /usr/lib/os-release.debian /usr/lib/os-release
fi
''',0o755)
 put(root,'DEBIAN/postrm','''#!/bin/sh
set -e
if [ "$1" = remove ] || [ "$1" = purge ]; then
 dpkg-divert --package shadowrealm-os-release --remove --rename --divert /usr/lib/os-release.debian /usr/lib/os-release
fi
''',0o755)
 put(root,'DEBIAN/conffiles','/etc/default/grub.d/10-shadowrealm-os.cfg\n/etc/default/grub.d/20-shadowrealm-os-virtualbox.cfg\n/etc/NetworkManager/conf.d/90-shadowrealm-os-privacy.conf\n/etc/xdg/mimeapps.list\n')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/'shadowrealm-os-release_2026.11-4_all.deb')],check=True)
