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
# Theme-specific application icons, installed under a name owned by this
# package so they never collide with the artwork package's aliases.
cp -a "$here/packaging/icons/." "$root/usr/share/icons/"
rm -f "$root/usr/share/icons/contact-sheet.png"
install -Dm644 "$here/packaging/icons/hicolor/256x256/apps/shadow-messenger-app.png" \
    "$root/usr/share/pixmaps/shadow-messenger-app.png"
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
Depends: libc6, libdbus-1-3, libgtk-4-1, libglib2.0-0t64, libsqlite3-0, ca-certificates, gnome-keyring
Description: Native Matrix messaging for ShadowRealm-OS
 Shadow Messenger is a GTK4 Matrix client with encrypted rooms, device
 verification, recovery, presence and desktop notifications.
EOF
cat > "$root/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    for theme in /usr/share/icons/ShadowRealm-OS-* /usr/share/icons/hicolor; do
        [ -f "$theme/index.theme" ] || continue
        gtk-update-icon-cache -q -t -f "$theme" || true
    done
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$root/DEBIAN/postinst"
cat > "$root/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    for theme in /usr/share/icons/ShadowRealm-OS-* /usr/share/icons/hicolor; do
        [ -f "$theme/index.theme" ] || continue
        gtk-update-icon-cache -q -t -f "$theme" || true
    done
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$root/DEBIAN/postrm"
dpkg-deb --root-owner-group --build "$root" "$outputs/shadowrealm-os-messenger_${version}_amd64.deb"
