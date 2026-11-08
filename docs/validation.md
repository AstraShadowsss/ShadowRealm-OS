# 2026.11 beta 1 validation

Image: `ShadowRealm-OS-2026.11-beta1-amd64.iso`  
SHA256: `0a182f8bfeba40084541be37fd335bb8f7db8aebbf64d7e5b47aba569b9fe9c6`

Checks performed on the AMD64 release build and its disposable VirtualBox test installation:

| Check | Result |
| --- | --- |
| ISO internal hashes, BIOS/UEFI boot entries, initramfs and boot maintenance packages | Passed |
| Fresh first-login appearance | Passed on the preceding boot-tested candidate: xfwm theme ShadowRealm-OS-Neon and GTK4 prefer-dark, without applying a theme manually |
| Factory privacy scan: saved accounts, private keys, network secrets and history | Passed |
| Corresponding-source archive | All 3,819 required Debian source inputs present; separate vendor sources retained |
| Package notice coverage | 2,027 installed packages; 2,218 notice files; no missing package notice records |
| BIOS live boot | Passed on the preceding candidate; default SR theme, dock and widgets loaded |
| UEFI live desktop and Calamares installation to a blank virtual disk | Passed; 38 installer jobs completed |
| Encrypted installed system: GRUB unlock, login and sudo | Passed |
| Desktop shutdown | Passed through the desktop power control |
| Installed services | No failed system services observed; NetworkManager, firewall and AppArmor active |
| AppArmor on installed system | 123 profiles loaded; 21 enforcing at the validation checkpoint |
| Eight appearance themes | Applied successfully; Neon restored; Gold SR accents and Professional Bluetooth rechecked |
| Menu icon routing | Project entries use the dock’s 48px artwork; third-party applications resolve native icons |
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

The installation test began with the preceding candidate of the same Debian/kernel/installer build, and received the final desktop, artwork, Terminal and experience packages. The final ISO was rebuilt from the clean factory root after those fixes. New installer defaults include the SR account avatar, ten-minute screensaver timeout, explicit Neon window-manager theme and native GTK4 dark preference. A fresh live-account settings window showed the SR avatar. The preceding candidate passed a fresh BIOS live boot with the installed test disk detached. The final image then received menu icon routing, background opacity defaults, clock shortcut routing and project notice corrections; those desktop changes were tested in the installed VM, and the rebuilt ISO passed structural, privacy and internal checksum checks. The final byte-for-byte image was not booted again.

## Limits

This is a beta, not a claim that every application and hardware combination is bug-free. No physical-machine, Secure Boot, shared-ESP dual-boot, suspend/resume or real Bluetooth-radio certification was performed. A USB Bluetooth adapter must be available to a VM before radio functions can be tested. GNOME/GTK4 vendor applications retain their native interface; light/dark preference follows the selected theme.

Debian's AppArmor service condition skips enforcement in the live overlay environment; the installed encrypted system was verified enforcing profiles. A signed custom ShadowRealm-OS update repository has not been published. Debian/vendor package updates and custom component maintenance are separate.

Notice coverage checks verify supplied files and inventories, not a legal certification of every upstream license. Matching corresponding source and retained notices are supplied with the release.
