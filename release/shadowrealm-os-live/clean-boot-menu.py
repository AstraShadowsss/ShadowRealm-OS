#!/usr/bin/python3
"""Prepare one supported installer path and remove the unused Debian payload."""
from pathlib import Path
import hashlib, json, shlex, subprocess, sys

root, work, base = map(Path, sys.argv[1:])
assert work.resolve().parent == Path('/mnt/shadowrealm-build')
assert work.name.startswith('iso-stage.')
removed = []
listing = subprocess.check_output(['xorriso', '-indev', str(base), '-ls', '/'], text=True, stderr=subprocess.DEVNULL)
names = {shlex.split(line)[0] for line in listing.splitlines() if line.strip()}
for name in ('pool', 'pool-udeb', 'dists', 'install', 'tools', 'firmware', 'debian', 'md5sum.README', 'sha256sum.README'):
    if name in names:
        removed.append('/'+name)
for folder in (work/'isolinux', work/'boot/grub'):
    for file in list(folder.rglob('*')):
        if not file.is_file():
            continue
        keep_cfg = file.name == 'grub.cfg' and file.parent.name.endswith('-efi')
        if (file.suffix == '.cfg' and not keep_cfg) or file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.pf2') or file.name == 'theme.txt':
            removed.append('/'+str(file.relative_to(work)))
            # Keep the freshly generated image; it replaces the old one by mapping.
            if file.name != 'splash.png':
                file.unlink()

# Verify that the boot code is represented by the supplied package sources.
for file in (work/'isolinux').glob('*.c32'):
    supplied = root/'usr/lib/syslinux/modules/bios'/file.name
    if not supplied.is_file() or supplied.read_bytes() != file.read_bytes():
        raise SystemExit('Syslinux boot-module/package mismatch: '+file.name)
boot = work/'isolinux/isolinux.bin'
supplied = root/'usr/lib/ISOLINUX/isolinux.bin'
if boot.read_bytes()[64:] != supplied.read_bytes()[64:]:
    raise SystemExit('ISOLINUX boot code does not match the supplied package.')
for platform in ('x86_64-efi', 'i386-pc'):
    sample = work/'boot/grub'/platform/'normal.mod'
    supplied = root/'usr/lib/grub'/platform/'normal.mod'
    if sample.is_file() and sample.read_bytes() != supplied.read_bytes():
        raise SystemExit('GRUB boot-module/package mismatch: '+platform)

(work/'isolinux/isolinux.cfg').write_text('''path /isolinux/
default vesamenu.c32
prompt 0
timeout 50
menu resolution 800 600
menu background /isolinux/splash.png
menu title ShadowRealm-OS
menu width 80
menu margin 8
menu vshift 16
menu rows 6
menu color title 1;36 #ffffffff #00000000 std
menu color unsel 37;44 #ffeeeeee #00000000 none
menu color sel 7;37;40 #ff000000 #ff00dce9 none
label shadowrealm-os-live
 menu label Try and install ShadowRealm-OS
 menu default
 kernel /live/vmlinuz
 append initrd=/live/initrd.img boot=live components quiet splash
label shadowrealm-os-safe
 menu label ShadowRealm-OS compatibility mode
 kernel /live/vmlinuz
 append initrd=/live/initrd.img boot=live components nomodeset
label shadowrealm-os-virtualbox
 menu label ShadowRealm-OS VirtualBox timing compatibility
 kernel /live/vmlinuz
 append initrd=/live/initrd.img boot=live components quiet splash clocksource=acpi_pm tsc=unstable
''')
subprocess.run(['grub-mkfont', '-s', '16', '-o', str(work/'boot/grub/shadowrealm-os-font.pf2'), str(root/'usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')], check=True)
(work/'boot/grub/shadowrealm-os-theme.txt').write_text('''desktop-image: "splash.png"
title-text: ""
+ boot_menu {
 left = 8%
 top = 48%
 width = 84%
 height = 32%
 item_height = 34
 item_padding = 6
 item_color = "#eeeeee"
 selected_item_color = "#00dce9"
}
+ label {
 left = 8%
 top = 88%
 width = 84%
 text = "Choose a mode with the arrow keys, then press Enter."
 color = "#b9c0c8"
}
''')
(work/'boot/grub/grub.cfg').write_text('''search --no-floppy --file --set=root /live/filesystem.squashfs
set default=0
set timeout=5
set shadow_vm_args=""
insmod smbios
smbios --type 1 --get-string 5 --set shadow_product
if [ "$shadow_product" = "VirtualBox" ]; then
 set shadow_vm_args="clocksource=acpi_pm tsc=unstable"
fi
if loadfont /boot/grub/shadowrealm-os-font.pf2; then
 set gfxmode=800x600,auto
 insmod all_video
 insmod gfxterm
 terminal_output gfxterm
 set theme=/boot/grub/shadowrealm-os-theme.txt
fi
menuentry "Try and install ShadowRealm-OS" {
 linux /live/vmlinuz boot=live components quiet splash $shadow_vm_args
 initrd /live/initrd.img
}
menuentry "ShadowRealm-OS compatibility mode" {
 linux /live/vmlinuz boot=live components nomodeset $shadow_vm_args
 initrd /live/initrd.img
}
menuentry "ShadowRealm-OS VirtualBox timing compatibility" {
 linux /live/vmlinuz boot=live components quiet splash clocksource=acpi_pm tsc=unstable
 initrd /live/initrd.img
}
''')
(work/'.disk').mkdir(exist_ok=True)
(work/'.disk/info').write_text('ShadowRealm-OS 2026.11 AMD64 live desktop and Calamares installer\n')
(work/'README.txt').write_text('ShadowRealm-OS live desktop and installer\n\nChoose Try and install ShadowRealm-OS, then open Install ShadowRealm-OS on the desktop.\nThe live session signs in automatically. Its temporary login is user, password live.\nInstalled accounts use the name and strong password you choose in the installer.\n\nLICENSES contains package notices, version inventories and the original-work license.\nCorresponding source and rebuild instructions accompany the release in ShadowRealm-OS Project.\n')
(work/'LICENSES/README.txt').write_text('These notices cover the desktop and its matching GRUB, ISOLINUX and Syslinux boot packages.\nOriginal ShadowRealm-OS work and third-party components retain separate license terms.\nExtract Package-license-notices.tar.gz to inspect the preserved notices.\nThe GPL-covered bootloader sources are included in the corresponding-source kit.\n')
(work/'removed-paths.json').write_text(json.dumps(sorted(set(removed))))

changed = {}
for folder in ('live', 'isolinux', 'boot/grub', 'LICENSES', '.disk'):
    for file in (work/folder).rglob('*'):
        if file.is_file() and (folder in ('live', 'LICENSES', '.disk') or file.suffix == '.cfg' or file.name in ('splash.png', 'shadowrealm-os-theme.txt', 'shadowrealm-os-font.pf2')):
            changed[str(file.relative_to(work))] = file
changed['README.txt'] = work/'README.txt'
for algorithm, original, output in [('md5', 'md5sum.original', 'md5sum.txt'), ('sha256', 'sha256sum.original', 'sha256sum.txt')]:
    rows = []
    for row in (work/original).read_text().splitlines():
        parts = row.split(None, 1)
        if len(parts) != 2:
            continue
        name = parts[1].removeprefix('./').lstrip('/')
        # The BIOS boot-info table is patched by xorriso; the outer ISO SHA covers it.
        if name in changed or name in ('isolinux/isolinux.bin', 'isolinux/boot.cat', 'md5sum.txt', 'sha256sum.txt'):
            continue
        if any('/'+name == old or ('/'+name).startswith(old+'/') for old in removed):
            continue
        rows.append(row)
    for name, file in sorted(changed.items()):
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, algorithm).hexdigest()
        rows.append(digest+'  ./'+name)
    (work/output).write_text('\n'.join(rows)+'\n')
print('Prepared clean BIOS/UEFI menus, verified boot-code provenance and generated both manifests.')
