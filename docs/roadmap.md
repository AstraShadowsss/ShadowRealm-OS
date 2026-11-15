# ShadowRealm-OS roadmap

ShadowRealm-OS is a Debian 13 and Xfce desktop with a recognizable visual identity, understandable system controls, and optional tools users can choose for themselves.

## Beta reliability

- Investigate the community report of an empty Processes widget. Compare the exact published r4 live session and a fresh installed account across several refreshes, locales and restarts. Check on physical hardware when available.
- Run a clean r4 installation and check first login, disk unlock when encrypted, graphical startup, Terminal, updates and normal shutdown. Record exact images and environments.
- Make first login consistently show the intended desktop. Test the display, audio, Wi-Fi, Bluetooth and suspend behavior on representative hardware. Verify Secure Boot separately.

## Control Center and professional theme

- Give the Control Center clear sections for Appearance, Desktop, Devices, Network, Privacy & Security, Accounts, and Software & Updates. Use the existing tools and eliminate duplicate routes where they add confusion.
- Show current state at the point of action. Explain whether Bluetooth is off or an adapter is missing and why an administrative action failed. Provide visible keyboard focus, readable toggle labels, and clear confirmation for changes that can interrupt connectivity.
- Use a consistent layout across Professional and Neon. Refine spacing, type, selection and focus states in Professional. Check small displays and larger text, then check the same screens in both themes.
- Complete dock editing and widget customization. Keep desktop shortcuts reorderable and removable. Add optional clock and calendar displays before externally backed weather or search.

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
| Control Center | Redesign the landing page and carry over the existing settings | Find common tasks by keyboard and mouse in Professional and Neon at small and large scales |
| Dock | Drag launchers to reorder them in place. Drop shortcuts from the desktop or Applications menu at the desired position. Expand the dock as items are added. | Verify drop placement, launching, removal, and saved order across logins and upgrades |
| Widgets | Add per-widget colors, readable scaling, placement and opacity controls | Text stays legible and independently configurable across themes |
| Clock and calendar | Add optional desktop widgets that use local time and the existing calendar workflow | Check time zone, date rollover, sizing and keyboard access |
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
