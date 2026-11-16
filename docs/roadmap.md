# ShadowRealm-OS roadmap

ShadowRealm-OS is a Debian 13 and Xfce desktop with a recognizable visual identity, understandable system controls, and optional tools users can choose for themselves.

## Beta reliability

- Investigate the community report of an empty Processes widget. Compare the exact published r4 live session and a fresh installed account across several refreshes, locales and restarts. Check on physical hardware when available.
- Repeat the clean live and installed checks on additional VirtualBox configurations and physical hardware. The [validation notes](validation.md) cover the tested r4 unencrypted and encrypted UEFI installations.
- Make first login consistently show the intended desktop. Test the display, audio, Wi-Fi, Bluetooth and suspend behavior on representative hardware. Verify Secure Boot separately.

## Desktop and system controls

Desktop 0.2.12 includes searchable settings, the updated Professional theme, movable and resizable widgets, independent Clock and Calendar, saved Notes, and a dock auto-fit control. These are available through signed APT updates.
- Show current state at the point of action. Explain whether Bluetooth is off or an adapter is missing and why an administrative action failed. Provide visible keyboard focus, readable toggle labels, and clear confirmation for changes that can interrupt connectivity.
- Check the settings on smaller displays and with larger text. Carry the same focus and status conventions into the remaining system windows.
- Keep the dock's drag-and-drop behavior consistent on smaller displays. Add local search and make any online weather lookups optional.

## Transparency and optional tools

- Design a dismissible first-run screen that summarizes what is installed, which services are active, and what network access users should expect. Link to the full package list and explain update sources.
- Extend the existing Shadow Shield where useful. Test DNS and MAC privacy settings against real connection behavior and show the limits of each setting.
- Offer optional gaming, development and container profiles with clear package sources, service changes and uninstall behavior. Evaluate Steam, Proton and Linux controller support independently of the built-in games. Evaluate rootless containers as an optional development setup.
- Keep source, release checksums, signed package metadata, build instructions and supporting notices aligned. Test rebuilds from a clean environment before claiming reproducibility.

Disposable sessions and stronger isolation are longer-term research. They need their own threat models and verification before they become product features.

## Implementation checklist

| Work | First deliverable | How to check it |
| --- | --- | --- |
| First login | Apply the branded wallpaper early and show a clear state while optional setup finishes | Time a first login and a later login on a fresh account |
| Control Center | Check keyboard navigation, smaller displays, and large text across themes | Find and open common tools without clipped controls |
| Dock | Check drag reorder and shortcut drops on smaller displays, a hidden dock and multiple monitors. | Verify drop placement, launching, removal, and saved order across logins and upgrades |
| Widgets | Check multi-monitor placement, time-zone changes, and large text | Widgets remain reachable after monitor changes, and user layouts and notes persist |
| Weather and search | Add a manual weather location and local app search, then evaluate file and online providers | Show which requests leave the device and allow the user to turn them off |
| First-run transparency | Summarize installed software, services and update sources with links to detail | Users can dismiss the screen, reopen it, and reach the relevant controls |
| Privacy controls | Audit outbound connections and add clear DNS, MAC randomization, permission and metadata controls where useful | Record what changes per connection, after reconnect and after reboot |
| Software profiles | Start with one optional profile and show packages, source, disk space and services | Install and remove it on a clean system while preserving personal data |
| Gaming | Validate Steam, Proton, Vulkan and representative USB and Bluetooth controllers | Record tested GPU and controller combinations and game compatibility limits |
| Containers | Prototype an optional Docker and Compose setup with rootless operation where supported | Explain access, ports and volumes, and preserve data on removal |
| Security research | Evaluate an optional isolated lab using a VM, with Kali as one possible guest | Check virtual networking and keep guest package repositories separate from the host |
| Hardware | Record physical graphics, Wi-Fi, Bluetooth, audio, webcam, peripherals, suspend and storage coverage | Publish results with hardware models and exact firmware/driver conditions |
| Secure Boot | Test an enrolled UEFI VM and selected physical hardware, including encrypted installation | Verify the boot chain and any driver-key enrollment requirements |
| Release engineering | Keep the signed APT update workflow, matching source and licenses, and evaluate signed ISO checksums | Rebuild on clean infrastructure and test that clients reject altered updates |
| Disposable sessions | Prototype explicit persistence and network boundaries | Test what survives shutdown and whether traffic follows the intended route |
| Compartmentalization | Assess isolated workspaces backed by virtualization | Document the threat model and test the boundaries before making privacy claims |
| Emergency data protection | Explore recovery and realistic storage guarantees before designing any destructive action | Review clear consent, backups and failure consequences before implementation |
