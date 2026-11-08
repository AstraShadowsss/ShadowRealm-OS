#!/bin/bash
set -euo pipefail
test "$#" -eq 1 || { echo "Usage: sudo bash check-iso.sh candidate.iso" >&2; exit 2; }
test "$(id -u)" -eq 0
image=$(realpath "$1")
root=$(mktemp -d)
rootfs=$(mktemp -d)
cleanup() {
    if mountpoint -q "$rootfs"; then umount "$rootfs"; fi
    if mountpoint -q "$root"; then umount "$root"; fi
    rmdir "$rootfs" "$root"
}
trap cleanup EXIT
boot_report=$(xorriso -indev "$image" -report_el_torito plain 2>&1)
printf '%s\n' "$boot_report"
grep -Eq 'El Torito boot img.*BIOS[[:space:]]+y' <<< "$boot_report"
grep -Eq 'El Torito boot img.*UEFI[[:space:]]+y' <<< "$boot_report"
mount -o loop,ro "$image" "$root"
fs="$root/live/filesystem.squashfs"
test -s "$fs"
mount -o loop,ro "$fs" "$rootfs"
privacy_args=()
if test -n "${SHADOWREALM_OS_AUDIT_FORBIDDEN_TEXT:-}"; then
    privacy_args+=(--forbid-text "$SHADOWREALM_OS_AUDIT_FORBIDDEN_TEXT")
fi
python3 "$(dirname "$0")/audit-root-privacy.py" "$rootfs" "${privacy_args[@]}"
test -s "$root/live/filesystem.packages"
for legacy in pool pool-udeb dists install tools firmware; do
    test ! -e "$root/$legacy"
done
test -s "$root/LICENSES/Package-license-notices.tar.gz"
(cd "$root" && sha256sum -c sha256sum.txt --quiet)
lsinitramfs "$root/live/initrd.img" | grep -F 'scripts/init-top/shadowrealm-os-vbox-clock'
python3 - "$fs" <<'PY'
import subprocess, sys
text = subprocess.check_output(['unsquashfs', '-cat', sys.argv[1], 'var/lib/apt/extended_states'], text=True)
for block in text.split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines() if ': ' in line)
    if fields.get('Package') in ('grub2-common', 'grub-pc-bin', 'grub-efi-amd64-bin'):
        assert fields.get('Auto-Installed') != '1', 'Installer cleanup could remove boot maintenance tools: ' + fields['Package']
print('Boot maintenance packages retained across installer cleanup.')
PY
for name in shadowrealm-os-desktop shadowrealm-os-security shadowrealm-os-artwork shadow-pinball shadow-runner skull-invaders circuit-chase marble-reactor neon-ascent neon-breaker shadow-snake shadow-solitaire; do
    grep -Eq "^$name[[:space:]]" "$root/live/filesystem.packages"
done
unsquashfs -cat "$fs" etc/passwd |
    awk -F: '$3 >= 1000 && $3 < 60000 {print "Unexpected regular account: " $1; bad=1} END {exit bad}'
unsquashfs -ls "$fs" |
    awk '/^squashfs-root\/home\/./ || /\/\.ssh\/(authorized_keys|id_[^/]+)$/ || /\/etc\/ssh\/ssh_host_.*_key$/ || /^squashfs-root\/packages(\/|$)/ || /\/etc\/apt\/sources.list.d\/(packages|zz-sources).list$/ {print "Unexpected private or build-only path: " $0; bad=1} END {exit bad}'
sha256sum "$image"
echo "ISO package and personal-data path checks passed."
