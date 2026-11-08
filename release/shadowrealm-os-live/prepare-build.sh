#!/bin/bash
set -euo pipefail
usage() { echo "Usage: bash prepare-build.sh /path/to/empty-build-dir [--build]" >&2; exit 2; }
test "$#" -ge 1 && test "$#" -le 2 || usage
target=$1
mode=${2:---prepare}
case "$mode" in --build|--prepare) ;; *) usage;; esac
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$source_dir/../.." && pwd)
test ! -e "$target" || { echo "Build directory must not exist."; exit 1; }
mkdir -p -- "$target"
target=$(cd -- "$target" && pwd)
install -Dm644 "$source_dir/config/package-lists/shadowrealm-os-base.list.chroot" "$target/config/package-lists/shadowrealm-os-base.list.chroot"
mkdir -p "$target/config/packages.chroot"
# Build the custom components first using the docs/build-guide.md.
for name in artwork desktop terminal panel security installer-settings experience; do
 deb=$(find "$repo/outputs" -maxdepth 1 -name "shadowrealm-os-${name}_0.2.0_*.deb" -print -quit)
 test -s "$deb"
 install -m644 "$deb" "$target/config/packages.chroot/"
done
install -m644 "$repo/outputs/shadowrealm-os-release_2026.11-2_all.deb" "$target/config/packages.chroot/"
count=0
for deb in "$repo"/outputs/*-1_all.deb; do
 case "$(basename "$deb")" in shadowrealm-os-release*) continue;; esac
 dpkg-deb --info "$deb" >/dev/null
 install -m644 "$deb" "$target/config/packages.chroot/"
 count=$((count+1))
done
test "$count" -eq 9
install -Dm755 "$source_dir/config/hooks/live/0900-shadowrealm-os-defaults.hook.chroot" "$target/config/hooks/live/0900-shadowrealm-os-defaults.hook.chroot"
cd -- "$target"
if test "$mode" = --prepare; then
 echo "Prepared Debian/Xfce base, ShadowRealm-OS desktop, security, and artwork, and nine game packages at $target."
 exit 0
fi
command -v lb >/dev/null || { echo "Install live-build on the build machine first."; exit 1; }
test "$(id -u)" -eq 0 || { echo "The build stage needs a privileged, disposable Debian builder."; exit 1; }
lb config --mode debian --distribution trixie --architectures amd64 \
 --binary-images iso-hybrid --archive-areas "main contrib non-free-firmware" \
 --debian-installer live --bootappend-live "boot=live components quiet splash"
lb build
# Add the signed vendor applications, then refresh and sanitize the root.
bash "$source_dir/refresh-live-root.sh" "$target/chroot" "$repo/outputs"
bash "$source_dir/finalize-root.sh" "$target/chroot" "$repo/outputs"
bash "$source_dir/build-from-root.sh" "$target/chroot" "$target/live-image-amd64.hybrid.iso" "$target/ShadowRealm-OS-amd64.iso"
