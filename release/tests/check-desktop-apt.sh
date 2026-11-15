#!/bin/bash
# Run on an installed ShadowRealm-OS system with current APT indexes.
# Optional APT arguments can select isolated sources and lists for a suite simulation.
set -euo pipefail
export LC_ALL=C

desktop=shadowrealm-os-desktop
required=(
    "$desktop" shadowrealm-os-artwork shadowrealm-os-panel shadowrealm-os-terminal
    xfdesktop4 xfce4-panel xfce4-session xfwm4 gvfs thunar
    network-manager network-manager-applet nm-connection-editor
)
for package in "${required[@]}"; do
    test "$(dpkg-query -W -f='${db:Status-Status}' "$package")" = installed
done
test "$(apt-mark showmanual "$desktop")" = "$desktop"
if dpkg-query -W -f='${Depends}' "$desktop" | grep -Fq network-manager-gnome; then
    echo 'Obsolete network-manager-gnome dependency' >&2
    exit 1
fi
test -x /usr/bin/shadowrealm-os-desktop
test -x /usr/share/shadowrealm-os/desktop/runtime/bin/shadow-link
test -r /etc/xdg/autostart/shadow-link.desktop
test -r /etc/xdg/autostart/shadowrealm-os-session.desktop

plan=$(mktemp)
trap 'rm -f "$plan"' EXIT
simulate() {
    local package
    if ! apt-get -s "$@" >"$plan" 2>&1; then
        cat "$plan" >&2
        return 1
    fi
    for package in "${required[@]}"; do
        if grep -Eq "^Remv $package([ :]|$)" "$plan"; then
            echo "APT would remove $package during $*" >&2
            grep '^Remv ' "$plan" >&2
            return 1
        fi
    done
    printf 'PASS: %s\n' "$*"
}

simulate "$@" dist-upgrade
simulate "$@" autoremove
if [[ $(dpkg-query -W -f='${db:Status-Status}' network-manager-gnome 2>/dev/null || true) == installed ]]; then
    simulate "$@" remove network-manager-gnome
else
    echo 'SKIP: network-manager-gnome is already absent'
fi
