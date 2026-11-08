#!/bin/bash
# Build the same patched Xfce panel used by the reference desktop.
set -euo pipefail
src=$(cd -- "$(dirname -- "$0")" && pwd)
version=$(cat "$src/VERSION")
out=${1:?Usage: build-panel.sh OUTPUT_DIRECTORY}
mkdir -p "$out";out=$(cd "$out" && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
tar -xjf "$src/xfce4-panel_4.20.4.orig.tar.bz2" -C "$work"
cd "$work/xfce4-panel-4.20.4"
patch -p1 < "$src/shadow-panel.patch"
multiarch=$(dpkg-architecture -qDEB_HOST_MULTIARCH)
./configure --prefix=/opt/shadowrealm-os-xfce-panel --libdir="/opt/shadowrealm-os-xfce-panel/lib/$multiarch" --disable-gtk-doc
make -j2
root="$work/package"
make DESTDIR="$root" install
find "$root" -name '*.la' -delete
mkdir -p "$root/DEBIAN" "$root/usr/bin" "$root/etc/xdg/autostart" "$root/usr/share/doc/shadowrealm-os-panel"
cat > "$root/usr/bin/shadowrealm-os-panel" <<'EOF'
#!/bin/sh
export XDG_DATA_DIRS="/opt/shadowrealm-os-xfce-panel/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
exec /opt/shadowrealm-os-xfce-panel/bin/xfce4-panel "$@"
EOF
cat > "$root/usr/bin/shadowrealm-os-panel-session" <<'EOF'
#!/bin/sh
# Replace the session's ordinary panel, with a tested fallback if startup fails.
export XDG_DATA_DIRS="/opt/shadowrealm-os-xfce-panel/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
if pgrep -u "$(id -u)" -f '^/opt/shadowrealm-os-xfce-panel/bin/xfce4-panel( |$)' >/dev/null; then exit 0; fi
for attempt in 1 2 3 4 5; do
 if gdbus introspect --session --dest org.xfce.Panel --object-path /org/xfce/Panel >/dev/null 2>&1; then break; fi
 sleep 1
done
timeout 8 /usr/bin/xfce4-panel --quit || true
sleep 1
/opt/shadowrealm-os-xfce-panel/bin/xfce4-panel &
pid=$!
sleep 2
if kill -0 "$pid" 2>/dev/null && gdbus introspect --session --dest org.xfce.Panel --object-path /org/xfce/Panel | grep -q AddLauncherToPanel; then
 wait "$pid"
else
 kill "$pid" 2>/dev/null || true
 exec /usr/bin/xfce4-panel
fi
EOF
chmod 755 "$root/usr/bin/"*
cat > "$root/etc/xdg/autostart/shadowrealm-os-panel.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=ShadowRealm-OS Panel
Exec=shadowrealm-os-panel-session
OnlyShowIn=XFCE;
NoDisplay=true
EOF
cp COPYING "$root/usr/share/doc/shadowrealm-os-panel/copyright"
cp AUTHORS "$root/usr/share/doc/shadowrealm-os-panel/AUTHORS"
arch=$(dpkg --print-architecture)
# Resolve linked library package dependencies using Debian's tooling.
mkdir -p debian
printf 'Source: shadowrealm-os-panel\nSection: x11\nPriority: optional\nMaintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>\n\nPackage: shadowrealm-os-panel\nArchitecture: any\nDescription: ShadowRealm-OS centered Xfce panel\n' > debian/control
libs=$(dpkg-shlibdeps -O -e "$root/opt/shadowrealm-os-xfce-panel/bin/xfce4-panel" -l"$root/opt/shadowrealm-os-xfce-panel/lib/$multiarch" 2>/dev/null | sed -n 's/^shlibs:Depends=//p')
test -n "$libs"
cat > "$root/DEBIAN/control" <<EOF
Package: shadowrealm-os-panel
Version: $version
Section: x11
Priority: optional
Architecture: $arch
Maintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>
Depends: xfce4-panel, $libs
Description: ShadowRealm-OS centered clock and editable dock integration
EOF
find "$root" -type f -executable -exec sh -c 'file -b "$1" | grep -q ELF && strip --strip-unneeded "$1" || true' sh {} \;
dpkg-deb --root-owner-group --build "$root" "$out/shadowrealm-os-panel_${version}_${arch}.deb"
