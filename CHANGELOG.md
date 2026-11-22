# Release notes
## Games update (2026-11-22)

- Marble Reactor 0.3.0: twelve distinct rounded tracks, varied entry angles and curvature, gradual color/speed progression, and a complete twelve-stage finish.
- Circuit Chase 0.2.0: swipe turns and an on-screen direction pad alongside keyboard controls; retain buffered turns and reachable objectives.
- Skull Invaders 0.2.0: three enemy types, three boss patterns, visible boss health, temporary shields, repair drops, and less frequent, shorter shot upgrades.
- Update the shared game runtime packages while retaining existing scores and settings.

Android gameplay changes are not included in this update.
## Desktop 0.2.17 (2026-11-22)

- Add Appearance → Icons & Dock to select an icon family independently of desktop colors and wallpapers, with a Follow desktop theme default.
- Keep Signature dock shapes and dark surfaces consistent across palettes; Professional accents share their own coordinated family.
- Correct the Bluetooth symbol and panel glyph scaling across all twelve palettes.
- Label Weather location and temperature-unit settings together. Fahrenheit and Celsius selections persist independently of the forecast cache.
## Desktop 0.2.16, artwork 0.2.5 and Terminal 0.2.3 (2026-11-22)

- Refresh the coordinated theme collection, including Purple & Black and four Professional accents with matching system, dock and panel icons.
- Replace retired Professional backgrounds with Satin Bloom, Flowing Glass and Sculpted Silk. Use the current artwork for login and GRUB, with theme-matched boot and shutdown logos.
- Correct dock Move left/right changes so the visible panel follows the saved order.
- Improve widget settings, theme opacity inheritance, Notes scrolling and network-rate labels. Add Fahrenheit/Celsius selection.
- Keep Terminal text readable in light themes and remove the unused logo space in Professional mode.
- Correct public package-file permissions when building with a restrictive file-creation mask.

The r4 installer is unchanged. Install the desktop updates through Software & Updates or APT.

## Desktop update 0.2.15

- Add an optional Weather widget with manually entered coordinates, forecasts from MET Norway, and a locally cached forecast for interrupted connections. Weather is off by default.

## Desktop update 0.2.14

- Wait for the active connection and system resolver to switch to DNSCrypt before confirming Encrypted DNS. Restore the previous settings if the switch fails.

## Desktop update 0.2.13

- Add Local Search for file names in a folder you choose. Open matches with their normal applications or send the same query to Control Center to find a setting.

## Desktop 0.2.12 and panel 0.2.1

- Keep neighboring widgets in place when moving or resizing a widget.
- Restore cyan and magenta throughout the Neon circuit corridor and extend the circuit traces toward the SR emblem across all seven branded palettes.
- Drag dock launchers to reorder them, or drop a shortcut from the desktop or Applications menu and confirm its placement.

## Desktop update 0.2.11 (2026-11-15)

- Split Clock and Calendar into independently positioned and configurable widgets.
- Add a Notes widget for saving local notes.
- Add a dock control that fits its length to the installed launchers.

## Desktop update 0.2.10 (2026-11-15)

- Move widgets by dragging their headers and resize them from the bottom-right corner. Each widget remembers its layout and can be reset from its context menu.
- Set separate colors for borders, text and numbers, usage bars, and history graphs.

## Desktop update 0.2.9 (2026-11-15)

- Add an optional desktop clock and monthly calendar.
- Set border color, background opacity and visibility for each widget.
- Enable widgets in Professional through an explicit preference.

## Desktop update 0.2.8 and artwork update 0.2.4 (2026-11-15)

- Organize Control Center into searchable settings sections and give Dock and Panel separate entries.
- Add dock size and visibility controls, with access to the launcher editor.
- Match the headers of the built-in settings windows and refine the Professional theme with softer colors, clearer controls and more consistent spacing.
- Fix refresh callbacks in Audio and Network that could run after their window closed.

These updates are distributed through the signed APT repository.

## Desktop update 0.2.6

- Depend directly on the NetworkManager applet and connection editor and declare the XFCE desktop components used at runtime.
- Mark the custom desktop as manually installed on newly built images and check APT upgrade and autoremove plans for desktop-stack removals.

See the [desktop package investigation](docs/desktop-upgrade-investigation.md).

## Desktop update 0.2.5 (2026-11-15)

- Start live widgets independently of the initial theme and wallpaper copy.

- Apply the shipped wallpaper before first-login profile setup copies themes, icons and wallpapers. Preserve wallpaper choices already saved by the user.

Open Software & Updates and refresh to find this update in the signed APT repository.

## 2026.11 beta 1 r4 — live-media handoff (2026-11-09)

- Give live-media removal notices a separate persistent display and expose the console during the late live-session shutdown handoff.
- Rebuild early boot artwork with the underlying initramfs tool when Debian's live wrapper is present.
- Preserve r3's root-permission and installer-mount fixes. The r4 ISO replaces r3 after targeted live-boot and handoff verification. The installer, account, partitioning and network code are unchanged.

## 2026.11 beta 1

### Installer correction (r3 — 2026-11-09)

- Corrected filesystem-root permissions in the ISO build. The r2 root was mode 0700, which prevented D-Bus and other unprivileged services from starting after installation and caused both graphical and console login sessions to fail.
- Added explicit root ownership/mode checks to ISO generation and validation, plus an installer finalization safeguard.
- Added a target-mount check before copying the live system, so a failed mount cannot silently fill the live session's temporary filesystem.
- Replaced the withdrawn r2 installer with r3 after a complete fresh UEFI encrypted installation and successful installed graphical login. Matching custom source, notices and checksums are supplied; the third-party source bundle is unchanged.

### Revised initial build (r2)

- Added a readable update-feed page and package catalog with links from the project website and download overview.
- Added SourceForge-specific download notes and moved the large third-party source bundle to six verified GitHub Release attachments to respect hosting limits.

- Fixed Appearance startup after the palette replacement; theme controls now read the installed manifest and were tested through every page.
- Normalized owned UI text and source line endings to prevent encoding artifacts.

- Replaced Blue & White with Black & White across desktop controls, icons, wallpapers, widgets and window decorations.
- Expanded current system, dock and panel families to 89 roles per theme; retained the existing dock artwork in the other seven styles.
- Reconciled the media export with the installed icon families and removed the old branded Professional wallpaper.
- Added enlarged widget explanations/captures and network, security, update and wallpaper galleries.
- Added a shared Neon SR logo/wordmark banner and a project website.
- Replaced the old walking-figure jacket emblem across the wallpaper family using one cleaned master and the exact SR insert; added an unbranded Professional variant.
- Corrected the menu sizing button's ellipsis text.

- Added the signed ShadowRealm-OS APT repository and its scoped public signing key, allowing custom component and game updates through Software & Updates/APT.
- Restricted that repository to ShadowRealm-OS packages; Debian and vendor repositories continue supplying their packages.
- Tested a signed package upgrade over HTTPS with existing user settings preserved, and verified rejection of unsigned, altered, expired and corrupt update content.
- Added repository build/publish tools, public-key setup instructions and maintenance documentation.
- Retained the Beta 1 release name; the r2 filename, build ID and new checksums identify the revised image.
- Fixed an old live-build identity file so standard system information reports ShadowRealm-OS and the current build ID.
- Added automatic VirtualBox filesystem-driver initialization to avoid installer startup stalls while restoring the guest's configured CPUs afterward; physical-machine CPU settings are unchanged.

- First ShadowRealm-OS beta edition of the Debian-based desktop.
- Unified SR logo, shared wordmark and coordinated palette assets.
- Renamed custom package, service, configuration and application identifiers.
- Live desktop and Calamares installer for AMD64 BIOS/UEFI systems.
- Integrated desktop utilities, nine offline Linux games and Debian package management.

See `docs/validation.md` for the checks performed on the final image and known limits. This is a beta, not a declaration that all hardware or applications are free of bugs.

### Final desktop polish

- Unified SR palette colors with the desktop theme manifest and regenerated role icons from their transparent SVG masters.
- Corrected Professional Bluetooth glyph and removed the hooded wallpaper retouch patch.
- Added synchronized account/login pictures, customizable greeter backgrounds, optional original session chimes and three XFCE screensaver animations.
- Added Drawing and direct access to GNOME Clocks alarms and timers.
- Added visible Terminal action feedback and native GTK4 light/dark preference switching.
