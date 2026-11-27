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
| 24 | Check installer checkbox/focus/disabled states in supported themes. | **Partial** | Installer CSS covers progress bars, checkboxes, radio buttons, disabled and focused controls. It has not been re-inspected from a real r5 ISO in every palette. |
| 25 | Repeat fresh ordinary and encrypted UEFI installation of the next candidate: account creation, unlock, graphical login, updates, restart and shutdown. | **Not done for r5** | r4 passed an encrypted UEFI install and restart; that evidence does not cover r5. Blocked on an ISO builder and installer test session. |
| 26 | Verify Secure Boot chain and module signatures in enrolled UEFI and physical hardware; investigate reported security violation. | **Open** | VirtualBox tests cannot establish this. Requires physical UEFI hardware with Secure Boot enrolled, `mokutil`/`sbverify` evidence and the reported violation's firmware logs. |
| 27 | Recheck DNSCrypt startup/effective resolver/reconnect/reboot/leaks/failure on hardware. | **Partial** | r4 software checks showed the resolver switching to the local DNSCrypt listener and no outbound port-53 traffic. r5 and hardware reconnect/reboot tests are outstanding. |
| 28 | Reproduce optional Docker firewall forwarding problem; scoped DNS/NAT/bridge/published-port support without global forwarding. | **Implemented, runtime test open** | Security 0.2.1 accepts `docker0`/`br-*` traffic, established/related traffic and root-published DNAT ports; the forward policy remains `drop`. `nft -c` syntax passed. Docker is not installed in the guest, so published-port and embedded-DNS behavior still needs a Docker runtime test. |
| 30 | Repeat APT upgrade/autoremove/dependency/startup recovery simulations; do not switch the main distribution to testing or add dummy packages. | **Not rerun for r5** | r4 upgrades, the desktop package audit and GNOME Keyring policy upgrade passed. Re-run on r5: `apt update`, upgrade/autoremove plans, simulated interrupted upgrade, signed-feed failure and recovery, and a no-custom-package-upgrade check on a fresh install. |
| 31 | Add dismissible/reopenable first-run summary of installed software, active services, network behavior and update sources. | **Implemented; installed-image check open** | `shadow-first-run` shows the summary and remembers dismissal. A new **Welcome Summary** menu entry runs it with `--force`. View it from a fresh r5 install and confirm its network/service text matches the image. |
| 32 | Verify latest boot/login/GRUB/Plymouth art visually; fix GRUB contrast over light artwork and check animation, beyond asset-path checks. | **Open** | No r5 ISO exists to inspect. The GRUB background and menu assets still need a real BIOS/UEFI boot check, including light artwork contrast, Plymouth animation and late-shutdown notice. |
| 33 | Check app menu. | **Partial** | The menu/classifier tests cover mixed categories and duplicate avoidance. The new Messenger and Welcome Summary entries need a live r5 menu check, including the shared icon in menu, dock and desktop. |
| 35 | Build next ISO after release gates; clean rebuild, exact matching sources/notices/checksums and private-data exclusion. | **Blocked** | The package set is staged, but the guest cannot run live-build or create the ISO; a root-capable builder and `/mnt/shadowrealm-build` are required. Do not publish until checks 23–33 pass. |
| 39 | Audit default outbound traffic/services with opt-in features disabled; improve DNS/VPN/Tor/MAC and application-permission controls with clear persistence/failure/user control. | **Not rerun for r5** | Previous data-capture checks covered DNSCrypt, Weather opt-in, Tor separation and no analytics. Re-run a fresh-install outbound audit with Telemetry/Weather/Tor/Flatpak autoupdates disabled, then review DNS, VPN, Tor, MAC and per-application permissions. |

## Package set staged for the builder

- desktop 0.2.21 (includes the dock shelf and Welcome Summary entry)
- terminal 0.2.3
- artwork 0.2.6 (reuse the built package; do not rebuild from the incomplete source archive)
- panel 0.2.1
- security 0.2.1 (scoped Docker forwarding)
- experience 0.2.0
- installer settings 0.2.2
- release 2026.11-4
- archive keyring 2026.11-2
- nine game packages
- Messenger 0.1.0 development preview

## Publication blockers

- No SourceForge credentials: the two current DEBs in the release folder cannot be moved or removed by this session. They are not signed updates.
- No APT signing credentials: desktop 0.2.21, security 0.2.1 and Messenger 0.1.0 cannot be published to the signed feed.
- No root-capable ISO builder: r5 cannot be built or installed here.

Do not describe the dock shelf, Messenger or the Docker forwarding path as
published until the signed feed and a fresh image are verified.
