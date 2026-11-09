#!/bin/bash
set -euo pipefail
test "$(id -u)" = 0
root=$(realpath "${1:?Usage: finalize-root.sh ROOT PACKAGES}")
packages=$(realpath "${2:?Packages required}")
case "$root" in /var/tmp/shadowrealm-os-iso-build/chroot|/mnt/shadowrealm-build/root) ;; *) exit 2;; esac
test -f "$root/var/lib/dpkg/status"
cleanup(){
 for part in sys proc dev; do mountpoint -q "$root/$part" && umount -R "$root/$part" || true; done
 rm -f "$root/usr/sbin/policy-rc.d" "$root/etc/apt/apt.conf.d/99shadowrealm-os-build-proxy"
}
trap cleanup EXIT
export DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
for part in dev sys; do mountpoint -q "$root/$part" || mount --rbind "/$part" "$root/$part"; mount --make-rslave "$root/$part";done
mountpoint -q "$root/proc" || mount -t proc proc "$root/proc"
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d";chmod 755 "$root/usr/sbin/policy-rc.d"
rm -f "$root/etc/resolv.conf";cp -L /etc/resolv.conf "$root/etc/resolv.conf"
chroot "$root" apt-get install -y systemd-timesyncd drawing xfce4-screensaver
rm -rf -- "$root/tmp/shadowrealm-os-final-packages"
mkdir -p "$root/tmp/shadowrealm-os-final-packages"
for name in artwork desktop terminal panel security installer-settings experience; do
 file=$(find "$packages" -maxdepth 1 -name "shadowrealm-os-${name}_*_*.deb" -print | sort -V | tail -n1);test -s "$file";cp "$file" "$root/tmp/shadowrealm-os-final-packages/"
done
cp "$packages/shadowrealm-os-release_2026.11-4_all.deb" "$root/tmp/shadowrealm-os-final-packages/"
find "$packages" -maxdepth 1 -name '*-1_all.deb' ! -name 'shadowrealm-os-release*' -exec cp {} "$root/tmp/shadowrealm-os-final-packages/" \;
test "$(find "$root/tmp/shadowrealm-os-final-packages" -name '*.deb' | wc -l)" = 18
chroot "$root" /bin/sh -c 'apt-get install --reinstall -y /tmp/shadowrealm-os-final-packages/*.deb'
ln -sfn ../usr/lib/os-release "$root/etc/os-release"
chmod 755 "$root/usr/share/doc/shadowrealm-os-desktop/vendor-notices"
# Keep the selected VLC/Shutter applications without duplicate menu programs.
# Retain installed Xfce features when their optional goodies meta-package goes.
mapfile -t xfce_tools < <(chroot "$root" dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' 'xfce4-*' | awk '$2=="installed" {print $1}')
chroot "$root" apt-mark manual "${xfce_tools[@]}"
chroot "$root" apt-get purge -y light-locker parole xfce4-screenshooter debian-installer-launcher
# Keep boot maintenance tools after the installer package is removed.
chroot "$root" apt-mark manual grub2-common grub-pc-bin grub-efi-amd64-bin
rm -rf -- "$root/tmp/shadowrealm-os-final-packages"
mkdir -p "$root/etc/initramfs-tools/conf.d"
printf 'RESUME=none\n' > "$root/etc/initramfs-tools/conf.d/resume"
chroot "$root" /usr/sbin/plymouth-set-default-theme shadowrealm-os
chroot "$root" update-initramfs -u -k all
systemctl --root="$root" enable systemd-timesyncd.service apparmor.service NetworkManager.service shadowrealm-os-brand-sync.timer shadowrealm-os-security-status.timer shadowrealm-os-firewall.service
# Restore native vendor app icons and defaults, keeping ShadowRealm-OS system artwork.
test -f "$root/usr/share/applications/librewolf.desktop"
chroot "$root" librewolf --version
chroot "$root" /usr/bin/shadowrealm-os-terminal --version
chroot "$root" apt-get check
chroot "$root" apt-get clean
python3 "$(dirname "$0")/prune-old-icon-caches.py" "$root"
printf 'shadowrealm-os\n' > "$root/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 shadowrealm-os\n::1 localhost ip6-localhost ip6-loopback\n' > "$root/etc/hosts"
python3 "$(dirname "$0")/update-dnscrypt-source.py" "$root"
# Discard the temporary live-build repository; retain one signed Debian feed.
rm -f "$root/etc/apt/sources.list.d/packages.list" "$root/etc/apt/sources.list.d/zz-sources.list"
rm -rf -- "$root/packages"
cat > "$root/etc/apt/sources.list" <<'SOURCES'
deb https://deb.debian.org/debian trixie main contrib non-free-firmware
deb-src https://deb.debian.org/debian trixie main contrib non-free-firmware
deb https://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb-src https://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb https://security.debian.org/debian-security trixie-security main contrib non-free-firmware
deb-src https://security.debian.org/debian-security trixie-security main contrib non-free-firmware
SOURCES
rm -f "$root/etc/resolv.conf";ln -s /run/NetworkManager/resolv.conf "$root/etc/resolv.conf"
truncate -s 0 "$root/etc/machine-id"
rm -f "$root/var/lib/dbus/machine-id" "$root/var/lib/systemd/random-seed"
find "$root/etc/ssh" -maxdepth 1 -name 'ssh_host_*' -delete
for file in secret_key timestamps seen-bssids; do rm -f "$root/var/lib/NetworkManager/$file";done
rm -rf -- "$root/root/.ssh" "$root/root/.gnupg" "$root/root/.cache"
rm -f "$root/root/.bash_history" "$root/var/lib/shadowrealm-os/branding.json"
find "$root/var/log" -type f -exec truncate -s 0 {} +
# No build sessions or their GPG agents may hold pseudo-filesystems open.
python3 - "$root" <<'PY'
import os,pathlib,signal,sys,time
root=pathlib.Path(sys.argv[1])
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  if (p/'root').resolve()==root:os.kill(int(p.name),signal.SIGTERM)
 except (OSError,ProcessLookupError):pass
time.sleep(.5)
PY
cleanup
trap - EXIT
for part in sys proc dev; do ! mountpoint -q "$root/$part";done
# Only temporary contents inside this checked disposable root are discarded.
find "$root/tmp" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
find "$root/var/tmp" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
if awk -F: '$3>=1000 && $3<65534 {bad=1;print} END {exit bad}' "$root/etc/passwd"; then :; else echo 'Unexpected regular account' >&2;exit 1;fi
printf 'PASS finalized clean ShadowRealm-OS root, current source-built components and nine games\n'
