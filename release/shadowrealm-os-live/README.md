# Build the ShadowRealm-OS AMD64 live installer

Use a disposable Debian 13 AMD64 builder. Read the docs/build-guide.md for dependencies and the commands that build all nine ShadowRealm-OS packages and nine game packages into outputs/. Keep outputs/ next to components/, games/ and release/.

The supported build layout is deliberately fixed:

- A new, initially absent /var/tmp/shadowrealm-os-iso-build directory.
- An ext4 build volume mounted at /mnt/shadowrealm-build, with at least 12 GB free for ISO work.

From the source repository root, run:

```sh
sudo bash release/shadowrealm-os-live/prepare-build.sh /var/tmp/shadowrealm-os-iso-build --build
sudo bash release/shadowrealm-os-live/check-iso.sh /var/tmp/shadowrealm-os-iso-build/ShadowRealm-OS-amd64.iso
```

The pipeline creates a Debian live-build base, refreshes applications, finalizes a clean root, embeds notices, and produces the hybrid ISO. It removes the unused Debian text installer; Calamares is the supported installer. In Calamares select the intended disk and use the Encrypt system checkbox for optional LUKS encryption. The tested layout has encrypted root and swap inside it, with a readable EFI System Partition on UEFI machines. Back up the destination and review the partition summary before confirming.

Debian and its security archive, signed LibreWolf and Jami repositories, and Flathub provide their respective updates. Jami's repository key is fingerprint-pinned in refresh-live-root.sh. ShadowRealm-OS custom package updates require a separately maintained, signed repository; none is published by this local build kit.

The live session signs in automatically (temporary account user, password live). Installed accounts are chosen by the recipient. No owner account, credentials, saved network profiles or personal Home should enter the image. check-iso.sh verifies both boot entries, internal checksums, required packages, retained boot maintenance tools and forbidden private/build paths. Consult the delivered Release validation.txt for current test results and HARDWARE-CHECKLIST.md for physical-device checks. Do not infer Secure Boot or bare-metal certification from VM tests.
