#!/bin/sh
# Build shadowrealm-os-messenger_<version>_amd64.deb.
# Usage: bash messenger/build-deb.sh [outputs-directory]
# Set MESSENGER_BINARY to package an existing binary, for example the
# disposable --cfg test build used in VM checks.
set -eu
here=$(cd -- "$(dirname -- "$0")" && pwd)
repo=$(cd -- "$here/.." && pwd)
outputs=${1:-$repo/outputs}
version=$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' "$here/native/Cargo.toml" | head -n1)
test -n "$version"
binary=${MESSENGER_BINARY:-$here/native/target/release/shadow-messenger}
if [ ! -x "$binary" ]; then
    cargo build --release --locked --manifest-path "$here/native/Cargo.toml"
fi
mkdir -p "$outputs"
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
install -Dm755 "$binary" "$root/usr/bin/shadow-messenger"
install -Dm644 "$here/packaging/org.shadowrealm_os.Messenger.desktop" \
    "$root/usr/share/applications/org.shadowrealm_os.Messenger.desktop"
install -Dm644 "$repo/branding/sr-logo-neon.png" "$root/usr/share/pixmaps/shadow-messenger.png"
install -Dm644 "$here/README.md" "$root/usr/share/doc/shadowrealm-os-messenger/README.md"
install -Dm644 "$repo/LICENSE" "$root/usr/share/doc/shadowrealm-os-messenger/copyright"
mkdir -p "$root/DEBIAN"
cat > "$root/DEBIAN/control" <<EOF
Package: shadowrealm-os-messenger
Version: $version
Section: net
Priority: optional
Architecture: amd64
Maintainer: ShadowRealm-OS contributors <packages@shadowrealm-os.invalid>
Depends: libc6, libdbus-1-3, libgtk-4-1, libglib2.0-0t64, libsqlite3-0, ca-certificates
Description: Native Matrix messaging for ShadowRealm-OS
 Shadow Messenger is a GTK4 Matrix client with encrypted rooms, device
 verification, recovery, presence and desktop notifications.
EOF
dpkg-deb --root-owner-group --build "$root" "$outputs/shadowrealm-os-messenger_${version}_amd64.deb"
