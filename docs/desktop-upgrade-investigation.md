# Desktop package dependency investigation

The package is named `shadowrealm-os-desktop`. It owns the system launcher and
the XFCE autostart entries for the session and widgets. The launchers use the
packaged runtime under `/usr/share/shadowrealm-os/desktop/runtime`. Removing the
package removes those files and prevents the custom session from starting at
the next login, even if user-level shortcuts remain.

## Packaging defect

Desktop 0.2.5 required Debian's `network-manager-gnome` transition package.
Debian 13 ships it as a wrapper for `network-manager-applet` and
`nm-connection-editor`. Forky ships the two real packages. APT on the r4 QA
installation scheduled the entire ShadowRealm-OS desktop for removal when
asked to remove the old transition package.

- [Debian 13 transition package](https://packages.debian.org/trixie/network-manager-gnome)
- [Forky network applet](https://packages.debian.org/forky/network-manager-applet)
- [Forky connection editor](https://packages.debian.org/forky/nm-connection-editor)

Version 0.2.6 declares the applet and editor directly and retains NetworkManager.
It also declares XFCE desktop, session and window manager, GVfs, X11 utilities
and process tools used by the desktop. The image recipe uses the split
packages and marks the custom desktop as manually installed to keep it rooted
for autoremove. The desktop package's installed files are identical to 0.2.5.
An APT manual mark protects against autoremove. A full-upgrade solver can still
propose removing a manually installed package if dependencies are unsatisfiable.

## Validation on the installed r4 QA image

| Check | Result |
| --- | --- |
| 0.2.5, simulate removal of the transition package | APT scheduled removal of the custom desktop. |
| Install 0.2.6 over 0.2.5 on Debian 13 | Passed with zero removals and an empty dpkg audit. |
| Compare the installed-file archive and maintainer scripts | Byte-identical to 0.2.5. |
| 0.2.6, simulate stable full-upgrade, autoremove and wrapper removal | Passed. The checks also verified the desktop's manual mark and packaged startup files. |
| Restore the old dependency in a copy of dpkg status and simulate full-upgrade with only the Forky index | APT scheduled removal of both the wrapper and the custom desktop, while upgrading the real applet and editor. |
| 0.2.6 with the isolated Forky index | All three simulations passed. Full-upgrade scheduled removal of the obsolete wrapper and kept the custom desktop, XFCE components and real network tools. |

## Regression and recovery

Run `bash release/tests/check-desktop-apt.sh` on a provisioned Debian 13
installation with refreshed APT indexes and desktop 0.2.6 or newer. It checks
the manual marker, required packages, launcher and autostart files, then
rejects removal of any required package in simulated full-upgrade, autoremove
and transition-package removal. To check a different package index on a scratch
system, pass isolated APT `-o` settings to the script. Debian 13 remains the
supported base. No testing packages were installed in the validation VM.

On a supported Debian 13 system with a missing desktop, first confirm the APT
sources and policy point to the supported Debian and ShadowRealm-OS repositories.
Preview the transaction with `apt-get -s install shadowrealm-os-desktop`.
If the plan is correct, use `sudo apt-get install --reinstall --no-remove
shadowrealm-os-desktop` and sign out and back in. Reinstalling recovers
package-owned launchers and autostart files. A machine already moved to testing
needs its suite and package state assessed separately before attempting recovery.
