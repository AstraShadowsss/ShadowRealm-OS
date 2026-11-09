# Building ShadowRealm-OS

ShadowRealm-OS is a customized Debian 13 desktop. Its original desktop, artwork, Terminal and nine offline games are maintained here. Debian packages remain managed by APT; sandboxed applications use Flatpak.

## Contents

- `components/`: editable C/Python/shell code, root helpers, eight theme asset packs, native component builders and the exact upstream Xfce panel source plus ShadowRealm-OS patch.
- `games/`: nine Linux games, package builder, icons and rules tests.
- `release/shadowrealm-os-live/`: AMD64 live/installer build, defaults, sanitization and inspection scripts.
- Third-party source archives are in the local Project / Rebuild Files / Third-party Sources directory, or the matching SourceForge source distribution.

Keep these directories together with the project guide. Generated ISO images and their checksums belong in the separate ShadowRealm-OS Release folder.

## Build custom packages

Use a disposable Debian 13 AMD64 VM with at least 4 GB RAM and 45 GB available disk space. The build commands do not read a personal desktop account. Install the development tools:

```sh
sudo apt-get update
sudo apt-get install build-essential dpkg-dev pkg-config python3 python3-apt python3-gi python3-pil gettext libgtk-3-dev libvte-2.91-dev libxfce4ui-2-dev libxfce4util-dev libxfconf-0-dev libexo-2-dev libwnck-3-dev libgarcon-1-dev libgarcon-gtk3-1-dev libdbusmenu-gtk3-dev libgtk-layer-shell-dev libxfce4windowing-0-dev live-build xorriso squashfs-tools cryptsetup lvm2 librsvg2-bin
mkdir -p outputs
python3 components/build-packages.py components outputs
python3 components/build-artwork.py components outputs
python3 components/build-experience.py components outputs
python3 components/build-security.py components outputs
python3 components/build-installer.py components outputs
python3 components/build-identity.py outputs
python3 release/build-archive-keyring.py release/shadowrealm-os-archive-keyring.gpg outputs
bash components/build-panel.sh outputs
python3 games/build-debs.py outputs
```

The games builder produces nine independently removable DEBs in `outputs/`. Do not mix earlier package revisions into that directory. Desktop uses DESKTOP_VERSION 0.2.3; artwork and Terminal use ASSET_VERSION 0.2.2; unchanged components retain 0.2.0; the distro identity package uses 2026.11-4. Increment versions before publishing an updated package.

The installer configuration package adds the maintained Calamares framework, a ShadowRealm-OS interface, offline GRUB files, optional LUKS encryption and LVM controls. Nine custom packages plus nine game packages are installed.

## Build the AMD64 installer

Use the fixed, empty build path `/var/tmp/shadowrealm-os-iso-build`; the scripts deliberately reject arbitrary root paths. Provide an ext4 build volume at `/mnt/shadowrealm-build` with at least 12 GB free. Then run:

```sh
sudo bash release/shadowrealm-os-live/prepare-build.sh /var/tmp/shadowrealm-os-iso-build --build
```

This builds a Debian live/installer base, adds the signed LibreWolf/Jami repositories and everyday applications, installs the custom packages, removes machine credentials and personal state, and creates a BIOS/UEFI hybrid image. Network access is required; upstream security packages can change, so byte-identical reproduction requires the supplied version/source manifest and a pinned Debian snapshot.

Never build by copying the owner's Home directory or by exporting the working personal VM.

## Desktop architecture and updates

System code lives under `/usr/share/shadowrealm-os/desktop/runtime/bin`. Fresh user profiles have links to that code in `~/.local/share/shadow-link/bin`; themes and personal preferences remain writable per user. Package updates therefore replace shared code while preserving settings. Older profiles containing regular private copies need a reviewed migration; do not overwrite a user's launchers or configuration wholesale.

The custom panel is isolated under `/opt/shadowrealm-os-xfce-panel`. Its session wrapper sets XDG_DATA_DIRS so Debian external plugins, including audio, resolve correctly. The patched panel provides the centered clock and editable dock integration. Its upstream license is GPL-2.0-or-later.

Terminal wraps secure Debian VTE and preserves command arguments and working directories. Its header uses the shared SR logo master. Never replace a running executable in place: build a package or use an atomic rename.

Root security and account operations use narrowly scoped, root-owned helpers and polkit. Account rename migrates login, Home and owned paths while retaining group memberships; test only with disposable accounts and keep recovery access. The account integration test explicitly requires a disposable-test environment variable.

A VirtualBox-specific initramfs hook, GRUB setting and early service select the ACPI clock when available. The helper also initializes Btrfs/RAID6/XOR drivers in a temporary single-vCPU window, restoring exactly the CPUs it offlined, to avoid observed VirtualBox/Windows kernel selftest stalls during installer storage probing. It acts only on VirtualBox and leaves physical-machine CPU/clock settings unchanged. The advanced kernel option `shadowrealm.vbox_preload=off` disables the filesystem preload for diagnosis.

## Update and signing responsibilities

Debian and signed vendor repositories supply their own packages. The revised Beta 1 includes the signed ShadowRealm-OS custom repository through the archive-keyring setup package. Maintain its signing key outside this source tree, publish matching source and notices for every updated package, and test upgrades before publishing. See update-repository.md for archive construction, publication order and metadata expiry. No publishing credentials or signing private keys are supplied.

Flatpak applications update separately. Users retain control of reboots, firewall rules, networking, DNS, Tor and VPN connections. Tor Browser and the optional system Tor proxy are distinct applications/services.

## Licenses and release checks

Original ShadowRealm-OS code and artwork use the accompanying MIT license, except specifically attributed third-party material. The Xfce panel retains its GPL license. Debian-derived installer configuration retains its ISC notices. GNOME-derived icons retain the notices in `components/adwaita-COPYRIGHT`. Debian, LibreWolf, Jami, Qt, Python, Cairo, SDL and other dependencies retain their own licenses; consult the accompanying third-party notices and corresponding sources.

Before publishing, boot BIOS and UEFI, install to a blank disk with optional encrypted root, unlock/reboot, verify unique machine identity, test appearance/default applications/audio/network/account controls, verify every checksum. Physical Wi-Fi, Bluetooth, webcam, GPU, Secure Boot claims require the actual devices; virtual tests do not substitute for those checks.

## Application menu and notices

The menu prioritizes actual roles such as WebBrowser and Email over secondary Security/Network tags. Manual category overrides still win. Galculator and GNOME Clocks are the normal calculator/clock applications; the small built-in calculator/clock views are not duplicate top-level menu entries. VLC and Shutter replace the overlapping Parole and Xfce screenshot launchers. Bluetooth has one Shadow Bluetooth entry, with Blueman device and adapter pages inside it. Xfce Terminal remains an available recovery backend rather than a second normal Terminal entry. Print defaults to Shutter without replacing a deliberately customized shortcut.

`components/test-menu-categories.c` checks the actual classifier with mixed desktop-entry tags and manual overrides. `components/vendor-notices/` is required when building the desktop package: it supplies upstream notices missing from two vendor packages. After finalizing an image root, run `python3 release/collect-release-notices.py ROOT OUTPUT` to create the package notice archive, exact package/source inventory and coverage report. Keep THIRD_PARTY_LICENSES.md with the original MIT license; neither replaces third-party terms.

The final ISO assembler keeps Calamares as the single install path and removes the unused Debian text installer and offline package pool. `release/shadowrealm-os-live/clean-boot-menu.py` verifies matching packaged boot code, creates BIOS/UEFI menus and regenerates internal checksum manifests. The final ISO includes the generated package notices under `LICENSES`. The live session automatically signs in; its temporary credentials are `user` / `live`. Installed account names and passwords are chosen during installation.

The image finalizer marks BIOS/UEFI boot maintenance packages as manual so installer cleanup cannot remove them. It removes live-build's temporary local package feed and duplicate Debian repository list, retaining one HTTPS Debian configuration and the signed vendor feeds. `update-dnscrypt-source.py` upgrades the obsolete Debian v2 resolver-list URL to upstream's v3 sources while retaining the pinned signature-verification key. The proxy listens on Debian's `127.0.2.1`; running the daemon alone does not change NetworkManager's selected DNS mode.

## Login, sounds and screensaver

The experience package installs the original sound generator and configurable session chimes, an SR screensaver module for the standard XFCE screensaver manager, and a polkit-authorized fixed-destination login-background helper. The default profile starts the bouncing-logo saver after ten idle minutes with password locking enabled. Users can change or disable it in Login, Sounds & Screensaver. GNOME Clocks supplies alarms, timers, world clocks and stopwatch; Drawing is the lightweight paint application.

Account picture changes update the stable Home `.face` image and AccountsService so the profile and LightDM use the same picture. A package-owned diversion replaces Debian's default skeleton avatar with SR for new accounts, while existing chosen pictures remain untouched.

Fresh-user xfwm appearance is seeded after the panel/workspace defaults, and GTK4 applications receive a dark preference by default. Keep those defaults when editing package construction; otherwise first login can fall back to stock window borders until a theme is applied.


## Regenerate branding

The checked-in asset archives already contain the current artwork. To edit and regenerate it, install `librsvg2-bin` and `python3-pil`, keep the approved raster masters and `palettes.json` together in `branding/`, then run:

```sh
python3 branding/build-branding.py branding build/branding
python3 branding/install-branding-inputs.py components build/branding
```

Review the generated palettes before rebuilding the artwork, desktop and Terminal packages. `palettes.json` must match the desktop appearance manifest. Preserve native third-party icons and upstream icon credits. The renderer shares one SR and wordmark geometry across palettes; source icon role PNGs are regenerated from their existing SVG masters with alpha.
