# ShadowRealm-OS

A Debian 13 desktop with its own look, built around Xfce and a set of small, integrated desktop tools.

<p align="center"><img src="branding/banner-neon.png" alt="ShadowRealm-OS — SR logo and wordmark" width="880"></p>

**2026.11 beta 1 · AMD64 · live desktop and installer**

![ShadowRealm-OS desktop](screenshots/desktop.png)

ShadowRealm-OS keeps the familiar Linux desktop: applications, files, a terminal and a package manager. Its custom panel, dock, widgets and Control Center bring the everyday controls together. Eight coordinated styles range from Neon and Hacker to White, Silver & Gold and a quieter Professional theme. Wallpapers can be changed separately.

## Download and install

[Download the beta ISO](https://sourceforge.net/projects/shadowrealm-os/files/2026.11-beta1/ShadowRealm-OS-2026.11-beta1-r4-amd64.iso/download) · [Checksums](https://sourceforge.net/projects/shadowrealm-os/files/2026.11-beta1/SHA256SUMS/download) · [Licenses & source-download guide](https://sourceforge.net/projects/shadowrealm-os/files/2026.11-beta1/)

Check the ISO against `SHA256SUMS` before writing it to a USB drive or attaching it to a virtual machine.

The AMD64 ISO starts a live desktop so you can try it before installing. Open **Install ShadowRealm-OS** to install to a disk. The installer supports BIOS and UEFI systems and offers disk encryption. Back up your files first; choosing to erase a disk deletes its contents.

- [Install on a PC or in VirtualBox](docs/installation.md)
- [System requirements and test limits](docs/system-requirements.md)
- [Desktop, software and updates](docs/user-guide.md)
- [Build from source](docs/build-guide.md)

## Included

- Custom application menu with categories, favorites and adjustable sizing; editable dock and desktop shortcuts.
- Coordinated GTK, window, icon, terminal, login and boot artwork using the SR identity.
- Control Center for appearance, accounts, network, audio, Bluetooth and system tools. Hardware controls depend on the available device and driver.
- Debian APT packages, signed LibreWolf and Jami repositories, and Flatpak support.
- LibreWolf, Thunderbird, LibreOffice, VLC, Thunar, Mousepad and other desktop applications. See the release package inventory for exact versions.
- Shadow Shield controls for the firewall and privacy tools, plus AppArmor policies. These tools do not make a system anonymous or immune to attacks.
- Drawing for simple painting; GNOME Clocks for alarms, timers, world clocks and stopwatch.
- Customizable login backgrounds, optional original session chimes and three screensaver animations with standard XFCE locking.
- Nine offline games, including Shadow Pinball, Skull Invaders, Shadow Runner, Circuit Chase, Snake, Shadow Spider Solitaire, Neon Ascent, Neon Breaker and Marble Reactor. Scores and settings stay local.

**Desktop 0.2.14** fixes Encrypted DNS reporting success before the resolver switches. Recent signed updates also include Local Search, stable widget placement, refreshed circuit corridor wallpapers, and drag-and-drop dock editing. Install them through Software & Updates. [Release notes](CHANGELOG.md)

## Screenshots

### Wallpaper collection

![Red and Black, Black and Blue, Neon, and Hacker with four different wallpapers](screenshots/wallpaper-styles.png)

### Seated City

![Six colors of the Seated City wallpaper](screenshots/seated-theme-styles.png)

### Control Center

![Searchable Control Center in Neon](screenshots/control-center-neon.png)

![The same Control Center in Professional](screenshots/control-center-professional.png)

### Widgets and system tools

| Clock | Calendar | Notes |
| --- | --- | --- |
| ![Clock widget showing the time](screenshots/widget-clock.png) | ![Calendar widget showing the month](screenshots/widget-calendar.png) | ![Notes widget showing saved notes](screenshots/widget-notes.png) |

![Separate Clock, Calendar and Notes widgets alongside their settings](screenshots/widget-settings-professional.png)

![System Overview, Network, Processes and Shadow Shield](screenshots/widgets.png)

![Network, Shadow Shield and Software & Updates](screenshots/system-tools.png)

[Desktop widgets guide](docs/widgets.md)

### Apps and games

![Application menu](screenshots/application-menu.png)

![The nine games in action](screenshots/games-in-action.png)

## Shadow Games for Android

Play nine offline games with touch controls on Android. [Download the APK](https://github.com/AstraShadowsss/ShadowRealm-OS/releases/tag/shadow-games-android-v1.0.0) or see the [installation guide and screenshots](docs/shadow-games-android.md).

## Beta status

This is an early public release. Installation and desktop checks are documented in [release validation](docs/validation.md). Physical hardware coverage is limited; test your graphics, sound, wireless and suspend behavior from the live desktop. Secure Boot and dual-boot installations are not certified for this beta. Keep a backup and recovery media.

See the [project roadmap](docs/roadmap.md) for the Control Center redesign, desktop customization, and optional tools. If the Processes card stays empty, the [widget guide](docs/widgets.md#if-the-processes-card-stays-empty) explains what to include in a report.

Debian and configured vendor repositories provide their package updates. The revised Beta 1 image also includes the signed ShadowRealm-OS repository for custom desktop components and games. Refresh Software & Updates to see available APT updates; installing them remains your choice. Flatpak applications update separately. See [repository details and setup for the earlier image](docs/update-repository.md).

## Source and licenses

Original project work is supplied under the [MIT license](LICENSE). Linux, Debian packages, the modified Xfce panel, libraries, firmware, fonts and adapted icons retain their own licenses; they are not relicensed as MIT. See [third-party licensing and source availability](THIRD_PARTY_LICENSES.md).

This repository contains the custom source, configurations, artwork masters and build recipes. The ISO and matching third-party source distribution belong on SourceForge, outside Git history. Personal files and VM disks are not part of this repository.

[Report a bug](https://github.com/AstraShadowsss/ShadowRealm-OS/issues) · [SourceForge](https://sourceforge.net/projects/shadowrealm-os/)

Created and maintained by AstraShadows
