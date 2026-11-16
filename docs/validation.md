# 2026.11 beta 1 r4 validation

First-login wallpaper follow-up: desktop package 0.2.4 installed over 0.2.3 in the r4 test VM and passed the package audit. On a new account, the packaged wallpaper was selected 5 seconds after the Xfce test timer started and the widget process appeared at 100 seconds. The test measured one VirtualBox configuration. It confirms that the wallpaper can load early and that widget startup still needs separate work.

The follow-up desktop package 0.2.5 installed over 0.2.4 and passed the package audit. On another fresh account in the same VM, the widget process appeared at 26 seconds and the packaged wallpaper was selected at 28 seconds after its Xfce test timer started. The desktop showed all four panels with live process rows. These are individual runs and startup time varies with the host workload. The signed APT feed serves the tested package.

On 15 November 2026, the r4 ISO matched its published SHA-256. A fresh VirtualBox live boot and a clean unencrypted UEFI installation both showed PID, command, CPU and memory rows. The installer finished, the media removal prompt appeared, and the installed account reached the themed desktop and opened Terminal. The first login temporarily showed the stock Xfce wallpaper before the branded desktop and widgets appeared. The blank Processes card was not reproduced in these tests.

Image: `ShadowRealm-OS-2026.11-beta1-r4-amd64.iso`  
SHA256: `4ba996ac5c690d88cfb5d8b401b9fdf6ec0984b7d2cf03d9c5c73837e5355655`

## R4 targeted correction

Artwork 0.2.3 separates interactive splash notices from service-status text. In a live session only, a late-shutdown helper releases Plymouth to a readable console so the installation-media removal/Enter instruction cannot remain hidden. Installed systems keep their themed shutdown. The new helper is restricted to `boot=live`.

The exact r4 image passed internal checksums, BIOS/UEFI boot-entry checks, root permission checks, factory privacy and all eight theme catalogs. A fresh live boot and actual late live-media shutdown/restart handoff were checked, including visible instructions and Enter continuation. Current notice coverage accounts for 2,028 packages and 2,219 notice files.

## Encrypted UEFI installation

A fresh VirtualBox install from the checksum-verified r4 ISO used Calamares automatic partitioning with encryption enabled. Calamares completed, the media-removal prompt was readable, and pressing Enter once continued to GRUB. A brief live-media unmount warning appeared before restart. The installed system accepted the disk passphrase, reached the graphical login screen, and accepted the account password. The root filesystem was mounted on a LUKS mapper, the branded desktop and live widgets loaded, and no system units were in the failed state before updating.

On that encrypted installation, **Software & Updates → System Updates → Install Debian Updates** completed with exit code 0. The transaction applied 58 upgrades, installed one new kernel package and removed zero packages. ShadowRealm-OS desktop advanced from 0.2.3 to 0.2.11 and artwork from 0.2.3 to 0.2.4. The package audit was clean, the desktop package was marked manually installed, and no system units were in the failed state. Restarting from the desktop accepted the disk and account passwords again. Terminal and the live widgets worked on the updated kernel, 6.12.117+deb13-amd64, with the root filesystem still encrypted.

## Dock display checks

Panel 0.2.1 reordered launchers at 800 × 600 and accepted a desktop shortcut while the dock was set to always hide. The shortcut appeared in the dock configuration after confirming its placement. In a separate XRandR layout with two logical regions, the dock stayed on the primary region and could reveal and reorder launchers. A second independent VirtualBox output did not activate in this live session. Physical multi-monitor and hot-plug checks remain open.

## Limits

This is a beta. Physical hardware, Secure Boot, shared-ESP dual boot, suspend/resume and real Bluetooth-radio certification remain unperformed. First sign-in prepares per-user artwork and can briefly show the Xfce background. Matching source and third-party notices accompany the release; notice-file coverage is not legal certification.
