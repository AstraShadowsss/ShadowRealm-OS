#!/bin/bash
# Refresh only an existing disposable live-build root; never point this at /.
set -euo pipefail
test "$(id -u)" = 0
root=$(realpath "${1:?Usage: refresh-live-root.sh ROOT PACKAGE_DIRECTORY}")
packages=$(realpath "${2:?Package directory required}")
case "$root" in /var/tmp/shadowrealm-os-iso-build/chroot|/mnt/shadowrealm-build/root) ;; *) echo 'Use an isolated live-build root.' >&2; exit 2;; esac
test -f "$root/var/lib/dpkg/status"
if awk -F: '$3>=1000 && $3<65534 {found=1} END {exit !found}' "$root/etc/passwd"; then echo 'Unexpected personal account in release root' >&2; exit 1; fi
cleanup(){
 rm -f "$root/etc/apt/apt.conf.d/99shadowrealm-os-build-proxy"
 for part in sys proc dev; do mountpoint -q "$root/$part" && umount -R "$root/$part" || true; done
 if test -e "$root/usr/sbin/policy-rc.d.shadowrealm-os-saved"; then mv "$root/usr/sbin/policy-rc.d.shadowrealm-os-saved" "$root/usr/sbin/policy-rc.d"; else rm -f "$root/usr/sbin/policy-rc.d"; fi
}
trap cleanup EXIT
if test -e "$root/usr/sbin/policy-rc.d"; then cp -a "$root/usr/sbin/policy-rc.d" "$root/usr/sbin/policy-rc.d.shadowrealm-os-saved"; fi
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d";chmod 755 "$root/usr/sbin/policy-rc.d"
for part in dev sys; do mount --rbind "/$part" "$root/$part";mount --make-rslave "$root/$part";done
mount -t proc proc "$root/proc"
cp -L /etc/resolv.conf "$root/etc/resolv.conf"
export DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
sed -i "s/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/" "$root/etc/locale.gen"
chroot "$root" locale-gen
printf 'LANG=en_US.UTF-8\n' > "$root/etc/default/locale"
chroot "$root" apt-get update
chroot "$root" apt-get install -y extrepo extrepo-offline-data gnupg curl ca-certificates
chroot "$root" extrepo enable librewolf
chroot "$root" extrepo update librewolf
# Jami's signed stable Debian 13 repository. Key is scoped to this repository.
chroot "$root" curl -fsSL https://dl.jami.net/public-key.gpg -o /usr/share/keyrings/jami-archive-keyring.gpg.pending
# Pin the official repository key used by this release; review upstream rotation.
jami_fingerprint=$(chroot "$root" gpg --batch --show-keys --with-colons /usr/share/keyrings/jami-archive-keyring.gpg.pending 2>/dev/null | awk -F: '$1=="fpr" && !seen++ {print $10}')
if test "$jami_fingerprint" != A295D773307D25A33AE72F2F64CD5FA175348F84; then
 rm -f "$root/usr/share/keyrings/jami-archive-keyring.gpg.pending"
 echo 'Jami repository key changed. Verify the upstream rotation before rebuilding.' >&2
 exit 1
fi
mv "$root/usr/share/keyrings/jami-archive-keyring.gpg.pending" "$root/usr/share/keyrings/jami-archive-keyring.gpg"
printf 'deb [signed-by=/usr/share/keyrings/jami-archive-keyring.gpg] https://dl.jami.net/stable/debian_13/ jami main\n' > "$root/etc/apt/sources.list.d/jami.list"
chroot "$root" apt-get update
chroot "$root" apt-get -y full-upgrade
chroot "$root" apt-get install -y librewolf jami thunderbird guvcview gnome-authenticator sirikali gocryptfs gparted gnupg torbrowser-launcher openvpn wireguard-tools network-manager-openvpn-gnome network-manager-openconnect-gnome xarchiver xfce4-taskmanager gnome-clocks mousepad galculator ristretto onboard seahorse libpam-gnome-keyring gvfs-backends gvfs-fuse thunar-archive-plugin thunar-volman xfce4-notes xfce4-clipman pipewire-audio wireplumber pavucontrol pulseaudio-utils bluez blueman dnscrypt-proxy flatpak xdg-desktop-portal-gtk mate-polkit
rm -rf -- "$root/tmp/shadowrealm-os-packages"
mkdir -p "$root/tmp/shadowrealm-os-packages"
for name in artwork desktop terminal panel security installer-settings; do
 file=$(find "$packages" -maxdepth 1 -name "shadowrealm-os-${name}_*_*.deb" -print | sort -V | tail -n1)
 test -s "$file";cp "$file" "$root/tmp/shadowrealm-os-packages/"
done
chroot "$root" /bin/sh -c 'apt-get install -y /tmp/shadowrealm-os-packages/*.deb' 
# Refresh games from their current package versions, including Spider and the spiral map.
test "$(find "$packages" -maxdepth 1 -type f -name '*-1_all.deb' ! -name 'shadowrealm-os-*' | wc -l)" -eq 9
find "$packages" -maxdepth 1 -type f -name '*-1_all.deb' ! -name 'shadowrealm-os-*' -exec cp {} "$root/tmp/shadowrealm-os-packages/" \;
test "$(find "$root/tmp/shadowrealm-os-packages" -name '*_all.deb' | wc -l)" -eq 11
cp "$packages/shadowrealm-os-archive-keyring_2026.11-1_all.deb" "$root/tmp/shadowrealm-os-packages/"
chroot "$root" /bin/sh -c 'apt-get install -y /tmp/shadowrealm-os-packages/*.deb' 
rm -rf -- "$root/tmp/shadowrealm-os-packages"
chroot "$root" flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
chroot "$root" /usr/sbin/plymouth-set-default-theme shadowrealm-os
chroot "$root" update-initramfs -u -k all
systemctl --root="$root" enable NetworkManager.service bluetooth.service shadowrealm-os-firewall.service shadowrealm-os-brand-sync.timer shadowrealm-os-security-status.timer shadow-account-rename.service
systemctl --root="$root" disable ssh.service ssh.socket tor.service tor@default.service 2>/dev/null || true
mkdir -p "$root/etc/lightdm/lightdm.conf.d"
printf '[Seat:*]\ngreeter-hide-users=false\ngreeter-show-manual-login=true\nallow-guest=false\n' > "$root/etc/lightdm/lightdm.conf.d/50-shadowrealm-os-users.conf"
printf 'shadowrealm-os\n' > "$root/etc/hostname"
# No build-host DNS, IDs, logs or access keys in the image.
rm -f "$root/etc/resolv.conf";ln -s /run/NetworkManager/resolv.conf "$root/etc/resolv.conf"
truncate -s 0 "$root/etc/machine-id"
rm -f "$root/var/lib/dbus/machine-id"
find "$root/etc/ssh" -maxdepth 1 -name 'ssh_host_*' -delete
chroot "$root" apt-get clean
printf 'PASS current desktop, terminal, panel, security, artwork and everyday applications installed\n'
