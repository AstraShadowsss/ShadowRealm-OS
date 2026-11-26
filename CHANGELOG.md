# Release notes

## Desktop runtime fix (2026-11-26)

- Replace the legacy split `shadow-link` wrapper left in the user runtime directory by older installs. Provisioning skipped existing files, so upgrades could keep launching the stale menu binary instead of the packaged one. Only that known runtime filename is replaced; unrelated custom files are preserved.

## Desktop 0.2.19+window1.icon1.clean3+refresh1+launch1 (2026-11-25)

- Activate applications asynchronously from the menu with a native launch context, so an application that starts through D-Bus presents its main window instead of a hidden one.
- Keep the menu alive until the launch finishes, and report a launch failure inside the menu rather than closing it.
- Apply coordinated window borders and GTK interaction styling across all twelve palettes. Vendor application icons stay native.
- Replace superseded factory icon artwork through a versioned migration. Unchanged factory files are updated; modified files, custom logos, launchers and wallpapers are preserved.
- Refresh the panel after a theme change so updated glyphs and styles appear without restarting the session.

## Shadow Icon Studio (2026-11-25)

- Add Shadow Icon Studio under Appearance → Icons & Dock.
- Import PNG, JPEG, SVG or WebP artwork, or load the artwork already installed for an application.
- Preview all twelve palettes, then apply the result to the menu, desktop and dock.
- Export SVG and the eight standard PNG sizes, batch export up to 100 source files, and export or import custom logo packs.
- Keep named personal icons separate from installed application overrides, and restore overrides individually or all at once.
- Include a built-in user guide. Local creation needs no network connection and no root access.
- Ship a 3,483-entry application catalog as identifiers and aliases only. Icon artwork is read from the applications already installed on the machine; no third-party logos are redistributed with the package.

## GNOME Keyring and repository policy (2026-11-25)

- Backport Debian's login-collection D-Bus registration correction as gnome-keyring, gnome-keyring-pkcs11 and libpam-gnome-keyring 48.0-1+shadowrealm1.
- Publish shadowrealm-os-archive-keyring 2026.11-2, which authorises the three keyring packages at priority 500 while keeping the restriction that stops the custom repository replacing unrelated Debian packages.
- Existing installations may need two update cycles: the policy package first, then the keyring packages. Sign out and back in, or restart, after the keyring update.

## In development — dock shelf

- Add an optional full-width dock shelf with centered launchers and a compact-layout switch.
- Preserve launcher order, size and visibility settings; keep structural spacing out of the editable launcher list.
- Restore the prior compact layout and background opacity when switching back.
- Local preview only; not yet included in the signed APT feed or r4 installer. Direct dragging, edge drops, multi-monitor behavior and final visual polish still need coverage.

## Shadow Games for Android 1.0.1 (2026-11-23)

- Equal Pinball flippers, centered Launch and working first-press/multitouch input.
- Keep landscape controls beside each game and repair selected-stack dragging in Spider Solitaire.
- Add twelve rounded Marble Reactor tracks and expanded Skull Invaders enemies, bosses and power-ups.
- Buffer quick Snake direction taps, fix Back navigation and stop game progression after fatal hits.
- Refresh Android screenshots and installation instructions. Preserve the existing app ID, signing certificate and local score storage.
- Validate all nine games in the installed emulator APK and run rule/progression checks. Physical-device coverage remains outstanding.

## Desktop 0.2.19 and artwork 0.2.6 (2026-11-23)

- Add Debian package removal to Software & Updates, with APT's interactive removal plan and an explanation for shared desktop tools.
- Restore the SR logo and wordmark on White, Silver & Gold's Circuit Corridor wallpaper.
- Refresh unchanged factory corridor copies while preserving custom backgrounds.
- Round panel buttons and notebook tabs consistently, and strengthen default light-theme text contrast.
- Apply the control styles to existing local theme copies without replacing their other edits.
- Exclude the retired HexChat add-ons from the next installer build.

## Desktop 0.2.18 (2026-11-22)

- Put Bluetooth power, device pairing and adapter preferences in one panel.
- Keep controller output and paired device addresses under a collapsed Technical Details section.
- Clearly distinguish unavailable, disabled and enabled Bluetooth states.

## Games update (2026-11-22)

- Marble Reactor 0.3.1: twelve distinct rounded tracks, varied entry angles and curvature, gradual color/speed progression, and a complete twelve-stage finish.
- Circuit Chase 0.2.1: swipe turns and an on-screen direction pad alongside keyboard controls; retain buffered turns and reachable objectives.
- Skull Invaders 0.2.1: three enemy types, three boss patterns, visible boss health, temporary shields, repair drops, and less frequent, shorter shot upgrades.
- Stop level progression and power-up collection after a fatal hit.
- Update the shared game runtime packages while retaining existing scores and settings.

The November 22 Linux update is separate from the Android 1.0.1 release above.
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
