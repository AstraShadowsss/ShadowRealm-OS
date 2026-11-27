# Validation history

## r5 development checkpoint (27 November 2026)

This is not a released image. No r5 ISO has been built or installed. Package and desktop checks below were run in the disposable Debian 13 VirtualBox guest; installer, Secure Boot and physical-hardware gates remain open.

### Shadow Messenger

The native client built without warnings, and the ordinary Rust tests passed. The GUI was exercised against the isolated loopback Synapse fixture: test-account login, an encrypted direct invitation accepted by a second profile, encrypted send/receive between two accounts, Presence selection, a custom away message, the Activity feed, normal and mention notifications, Do Not Disturb suppression, saved-account restore, message persistence after restart, Preferences, Devices & Security, and recovery-key setup. The notification click action did **not** open the conversation. The notification now also carries an explicit **Open** action button, and the session notification daemon reports the `actions` capability; a fresh click test is still required. The full test suite is still flaky when run in one process, while the ignored integration and theme tests pass individually.

### Themes and icons

All twelve live palette windows passed the palette test, including Black/Blue, Black/White, Hacker, Neon, the four Professional variants, Purple/Black, Red/Black, White/Silver/Gold and Woodland. The signed-out/signed-in menu-bar text colours were corrected. A new `shadow-messenger-app` chat-bubble icon was generated for every palette and visually inspected in a contact sheet; the release package installs it under a package-owned name to avoid colliding with the artwork package. The development launcher was pointing at a fixed email-icon path, which explains category icon fallbacks in the menu; the packaged launcher now uses the shared theme icon.

### Firewall and Messenger

Shadow Shield keeps inbound and forwarded traffic denied by default and allows outbound traffic. Messenger is an outbound HTTPS/WebSocket client, so this policy does not block normal sign-in or sync. Docker is optional and not installed in the image; its bridge and published-port path was the unresolved exception. Security 0.2.1 adds scoped forwarding for `docker0`/`br-*`, established/related traffic and root-configured DNAT published ports, while the forward policy remains `drop`. The nftables rules passed `nft -c` syntax validation; a running Docker engine was not available for an end-to-end test.

### Installer and first run

A pre-installer guidance window now covers disk erasure, encryption recovery and media removal. The first-run Welcome Summary is dismissible and can be reopened from the application menu. Neither has been viewed from a fresh r5 ISO. Existing r4 validation remains the only completed install evidence.

### Package and disk state

Current r5 packages staged in `/var/tmp/r5-out`: desktop 0.2.21, Terminal 0.2.4, artwork 0.2.6, panel 0.2.1, security 0.2.1, experience 0.2.0, installer settings 0.2.2, release 2026.11-4, archive keyring 2026.11-2, all nine games and `shadowrealm-os-messenger` 0.1.0. Regenerable `/var/tmp` build and test directories were removed, reclaiming about 6 GB; the Synapse fixture and account data were kept. The VM still has no root access, live-build, xorriso, mksquashfs, debootstrap or the expected build volume.

### Release-folder audit

The desktop 0.2.20 and Terminal 0.2.3 DEBs that had been uploaded to the SourceForge 2026.11-beta1 folder were removed; the folder now holds the ISO, checksums, notices, source material and the archive-keyring package the ISO ships. The signed feed supplies the current versions of every custom package.

### Dock shelf

The dock shelf code is present in desktop 0.2.21, which the signed feed now publishes, so installed systems receive it through Software & Updates. Direct dragging, edge drops, multi-monitor behavior and final polish were not rechecked for r5.

## 2026.11 beta 1 r4 validation

First-login wallpaper follow-up: desktop package 0.2.4 installed over 0.2.3 in the r4 test VM and passed the package audit. On a new account, the packaged wallpaper was selected 5 seconds after the Xfce test timer started and the widget process appeared at 100 seconds. The test measured one VirtualBox configuration. It confirms that the wallpaper can load early and that widget startup still needs separate work.

The follow-up desktop package 0.2.5 installed over 0.2.4 and passed the package audit. On another fresh account in the same VM, the widget process appeared at 26 seconds and the packaged wallpaper was selected at 28 seconds after its Xfce test timer started. The desktop showed all four panels with live process rows. These are individual runs and startup time varies with the host workload. The signed APT feed serves the tested package.

On 15 November 2026, the r4 ISO matched its published SHA-256. A fresh VirtualBox live boot and a clean unencrypted UEFI installation both showed PID, command, CPU and memory rows. The installer finished, the media removal prompt appeared, and the installed account reached the themed desktop and opened Terminal. The first login temporarily showed the stock Xfce wallpaper before the branded desktop and widgets appeared. The blank Processes card was not reproduced in these tests.

Image: `ShadowRealm-OS-2026.11-beta1-r4-amd64.iso`  
SHA256: `4ba996ac5c690d88cfb5d8b401b9fdf6ec0984b7d2cf03d9c5c73837e5355655`

## R4 targeted correction

Artwork 0.2.3 separates interactive splash notices from service-status text. In a live session only, a late-shutdown helper releases Plymouth to a readable console so the installation-media removal/Enter instruction cannot remain hidden. Installed systems keep their themed shutdown. The new helper is restricted to `boot=live`.

The exact r4 image passed internal checksums, BIOS/UEFI boot-entry checks, root permission checks, factory privacy and all eight theme catalogs. A fresh live boot and actual late live-media shutdown/restart handoff were checked, including visible instructions and Enter continuation. Current notice coverage accounts for 2,028 packages and 2,219 notice files.

## Encrypted UEFI installation

A fresh VirtualBox install from the checksum-verified r4 ISO used Calamares automatic partitioning with encryption enabled. Calamares completed, the media-removal prompt was readable, and pressing Enter once continued to GRUB. A brief live-media unmount warning appeared before restart. The installed system accepted the disk passphrase, reached the graphical login screen, and accepted the account password. The root filesystem was mounted on a LUKS mapper, the branded desktop and live widgets loaded, and no system units were in the failed state before updating.

On that encrypted installation, **Software & Updates → System Updates → Install Debian Updates** completed with exit code 0. The transaction applied 58 upgrades, installed one new kernel package and removed zero packages. ShadowRealm-OS desktop advanced from 0.2.3 to 0.2.11 and artwork from 0.2.3 to 0.2.4. The package audit was clean, the desktop package was marked manually installed, and no system units were in the failed state. Restarting from the desktop accepted the disk and account passwords again. Terminal and the live widgets worked on the updated kernel, 6.12.117+deb13-amd64, with the root filesystem still encrypted.

## Dock display checks

Panel 0.2.1 reordered launchers at 800 × 600 and accepted a desktop shortcut while the dock was set to always hide. The shortcut appeared in the dock configuration after confirming its placement. In a separate XRandR layout with two logical regions, the dock stayed on the primary region and could reveal and reorder launchers. A second independent VirtualBox output did not activate in this live session. Physical multi-monitor and hot-plug checks remain open.

## Local Search

Desktop 0.2.13 built and installed over the r4 baseline in a disposable Debian 13/Xfce live session. The package audit was clean. The application menu launched Local Search, a test file in Documents appeared and opened in Mousepad, and Find Settings passed the query to the existing Control Center. A search against the live filesystem also verified that ordinary files are found when their filesystem metadata differs from the parent directory.

## Limits

This is a beta. Physical hardware, Secure Boot, shared-ESP dual boot, suspend/resume and real Bluetooth-radio certification remain unperformed. First sign-in prepares per-user artwork and can briefly show the Xfce background. Matching source and third-party notices accompany the release; notice-file coverage is not legal certification.

## Encrypted DNS on installed r4

A fresh UEFI installation from r4 booted from disk in VirtualBox. Before changing the DNS setting, a lookup used ordinary DNS despite the DNSCrypt service running. Desktop 0.2.14 installed cleanly over the bundled desktop package. Its DNS control switched the system resolver to the local DNSCrypt listener before returning success. The next lookups resolved, and a separate capture contained HTTPS upstream traffic and zero outgoing TCP or UDP port 53 packets.

## Weather on installed r4

Desktop 0.2.15 installed cleanly on a fresh r4 VirtualBox guest booted from disk. Weather stayed off after saving a location. In the test capture, traffic to the forecast provider appeared only after enabling Weather and again after reconnecting the guest. The widget displayed a forecast, showed a cached forecast with an offline label when the network was disconnected, and refreshed on reconnection. Disabling Weather hid the card.

## Desktop 0.2.16 / artwork 0.2.5 / Terminal 0.2.3

The three packages installed over the previous private candidates in the Debian VM with a clean dpkg audit. The package-owned per-user asset migration completed, all 12 palette boot/login/default-wallpaper paths resolved, and the Professional boot-image regeneration completed successfully. The visible dock followed the move control and returned to its original order. The installed Terminal and Control Center launched. Professional desktop and Control Center screenshots were captured from the installed packages.

These checks do not constitute a new ISO installation, a fresh encrypted-install test, Secure Boot certification or physical-hardware coverage. Those remain separate release gates.

## Game progression update

Marble Reactor passed twelve distinct bounded tracks and all twelve completion transitions. Spider passed sixty seeded deals, legal stack moves, undo, card conservation and a completion transition. Circuit Chase passed objective reachability and direction-pad/swipe input checks. Skull Invaders passed weapon, shield, repair and three-boss progression checks plus twelve seeded movement/firing simulations. These rule tests passed in Debian and in the portable Windows runtime. Native GTK views of the three changed games were also inspected and captured.

Eight shared-runtime game packages were accepted and installed from the public signed APT feed in the reference VM; dpkg audit was clean. Full manual playthroughs of all nine games and the Android changes are still separate checks. The installer remains r4.

## Android 1.0.1

The APK built with version code 2 and the same signing certificate as 1.0.0, and installed over the previous preview. All nine games rendered in the installed Android emulator app. Touch-control bounds and playfield separation, Pinball simultaneous flippers and centered Launch, Spider stack dragging, pause and native Back navigation passed with no uncaught JavaScript errors. Rule tests cover Snake wrapping and buffered input, Spider card conservation/moves/undo/completion, all twelve distinct Marble tracks and final-stage completion, enemy/boss/power-up transitions, reachable maze objectives and finite Pinball physics with a three-ball limit.

The public APK was downloaded and its SHA-256 matched the tested local artifact. Ten new captures accompany the Android guide. Physical-phone and older-WebView coverage, audible output and longer manual playthroughs remain outstanding. The emulator had intermittent System UI stalls outside the game; the completed app test did not record a game crash. Android publication does not change the r4 Linux image.
