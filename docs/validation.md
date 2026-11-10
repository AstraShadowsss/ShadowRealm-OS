# 2026.11 beta 1 r4 validation

Image: `ShadowRealm-OS-2026.11-beta1-r4-amd64.iso`  
SHA256: `4ba996ac5c690d88cfb5d8b401b9fdf6ec0984b7d2cf03d9c5c73837e5355655`

## R4 targeted correction

Artwork 0.2.3 separates interactive splash notices from service-status text. In a live session only, a late-shutdown helper releases Plymouth to a readable console so the installation-media removal/Enter instruction cannot remain hidden. Installed systems keep their themed shutdown. The new helper is restricted to `boot=live`.

The exact r4 image passed internal checksums, BIOS/UEFI boot-entry checks, root permission checks, factory privacy and all eight theme catalogs. A fresh live boot and actual late live-media shutdown/restart handoff were checked, including visible instructions and Enter continuation. Current notice coverage accounts for 2,028 packages and 2,219 notice files.

R4 retains r3's kernel, installer 0.2.1, account code and root-permission/mount safeguards. The complete 39-job encrypted installation, original-password graphical login, sudo, Terminal, active system services and normal desktop shutdown were verified on r3 immediately before this artwork-only revision; that full installation was not repeated for r4. These results must not be presented as physical-hardware or Secure Boot certification.

## Limits

This is a beta. Physical hardware, Secure Boot, shared-ESP dual boot, suspend/resume and real Bluetooth-radio certification remain unperformed. First sign-in prepares per-user artwork and can briefly show the Xfce background. Matching source and third-party notices accompany the release; notice-file coverage is not legal certification.

Existing r2 installations with the root-permission defect can be repaired without erasure using [the recovery guide](r2-install-recovery.md). Signed APT publication is separate from ISO publication; the existing feed was not replaced by this installer-media update.
