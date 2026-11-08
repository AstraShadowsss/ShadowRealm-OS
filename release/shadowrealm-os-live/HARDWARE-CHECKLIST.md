# Bare-metal release checks

Boot the live image from USB on a spare amd64 machine before changing its disk. Record the exact model, GPU, Wi-Fi chipset, and kernel. Report support for tested models only.

- Boot in UEFI and legacy BIOS where available. Check Secure Boot separately, including the installed system.
- Verify internal NVMe and SATA detection, USB storage, and the installer target list. Install only to a designated test disk.
- Verify Ethernet and Wi-Fi connection, reconnect after suspend, and Bluetooth pairing where available.
- Verify native display resolution, GPU acceleration, external display, brightness, and suspend/resume.
- Test speakers, headphones, microphone recording, webcam preview, and input devices.
- Check battery reporting, charger detection, shutdown, restart, and a kernel update followed by reboot.
- Review missing firmware and driver failures using lspci -nnk, lsusb, and kernel logs. Keep machine identifiers and personal network details out of public reports.

The baseline uses Debian kernel drivers and redistributable firmware. Proprietary NVIDIA drivers and adapters that require vendor software are separate compatibility tests.
