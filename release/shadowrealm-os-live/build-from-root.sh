#!/bin/bash
# Produce a bootable hybrid ISO from a verified, unmounted live-build root.
set -euo pipefail
test "$#" = 3
tools_dir=$(cd -- "$(dirname -- "$0")" && pwd)
root=$(realpath "$1");base=$(realpath "$2");out=$(realpath -m "$3")
case "$root" in /var/tmp/shadowrealm-os-iso-build/chroot|/mnt/shadowrealm-build/root) ;; *) exit 2;; esac
test "$(id -u)" = 0
test -L "$root/etc/os-release"
cmp "$root/etc/os-release" "$root/usr/lib/os-release"
mountpoint -q /mnt/shadowrealm-build || { echo "Mount the ext4 release scratch volume first." >&2; exit 2; }
test ! -e "$out";test ! -e "$out.partial"
! findmnt -rn -o TARGET | grep -F "$root/" >/dev/null
work=$(mktemp -d -p /mnt/shadowrealm-build iso-stage.XXXXXXXX)
mkdir -p "$work/live" "$work/isolinux" "$work/boot/grub"
for name in shadowrealm-os-desktop shadowrealm-os-terminal shadowrealm-os-panel shadowrealm-os-security shadowrealm-os-artwork shadowrealm-os-installer-settings; do
 expected=0.2.0
 case "$name" in shadowrealm-os-installer-settings) expected=0.2.1;; shadowrealm-os-desktop) expected=0.2.3;; shadowrealm-os-terminal|shadowrealm-os-artwork) expected=0.2.2;; esac
 test "$(dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Version}' "$name")" = "$expected"
done
test "$(dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Version}' shadow-solitaire)" = 0.2.0-1
if awk -F: '$3>=1000 && $3<65534 {bad=1} END {exit bad}' "$root/etc/passwd"; then :;else exit 1;fi
find "$root/var/log" -type f -exec truncate -s 0 {} +
find "$root/etc/ssh" -maxdepth 1 -name 'ssh_host_*' -delete
rm -f "$root/etc/ssl/private/ssl-cert-snakeoil.key" "$root/etc/ssl/certs/ssl-cert-snakeoil.pem" "$root/var/lib/shadowrealm-os/first-boot-complete"
truncate -s 0 "$root/etc/machine-id"
test ! -e "$root/etc/apt/apt.conf.d/99shadowrealm-os-build-proxy"
python3 "$tools_dir/prune-old-icon-caches.py" "$root"
python3 "$tools_dir/check-packaged-assets.py" "$root"
collector="$tools_dir/../collect-release-notices.py"
test -f "$collector" || collector="$tools_dir/collect-release-notices.py"
python3 "$collector" "$root" "$work/LICENSES"
# A private staging directory may be mode 0700. Preserve normal root access
# in the image: otherwise installed D-Bus and user sessions cannot start.
chown 0:0 "$root"
chmod 0755 "$root"
test "$(stat -c '%a:%u:%g' "$root")" = 755:0:0
mksquashfs "$root" "$work/live/filesystem.squashfs" -root-mode 0755 -comp zstd -Xcompression-level 3 -processors 2 -no-progress -noappend
kernel=$(find "$root/boot" -maxdepth 1 -type f -name 'vmlinuz-*' -printf '%f\n' | sort -V | tail -1)
version=${kernel#vmlinuz-}
for suffix in '' "-$version"; do
 cp "$root/boot/$kernel" "$work/live/vmlinuz$suffix"
 cp "$root/boot/initrd.img-$version" "$work/live/initrd.img$suffix"
done
dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Package}\t${Version}\n' | sort > "$work/live/filesystem.packages"
xorriso -osirrox on -indev "$base" -extract /isolinux "$work/isolinux" -extract /boot/grub "$work/boot/grub" -extract /md5sum.txt "$work/md5sum.original" -extract /sha256sum.txt "$work/sha256sum.original" >/dev/null 2>&1
python3 - "$root" "$work" <<'PYBRAND'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
root,work=map(Path,sys.argv[1:])
canvas=Image.new('RGB',(800,600),'black')
logo=Image.open(root/'usr/share/shadowrealm-os/branding/ShadowRealm-OS-Circular-Neon.png').convert('RGBA')
logo.thumbnail((220,220),Image.Resampling.LANCZOS)
canvas.paste(logo,(35,25),logo)
draw=ImageDraw.Draw(canvas)
fonts=root/'usr/share/fonts/truetype/dejavu'
wordmark=Image.open(root/'usr/share/shadowrealm-os/branding/Wordmark-Neon.png').convert('RGBA')
wordmark.thumbnail((460,90),Image.Resampling.LANCZOS)
canvas.paste(wordmark,(285,50),wordmark)
draw.text((285,125),'Live desktop and installer',font=ImageFont.truetype(str(fonts/'DejaVuSans.ttf'),20),fill='#eeeeee')
draw.text((285,165),'Debian 13 base',font=ImageFont.truetype(str(fonts/'DejaVuSans.ttf'),15),fill='#aaaaaa')
for path in [work/'isolinux/splash.png',work/'boot/grub/splash.png']:
 canvas.save(path)
PYBRAND
python3 "$tools_dir/clean-boot-menu.py" "$root" "$work" "$base"
python3 - "$work" "$base" "$out.partial" <<'PYISO'
from pathlib import Path
import subprocess,sys,json
work,base,out=map(Path,sys.argv[1:])
args=['xorriso','-indev',str(base),'-outdev',str(out)]
removed=json.loads((work/'removed-paths.json').read_text())
if removed:args+=['-rm_r',*removed,'--']
for folder in ('live','isolinux','boot/grub','LICENSES','.disk'):
 for f in sorted((work/folder).rglob('*')):
  if f.is_file() and (folder in ('live','LICENSES','.disk') or f.suffix=='.cfg' or f.name in ('splash.png','shadowrealm-os-theme.txt','shadowrealm-os-font.pf2')):
   args+=['-map',str(f),'/'+str(f.relative_to(work))]
args+=['-map',str(work/'README.txt'),'/README.txt','-map',str(work/'sha256sum.txt'),'/sha256sum.txt','-map',str(work/'md5sum.txt'),'/md5sum.txt','-boot_image','any','replay','-volid','SHADOWREALM_OS_202611','-publisher','ShadowRealm-OS Project','-application_id','ShadowRealm-OS build recipes']
subprocess.run(args,check=True)
PYISO
xorriso -indev "$out.partial" -report_el_torito plain
mv -T "$out.partial" "$out"
sha256sum "$out"
printf 'ISO staged at %s; scratch %s retained until boot tests pass.\n' "$out" "$work"
