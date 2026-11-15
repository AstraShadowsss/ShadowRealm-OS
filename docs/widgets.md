# Desktop widgets

The desktop widgets show local system data. The clock and calendar is optional and uses the computer’s time zone.

| Panel | What it shows |
| --- | --- |
| System Overview | CPU activity between samples; RAM in use based on MemAvailable; swap use; root filesystem space in use. These are percentages, not a security score. |
| Network / Live | An active IPv4 interface and address, plus received and sent traffic in KiB/s. This is local interface traffic, not an Internet speed test. |
| Processes | Process ID, command name, CPU and memory percentages from Linux process statistics. Scroll to see additional rows. Process CPU is the average reported by `ps`, rather than the same interval as the overview CPU bar. |
| Shadow Shield | Firewall status, AppArmor status, detected VPN interface and Tor service status. |
| Clock & calendar | Local time, current month and today’s date. Enable it in Shadow Widgets. |

Open Network for connections, custom DNS and airplane mode. Open Shadow Shield for firewall rules and privacy controls, including VPN/Tor tools. Software & Updates manages installed APT software and available updates; Flatpak updates are separate.

Open **Control Center → Desktop → Widgets** to show or hide each widget and adjust its border color and background opacity. Select **Theme** to restore the active theme’s border color. Leave opacity at **−1** to use the shared value from Appearance. Professional hides desktop widgets by default. Enable **Show widgets in the Professional theme** to display the ones you selected.

The source asset archives include 89 common system roles in each of eight palettes. System tiles, dock artwork and panel glyphs are separate families. Standard inherited icons cover additional names; third-party application icons remain supplied by their own packages.
