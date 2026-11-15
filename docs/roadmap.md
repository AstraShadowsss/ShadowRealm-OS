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
