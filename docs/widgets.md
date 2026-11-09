# Desktop widgets

The four small panels are live status displays, backed by local Linux data. They are part of the custom desktop source in `components/shadow-link-dock.c`; GitHub contains their source and screenshots, not a separate online monitoring service.

| Panel | What it shows |
| --- | --- |
| System Overview | CPU activity between samples; RAM in use based on MemAvailable; swap use; root filesystem space in use. These are percentages, not a security score. |
| Network / Live | An active IPv4 interface and address, plus received and sent traffic in KiB/s. This is local interface traffic, not an Internet speed test. |
| Processes | Process ID, command name, CPU and memory percentages from Linux process statistics. Scroll to see additional rows. Process CPU is the average reported by `ps`, rather than the same interval as the overview CPU bar. |
| Shadow Shield | Firewall status/policy, detected VPN interface and Tor service status. An active VPN interface or running Tor service alone does not prove every application is protected. |

Open Network for connections, custom DNS and airplane mode. Open Shadow Shield for firewall rules and privacy controls, including VPN/Tor tools. Software & Updates manages installed APT software and available updates; Flatpak updates are separate. None of these widgets uploads its readings to GitHub.

Appearance controls the coordinated palette. Widget settings control which panels are visible, their sizing and placement. Background transparency changes the supported panel background while keeping text readable.

The source asset archives include 89 common system roles in each of eight palettes. System tiles, dock artwork and panel glyphs are separate families. Standard inherited icons cover additional names; third-party application icons remain supplied by their own packages.
