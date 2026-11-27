# r5 installer and release findings

Status as of 27 November 2026. This is a private development checklist, not a
release announcement. No r5 ISO exists yet and nothing here authorises
publication.

## Build and test environment

- The disposable Debian 13 guest has no usable root path for this session.
  `sudo` is not available to the agent, root SSH is denied, and live-build,
  xorriso, mksquashfs, debootstrap, the Xfce development libraries and
  `/mnt/shadowrealm-build` are absent.
- Current packages are staged in `/var/tmp/r5-out`; the package sources are
  under `components/`, `games/` and `messenger/`.
- Regenerable build/test directories in `/var/tmp` were removed, reclaiming
  about 6 GB. The Synapse fixture and its accounts were deliberately kept for
  further Messenger checks.
- The image must be built on a root-capable Debian 13 builder. Do not publish
  an ISO until the install gates below pass.

## Checklist

| # | Item | Status | Evidence / next action |
| --- | --- | --- | --- |
| 23 | Investigate reported hardware installer errors; clear progress/errors/completion, partition guidance, data-loss warning, LUKS/LVM and separate account/unlock passwords, media removal and first restart. | **Open** | A pre-installer guidance window now states that erase deletes the disk, warns about manual partitioning, explains a separate encryption passphrase and recovery key, and tells the user to remove media before the first boot. Calamares still needs a fresh hardware reproduction with the original error logs; no r5 ISO has been booted. |
| 24 | Check installer checkbox/focus/disabled states in supported themes. | **Re-inspected; ISO check open** | `release/check-installer-states.py` renders `usr/share/shadowrealm-os/installer.qss` from installer settings 0.2.2 in a real Qt window. Unchecked, checked, disabled and focused controls are distinct: cyan borders on enabled fields, magenta fill on checked boxes and radio dots, grey borders and labels when disabled, and a cyan progress chunk. The installer uses one fixed dark stylesheet for every desktop palette, so the states do not change with the theme; the GTK guidance window follows the selected palette. Still to view from a booted ISO. |
| 25 | Repeat fresh ordinary and encrypted UEFI installation of the next candidate: account creation, unlock, graphical login, updates, restart and shutdown. | **Not done for r5** | r4 passed an encrypted UEFI install and restart; that evidence does not cover r5. Blocked on an ISO builder and installer test session. |
| 26 | Verify Secure Boot chain and module signatures in enrolled UEFI and physical hardware; investigate reported security violation. | **Open** | VirtualBox tests cannot establish this. Requires physical UEFI hardware with Secure Boot enrolled, `mokutil`/`sbverify` evidence and the reported violation's firmware logs. |
| 27 | Recheck DNSCrypt startup/effective resolver/reconnect/reboot/leaks/failure on hardware. | **Partial** | r4 software checks showed the resolver switching to the local DNSCrypt listener and no outbound port-53 traffic. r5 and hardware reconnect/reboot tests are outstanding. |
| 28 | Reproduce optional Docker firewall forwarding problem; scoped DNS/NAT/bridge/published-port support without global forwarding. | **Implemented, runtime test open** | Security 0.2.1 accepts `docker0`/`br-*` traffic, established/related traffic and root-published DNAT ports; the forward policy remains `drop`. `nft -c` syntax passed. Docker is not installed in the guest, so published-port and embedded-DNS behavior still needs a Docker runtime test. |
| 30 | Repeat APT upgrade/autoremove/dependency/startup recovery simulations; do not switch the main distribution to testing or add dummy packages. | **Partial; fresh-image run open** | On the installed r4 image with current indexes, `apt-get -s upgrade` plans only desktop 0.2.21 and security 0.2.1, and `release/tests/check-desktop-apt.sh` passes dist-upgrade, autoremove and the network-manager-gnome removal. `release/tests/test-apt-rejection.sh` rejects unsigned, altered, expired and byte-modified metadata. Still to run a real upgrade and the same checks on a fresh r5 install. |
| 31 | Add dismissible/reopenable first-run summary of installed software, active services, network behavior and update sources. | **Implemented; installed-image check open** | `shadow-first-run` shows the summary and remembers dismissal. A new **Welcome Summary** menu entry runs it with `--force`. View it from a fresh r5 install and confirm its network/service text matches the image. |
| 32 | Verify latest boot/login/GRUB/Plymouth art visually; fix GRUB contrast over light artwork and check animation, beyond asset-path checks. | **Open** | No r5 ISO exists to inspect. The GRUB background and menu assets still need a real BIOS/UEFI boot check, including light artwork contrast, Plymouth animation and late-shutdown notice. |
| 33 | Check app menu. | **Live check passed; r5 image check open** | Menu/classifier tests cover mixed categories and duplicate avoidance. The menu was opened live on the r4 desktop with the r5 packages: Favorites lists Shadow Messenger with the same envelope-plate icon as the theme's mail application, the desktop entry and the conversation window icon share the file, and the renamed launcher no longer shows a development title. Welcome Summary still needs the same pass on a booted r5 image. |
| 35 | Build next ISO after release gates; clean rebuild, exact matching sources/notices/checksums and private-data exclusion. | **Blocked** | The package set is staged, but the guest cannot run live-build or create the ISO; a root-capable builder and `/mnt/shadowrealm-build` are required. Do not publish until checks 23–33 pass. |
| 39 | Audit default outbound traffic/services with opt-in features disabled; improve DNS/VPN/Tor/MAC and application-permission controls with clear persistence/failure/user control. | **Not rerun for r5** | Previous data-capture checks covered DNSCrypt, Weather opt-in, Tor separation and no analytics. Re-run a fresh-install outbound audit with Telemetry/Weather/Tor/Flatpak autoupdates disabled, then review DNS, VPN, Tor, MAC and per-application permissions. |

## Package set staged for the builder

- desktop 0.2.21 (includes the dock shelf and Welcome Summary entry)
- terminal 0.2.4 (tabs and Ctrl+V paste)
- artwork 0.2.6 (reuse the built package; do not rebuild from the incomplete source archive)
- panel 0.2.1
- security 0.2.1 (scoped Docker forwarding)
- experience 0.2.0
- installer settings 0.2.2
- release 2026.11-4
- archive keyring 2026.11-2
- nine game packages
- Messenger 0.1.0

## Publication blockers

- The two loose DEBs that were in the release folder (desktop 0.2.20 and terminal 0.2.3) were removed. Their contents are superseded by the signed feed, which now carries desktop 0.2.21, terminal 0.2.4, installer settings 0.2.2, security 0.2.1 and Messenger 0.1.0.
- The signed feed is published and verified: `apt-get update` accepts `InRelease`, `apt-get download` returns Messenger 0.1.0 with the expected SHA256, and `apt-cache policy` candidates resolve to desktop 0.2.21, installer settings 0.2.2 and security 0.2.1. The index is valid until 25 February 2027; `release/build-apt-repository.py` now defaults to a 90-day window so a rebuild cannot silently return to the old 14 days.
- No root-capable ISO builder: r5 cannot be built or installed here.

The signed feed is verified; the dock shelf, Messenger and the Docker forwarding
path still need a pass on a fresh image before they are described as released.
