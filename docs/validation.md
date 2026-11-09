# 2026.11 beta 1 r3 validation

Image: `ShadowRealm-OS-2026.11-beta1-r3-amd64.iso`  
SHA256: `a1be7bdc349d4eb446c0e383198c7fb0489549fc5c4dc75f560da54910691d90`

## Installer correction

A fresh encrypted r2 installation reproduced its failure: the filesystem root was mode 0700, preventing D-Bus and ordinary user sessions from traversing `/`. A correct password authenticated but its session immediately closed. Restoring only the installed root to root:root mode 0755 restored graphical login and the themed desktop.

The r3 build explicitly sets and checks that root mode. Installer settings 0.2.1 also correct the target root during finalization and reject an unmounted target before copying files. The r2 image was withdrawn; use r3 for new installations. See [r2 recovery](r2-install-recovery.md) for existing installations.

## Checks on these ISO bytes

| Check | Result |
| --- | --- |
| Internal checksums and BIOS/UEFI boot entries | Passed |
| Factory privacy scan: accounts, private host keys, credentials and network/history files | Passed |
| Eight theme catalogs, current SR artwork and Linux launchers | Passed |
| Package notice coverage | 2,028 packages accounted for; 2,219 notice files |
| Filesystem root | root:root, mode 0755 |
| Installer mount guard | Rejects missing/live-root/unmounted targets; accepts a mounted filesystem |
| Cold BIOS live boot | Passed: Neon desktop, dock and widgets |
| Fresh UEFI live desktop and normal GUI installer | Passed |
| Complete automatic encrypted installation | All 39 jobs completed |
| Installed encrypted boot, graphical login and original test password | Passed without a post-install repair |
| Neon desktop, panel, dock, widgets and Terminal | Passed |

The controlled install used a blank 40 GB VirtualBox disk, 4 GB RAM, two CPUs, UEFI, US keyboard and America/New_York. Live-only diagnostic SSH was not copied into the installed root. Test credentials, private signing material and VM disks are excluded from release artifacts.

The desktop, games, kernel and signed-update configuration retain the r2 package versions except installer settings 0.2.1. Earlier app/theme/audio checks are regression context, not a claim that every application was exhaustively retested for r3. The existing signed APT feed remains separate from ISO publication; a GitHub commit does not publish an APT update.

## Limits

This is a beta. Physical hardware, Secure Boot, shared-ESP dual boot, suspend/resume and real Bluetooth-radio certification have not been performed. Test hardware from the live desktop before installing. A VM needs a passed-through Bluetooth adapter to test radio functions. Notice coverage checks confirm supplied files and inventories, not legal certification of every upstream license. Matching corresponding source and retained notices accompany the release.
