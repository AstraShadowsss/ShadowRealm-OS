# Release notes

## 2026.11 beta 1

### Revised initial build (r2)

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
