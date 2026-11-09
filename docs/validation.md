# 2026.11 beta 1 validation

Image: `ShadowRealm-OS-2026.11-beta1-r2-amd64.iso`
SHA256: `6b01c968226107850435573cebfc5086460a00405f44bee1023b06c251fc9741`

Checks performed on the AMD64 release build and its disposable VirtualBox test installation:

| Check | Result |
| --- | --- |
| ISO internal hashes, BIOS/UEFI boot entries, initramfs and boot maintenance packages | Passed |
| Fresh first-login appearance | Passed on revised r2 live boots: xfwm theme ShadowRealm-OS-Neon and GTK4 prefer-dark, without applying a theme manually |
| Factory privacy scan: saved accounts, private keys, network secrets and history | Passed |
| Corresponding-source archive | All 3,819 required Debian source inputs present; separate vendor sources retained |
| Package notice coverage | 2,028 installed packages; 2,219 notice files; no missing package notice records |
| BIOS live boot | Passed on the revised image; default SR theme, dock and widgets loaded |
| UEFI live desktop and Calamares installation to a blank virtual disk | Preceding installer/base build: 38 jobs completed; revised image: fresh live boot and installer preflight passed |
| Encrypted installed system: GRUB unlock, login and sudo | Passed |
| Desktop shutdown | Passed through the desktop power control |
| Installed services | No failed system services observed; NetworkManager, firewall and AppArmor active |
| AppArmor on installed system | 123 profiles loaded; 21 enforcing at the validation checkpoint |
| Eight appearance themes | Applied successfully; Neon restored; Gold SR accents and Professional Bluetooth rechecked |
| Menu icon routing | Project entries use the dock's 48px artwork; third-party applications resolve native icons |
| Clock shortcuts | Top-bar click and application desktop-entry launch open GNOME Clocks; legacy Shadow Clock route redirected |
| Menu, desktop creation, Terminal launcher and Trash | Passed; created folder moved to Trash by GUI drag |
| Audio slider and mute | Volume and mute controls verified; Windows WASAPI + Intel HD Audio enabled in the test VM, and audible chime playback confirmed by the user |
| Transparency controls | Window and menu background values persisted; text remained opaque |
| LibreWolf | Launched and rendered Example Domain over HTTPS; native menu icon/default HTTPS handler verified |
| Account picture | SR default shown; GUI choice updated the shared `.face`/AccountsService picture |
| Custom login background | Fixed-destination set/reset helper validated; theme-following override restored |
| Session sounds | Original WAVs generated; login and logout playback actions returned success; user service active |
| Screensaver | Preview and actual full-screen bouncing SR tested; mouse/keyboard wake verified; standard XFCE lock controls retained |
| Drawing and GNOME Clocks | Applications opened; alarms/timers/stopwatch available through GNOME Clocks |
| Terminal actions | Visible button acknowledgement verified; shell and secure Debian VTE started successfully |
| GitHub screenshots | Actual clean desktop, menu, Control Center, Terminal and appearance captures supplied |

The preceding installer/base-system build completed a UEFI encrypted installation and received the current desktop packages. The revised image retains that kernel and installer base, adds signed custom updates and VirtualBox startup compatibility, and was checked with fresh default BIOS and UEFI live boots. A full encrypted installation was not repeated for r2.

## Limits

This is a beta, not a claim that every application and hardware combination is bug-free. No physical-machine, Secure Boot, shared-ESP dual-boot, suspend/resume or real Bluetooth-radio certification was performed. A USB Bluetooth adapter must be available to a VM before radio functions can be tested. GNOME/GTK4 vendor applications retain their native interface; light/dark preference follows the selected theme.

Debian's AppArmor service condition skips enforcement in the live overlay environment; the installed encrypted system was verified enforcing profiles. The revised Beta 1 includes the signed custom update repository. Debian/vendor packages and custom component updates retain their separate maintainers; metadata refresh and key maintenance are documented in update-repository.md.

Notice coverage checks verify supplied files and inventories, not a legal certification of every upstream license. Matching corresponding source and retained notices are supplied with the release.

## Revised Beta 1 (r2)

The revised image passed a fresh UEFI live boot with Neon desktop, widgets, Terminal, Clocks, Software & Updates and the actual ShadowRealm-OS installer launcher. Installer preflight was checked with a blank 32 GB virtual disk. The signed HTTPS repository was accepted by APT in the live system. Standard os-release identification reports ShadowRealm-OS and BUILD_ID=20261108.1. The image uses the standard os-release symlink to its packaged identity; the image checker enforces that match.

Signed repository checks passed: real setup and identity-package upgrades, user-setting preservation, package pinning, and rejection of unsigned/altered/expired metadata and corrupt downloads. The existing encrypted-install test remains the preceding installer/base-system test; a full encrypted installation was not repeated for this metadata/keyring revision. Physical hardware and Secure Boot limits remain as above.

A separate cold BIOS default boot of the same r2 bytes also reached the branded installer ready screen. Both tests confirmed two online CPUs and early automatic Btrfs initialization without soft-lockup messages. The VirtualBox-only helper temporarily offlines secondary CPUs for kernel filesystem selftests and restores their prior state before desktop use.

## Asset and existing-account checks

The packaged catalog contains 89 roles in each of eight themes, with separate
system tiles, dock artwork and panel glyphs. Catalog checks verify role files,
vector validity and transparent system-tile corners. The 296 pre-existing
retained SVG masters were compared unchanged. Black & White replaced the
retired palette; its widgets, window decorations, dock and Terminal were
checked on the running desktop. Screenshots show real VM readings during work,
not default resource consumption.

A disposable profile test passed fresh provisioning and migration of an existing
account from the retired palette, while preserving its own wallpaper file and
transparency setting. Linux launcher shebangs are checked for Windows line endings
before image assembly and again inside the final ISO.

Desktop uses 0.2.3; artwork and Terminal use 0.2.2. Appearance was tested as a real GTK window on the installed system and final live image: all four pages opened, the eight installed theme entries were present, and Black & White apply followed by Neon restore passed. The walking-figure wallpaper family was rebuilt from one cleaned master with the approved SR insert; Professional is unbranded. The image checker verifies matching artwork/desktop copies of all eight variants. Signed HTTPS APT acceptance and a downloaded 0.2.2 package hash were verified.

Final release SHA256: `7c53bbca05ff84841b381941c87d8a258800a465347b192a19efd00ae3cb2c73`. Both cold BIOS and UEFI boots of these exact bytes passed installer preflight, two restored online CPUs, early Btrfs preload, no soft-lockup messages, and signed APT acceptance. UEFI checks used the temporary test SSH connection; BIOS and UEFI installer readiness were observed locally; runtime checks used temporary live-session SSH. Temporary test access was added only to the volatile live overlay, not the ISO.
