#!/bin/sh
# Run as root on the ShadowRealm build VM.
#   sh /var/tmp/r5-root-setup.sh --resize   # grow the root filesystem, then install
#   sh /var/tmp/r5-root-setup.sh            # install only
set -e
PKG=/var/tmp/r5-out

if [ "${1:-}" = "--resize" ]; then
    if ! command -v growpart >/dev/null 2>&1; then
        apt-get update -qq && apt-get install -y cloud-guest-utils || true
    fi
    if command -v growpart >/dev/null 2>&1; then
        growpart /dev/sda 2 || true
    else
        echo "growpart is not available; the partition was not grown." >&2
        exit 1
    fi
    resize2fs /dev/sda2
fi

# Install the staged r5 set in version order. If an older desktop build is
# still present, the newer one is installed last; the r5 staging directory
# should normally contain only the current versions.
set -- $(ls -1 "$PKG"/*.deb 2>/dev/null | sort -V)
[ "$#" -gt 0 ] || { echo "No packages found in $PKG" >&2; exit 1; }
dpkg -i "$@"
apt-get -f install -y || true
systemctl try-restart shadowrealm-os-firewall.service 2>/dev/null || true

for theme in /usr/share/icons/ShadowRealm-OS-*; do
    [ -d "$theme" ] && gtk-update-icon-cache -f -q "$theme" 2>/dev/null || true
done
update-desktop-database -q 2>/dev/null || true
pkill -f 'shadowrealm-os-desktop widgets' 2>/dev/null || true

echo "Installed desktop: $(dpkg-query -W -f='${Version}' shadowrealm-os-desktop)"
df -h /
