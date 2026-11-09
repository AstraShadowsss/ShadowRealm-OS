# Installing ShadowRealm-OS

## Before you begin

Download the AMD64 ISO and its `SHA256SUMS` from the same release directory. On Windows, run `Get-FileHash -Algorithm SHA256 "path\to\ShadowRealm-OS-2026.11-beta1-r2-amd64.iso"` in PowerShell and compare all 64 characters. On Linux, put both files in one directory and run `sha256sum -c SHA256SUMS`.

Checksums detect a changed or incomplete download. They do not independently authenticate its publisher. This beta does not include a release signature.

Back up the destination computer. If using a USB drive, write the ISO as a disk image with an image-writing application; copying the ISO file onto an ordinary filesystem is not enough. An 8 GB or larger USB drive is recommended. Writing an image erases the USB drive.

## On a PC

1. Boot the USB using the computer's boot menu. Choose the live desktop entry.
2. Test display, keyboard, mouse, audio and network before installing. This beta has not been certified for Secure Boot; disable it if the image will not start.
3. Open **Install ShadowRealm-OS**. Choose your language, time zone and keyboard layout.
4. Review the destination disk carefully. Automatic erase-disk installation is the simplest path for a dedicated disk. Optional encryption protects the installed disk while powered off; keep the encryption passphrase safe.
5. Create your own account and password. Read the installer's final summary before confirming disk changes.
6. Finish, restart and remove the USB when prompted. With encryption enabled, enter the disk passphrase during boot, then sign in with your account password.

The live environment is temporary and automatically signs in. Its account is `user`, password `live`; this is not the password of an installed system. The installer creates the account you specify.

Encryption can add a delay before the login screen, particularly in a VM. Do not interrupt an installation or power off while disk changes are in progress. Shared EFI partitions, manual partitioning and dual boot need additional care and are not certified by this beta's VM tests.

## In VirtualBox

Download VirtualBox from [Oracle's official downloads page](https://www.virtualbox.org/wiki/Downloads). The Extension Pack is optional and is not needed to boot or install this ISO; it has separate license terms.

1. Create a new Linux VM, Debian (64-bit). Select the ISO and **skip unattended installation** so the normal ShadowRealm-OS installer runs.
2. Assign 2 CPU cores and 4 GB RAM if the host can spare them. Create a dynamically allocated virtual disk of at least 32 GB; 40 GB gives more room for applications and updates.
3. Use VMSVGA graphics, 128 MB video memory and a USB Tablet pointing device. NAT networking is suitable for normal use. Leave 3D acceleration off initially.
4. Enable EFI for the recommended VirtualBox setup, boot the VM and follow the normal installer. Use the same firmware mode afterward. UEFI boot detects VirtualBox automatically; a named VirtualBox timing compatibility entry is also available in both boot menus.
5. After installation, detach the ISO from the virtual optical drive and boot the virtual disk.

Guest integration is included where available, but shared clipboard and host folders depend on VirtualBox settings. Do not expose shared folders containing sensitive host files to an untrusted guest. This release provides a bootable AMD64 ISO.

At the end of the live session, the splash can hide the media-removal prompt. After removing the installer USB, or once the virtual DVD has ejected, press Enter if the splash remains.

For VirtualBox sound, enable Audio and Audio Output in the VM settings. Use Intel HD Audio and the host's default audio driver (Windows Audio Session/WASAPI on Windows). Microphone input can stay disabled. A null/silent host audio driver cannot play sound through your speakers.
