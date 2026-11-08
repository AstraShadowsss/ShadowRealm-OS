#!/bin/sh
set -eu
test "$#" -eq 2 || { echo "Usage: sh repack-arm64.sh desktop_amd64.deb output_arm64.deb" >&2; exit 2; }
test "$(dpkg --print-architecture)" = arm64 || { echo "Run this on Debian 13 ARM64." >&2; exit 1; }
test "$(dpkg-deb -f "$1" Package)" = shadowrealm-os-desktop
test "$(dpkg-deb -f "$1" Architecture)" = amd64
test ! -e "$2"
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
dpkg-deb --raw-extract "$1" "$tmp/package"
sh "$script_dir/build-native.sh" "$tmp/bin"
runtime="$tmp/package/usr/share/shadowrealm-os/desktop/runtime/bin"
for name in shadow-link shadow-terminal-gtk-v3; do
    install -m755 "$tmp/bin/$name" "$runtime/$name"
done
for binary in "$runtime"/*; do
    if readelf -h "$binary" > "$tmp/elf" 2>/dev/null; then
        grep -q 'Machine:.*AArch64' "$tmp/elf" || {
            echo "Wrong executable architecture: $binary" >&2
            exit 1
        }
    fi
done
sed -i 's/^Architecture: amd64$/Architecture: arm64/' "$tmp/package/DEBIAN/control"
dpkg-deb --root-owner-group --build "$tmp/package" "$2"
