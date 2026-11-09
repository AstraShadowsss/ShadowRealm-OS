#!/usr/bin/python3
"""Package the ShadowRealm-OS live installer using Debian's maintained Calamares modules."""
import argparse, shutil, subprocess, tarfile, tempfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
version_file = a.source/'INSTALLER_VERSION'
version = (version_file if version_file.is_file() else a.source/'VERSION').read_text().strip()

def put(root, name, text, mode=0o644):
    path = root/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(mode)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = root/'etc/shadowrealm-os/calamares'
    cfg.mkdir(parents=True)
    with tarfile.open(a.source/'calamares-settings-source.tar.gz') as archive:
        archive.extractall(cfg, filter='data')
    (cfg/'qml').symlink_to('/usr/share/calamares/qml')
    (cfg/'branding').symlink_to('/usr/share/calamares/branding')
    settings = cfg/'settings.conf'
    text = settings.read_text().replace('branding: debian', 'branding: shadowrealm-os')
    text = text.replace('  - bootloader-config', '  - shadowrealm-os-bootloader-config')
    text = text.replace('  - sources-final', '  - shadowrealm-os-finalize')
    text = text.replace('  - unpackfs', '  - shadowrealm-os-target-check\n  - unpackfs')
    # The complete system and bootloader files are already in the live image.
    # Do not add a second, older installer/CD package repository to the target.
    text = text.replace('  - sources-media\n', '').replace('  - sources-media-unmount\n', '')
    text = text.replace('prompt-install: false', 'prompt-install: true')
    text = text.replace('disable-cancel-during-exec: false', 'disable-cancel-during-exec: true')
    text += '\nhide-back-and-next-during-exec: true\n'
    settings.write_text(text)
    welcome = cfg/'modules/welcome.conf'
    welcome.write_text(welcome.read_text().replace('true', 'false').replace('requiredStorage:    15', 'requiredStorage:    20').replace('requiredRam:        1.0', 'requiredRam:        2.0'))
    with welcome.open('a') as file:
        file.write('\ninternetCheckUrl: "https://deb.debian.org/debian/"\n')
    put(root, 'etc/shadowrealm-os/calamares/modules/locale.conf', '''---
useSystemTimezone: true
adjustLiveTimezone: true
geoip:
  style: none
''')
    put(root, 'etc/shadowrealm-os/calamares/modules/partition.conf', '''# Calamares 3.3 partition options: upstream configuration is CC0-1.0.
# https://github.com/calamares/calamares/blob/v3.3.14/src/modules/partition/partition.conf
---
efi:
  mountPoint: /boot/efi
  recommendedSize: 512MiB
  minimumSize: 300MiB
  label: EFI
userSwapChoices: [none, file]
initialSwapChoice: file
initialPartitioningChoice: none
defaultFileSystemType: ext4
luksGeneration: luks1
enableLuksAutomatedPartitioning: true
preCheckEncryption: false
allowManualPartitioning: true
lvm:
  enable: true
''')
    packages = cfg/'modules/packages.conf'
    packages.write_text(packages.read_text()+"      - 'shadowrealm-os-installer-settings'\n      - 'calamares'\n      - 'debian-installer-launcher'\n")
    put(root, 'usr/share/calamares/branding/shadowrealm-os/branding.desc', '''---
componentName: shadowrealm-os
welcomeStyleCalamares: true
welcomeExpandingLogo: true
windowExpanding: normal
windowSize: 900px,640px
windowPlacement: center
strings:
  productName: ShadowRealm-OS
  shortProductName: ShadowRealm-OS
  version: "2026.11"
  shortVersion: "2026.11"
  versionedName: ShadowRealm-OS 2026.11
  shortVersionedName: ShadowRealm-OS 2026.11
  bootloaderEntryName: ShadowRealm-OS
sidebar: widget
navigation: widget
slideshow: show.qml
slideshowAPI: 2
images:
  productLogo: logo.png
  productIcon: logo.png
  productWelcome: logo.png
style:
  SidebarBackground: "#090910"
  SidebarText: "#eeeeee"
  SidebarTextCurrent: "#00dce9"
  SidebarBackgroundCurrent: "#25202d"
''')
    with tarfile.open(a.source/'shadowrealm-os-artwork-source.tar.gz') as archive:
        member = archive.getmember('./usr/share/shadowrealm-os/branding/ShadowRealm-OS-Circular-Neon.png')
        logo = archive.extractfile(member).read()
    logo_path = root/'usr/share/calamares/branding/shadowrealm-os/logo.png'
    logo_path.write_bytes(logo)
    put(root, 'usr/share/calamares/branding/shadowrealm-os/show.qml', '''import QtQuick 2.0
import calamares.slideshow 1.0
Presentation {
    Slide {
        Rectangle { anchors.fill: parent; color: "#000000" }
        Column {
            anchors.centerIn: parent
            spacing: 16
            Image {
                source: "logo.png"
                width: 160; height: 160
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text: qsTr("ShadowRealm-OS is being installed.")
                width: 500; font.pixelSize: 24; color: "#f2eff8"
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            Text {
                text: qsTr("Keep this computer powered on until installation finishes.")
                width: 500; font.pixelSize: 16; color: "#f2eff8"
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }
}
''')
    put(root, 'usr/share/shadowrealm-os/installer.qss', '''QWidget { background-color: #000000; color: #f2eff8; }
QLineEdit, QComboBox, QAbstractItemView { background-color: #15151e; color: #f2eff8; selection-background-color: #80159a; selection-color: white; border: 1px solid #595064; padding: 4px; }
QPushButton { background-color: #211527; color: #f2eff8; border: 1px solid #73517e; border-radius: 3px; padding: 7px 18px; }
QPushButton:hover, QPushButton:focus { border-color: #00dce9; background-color: #302039; }
QPushButton:disabled { color: #77717e; border-color: #37313d; }
QCheckBox, QRadioButton { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #00dce9; background: #15151e; }
QCheckBox::indicator:checked { background: #bd00cd; border: 2px solid #00dce9; }
QProgressBar { border: 1px solid #595064; background: #15151e; color: #f2eff8; text-align: center; }
QProgressBar::chunk { background: #00aab5; }
PartitionLabelsView, PartitionLabelsView QWidget { background-color: #eeeeee; color: #111111; }
QToolTip { background: #211527; color: white; border: 1px solid #00dce9; }
''')
    for name, body in {
        'shadowrealm-os-bootloader-config': '''import pathlib
import libcalamares
def run():
    root=pathlib.Path(libcalamares.globalstorage.value("rootMountPoint"))
    if root==pathlib.Path("/") or not (root/"etc/debian_version").is_file():
        return ("Invalid installation target", "The installer target was not mounted.")
    if not (root/"usr/sbin/grub-install").is_file():
        return ("Bootloader files are missing", "The live image must include GRUB for offline installation.")
    # A LUKS key in the initramfs must never be readable by ordinary accounts.
    folder=root/"etc/initramfs-tools/conf.d"
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"shadowrealm-os-permissions").write_text("UMASK=0077\\n")
    return None
''',
        'shadowrealm-os-target-check': '''import pathlib
import libcalamares

def run():
    value=libcalamares.globalstorage.value("rootMountPoint")
    if not isinstance(value,str) or not value:
        return ("Installation target is not mounted", "No target filesystem was provided. Restart the live session before retrying the installation.")
    root=pathlib.Path(value).resolve()
    if root==pathlib.Path("/") or not root.is_mount():
        return ("Installation target is not mounted", "The target disk could not be mounted. Files have not been copied. Restart the live session before retrying the installation.")
    return None
''',
        'shadowrealm-os-finalize': '''import pathlib
import libcalamares
def run():
    root=pathlib.Path(libcalamares.globalstorage.value("rootMountPoint"))
    if root==pathlib.Path("/") or not (root/"etc/debian_version").is_file():
        return ("Invalid installation target", "The installer target was not mounted.")
    # The filesystem root must be traversable by services and user sessions.
    # Staging directories created by mktemp are private and can otherwise
    # propagate mode 0700 through an archive into the installed root.
    root.chmod(0o755)
    sources="""# Debian repositories; package signatures are verified by APT.
deb https://deb.debian.org/debian trixie main contrib non-free-firmware
deb-src https://deb.debian.org/debian trixie main contrib non-free-firmware
deb https://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb-src https://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb https://security.debian.org/debian-security trixie-security main contrib non-free-firmware
deb-src https://security.debian.org/debian-security trixie-security main contrib non-free-firmware
"""
    (root/"etc/apt/sources.list").write_text(sources)
    # Drop the stock duplicate and live-build's temporary unsigned local feed.
    for name in ("zz-sources.list", "packages.list"):
        (root/"etc/apt/sources.list.d"/name).unlink(missing_ok=True)
    # Debian's signed EFI GRUB may start with its prefix on the ESP, rather
    # than reading the differently named ShadowRealm-OS vendor helper automatically.
    # Dispatch only our own firmware path; never replace another OS's file.
    vendor=root/"boot/efi/EFI/ShadowRealm-OS/grub.cfg"
    if vendor.is_file():
        entry=root/"boot/efi/boot/grub/grub.cfg"
        marker="# ShadowRealm-OS signed-GRUB compatibility entry"
        if entry.exists() and not entry.read_text().startswith(marker):
            return ("EFI configuration conflict", "Use a dedicated EFI partition; an existing boot configuration was preserved.")
        entry.parent.mkdir(parents=True,exist_ok=True)
        entry.write_text(marker+"\\nif [ \\"$fw_path\\" = \\"($root)/EFI/ShadowRealm-OS\\" ]; then\\n configfile ($root)/EFI/ShadowRealm-OS/grub.cfg\\nfi\\n")
    for image in (root/"boot").glob("initrd.img-*"):
        image.chmod(0o600)
    username=libcalamares.globalstorage.value("username")
    if isinstance(username,str) and username and "/" not in username and username not in (".",".."):
        shortcut=root/"home"/username/"Desktop/Install ShadowRealm-OS.desktop"
        if shortcut.resolve().is_relative_to(root/"home") and shortcut.is_file() and "Exec=shadowrealm-os-install" in shortcut.read_text():
            shortcut.unlink()
            try: shortcut.parent.rmdir()
            except OSError: pass
    return None
''',
    }.items():
        base = 'usr/lib/calamares/modules/'+name+'/'
        put(root, base+'module.desc', f'---\ntype: job\nname: {name}\ninterface: python\nscript: main.py\n')
        put(root, base+'main.py', body)
        compile(body, name, 'exec')
    put(root, 'usr/bin/shadowrealm-os-install', '''#!/bin/sh
set -eu
if [ ! -f /run/live/medium/live/filesystem.squashfs ]; then
 echo 'Start the ShadowRealm-OS installer from the live USB or ISO.' >&2
 exit 1
fi
exec 9>"${XDG_RUNTIME_DIR:?}/shadowrealm-os-installer.lock"
flock -n 9 || exit 0
restore() {
 xhost -si:localuser:root >/dev/null 2>&1 || true
 if [ -f /etc/fstab.shadowrealm-os-live ]; then sudo mv /etc/fstab.shadowrealm-os-live /etc/fstab; fi
}
trap restore EXIT HUP INT TERM
if [ -f /etc/fstab ] && [ ! -e /etc/fstab.shadowrealm-os-live ]; then
 sudo mv /etc/fstab /etc/fstab.shadowrealm-os-live
fi
xhost +si:localuser:root >/dev/null
export QT_AUTO_SCREEN_SCALE_FACTOR=1
pkexec /usr/bin/calamares --config /etc/shadowrealm-os/calamares -stylesheet /usr/share/shadowrealm-os/installer.qss
''', 0o755)
    put(root, 'etc/polkit-1/rules.d/45-shadowrealm-os-live-installer.rules', '''// The live session already grants local sudo without a password.
// Authorize only the installer action, only from its active local session.
polkit.addRule(function(action, subject) {
    if (action.id === "com.github.calamares.calamares.pkexec.run" && subject.local && subject.active) {
        try {
            if (polkit.spawn(["/usr/bin/test", "-f", "/run/live/medium/live/filesystem.squashfs"]) === "") {
                return polkit.Result.YES;
            }
        } catch (error) { }
    }
});
''')
    entry = '[Desktop Entry]\nType=Application\nName=Install ShadowRealm-OS\nComment=Install ShadowRealm-OS on a selected disk\nExec=shadowrealm-os-install\nTryExec=/usr/bin/calamares\nIcon=/usr/share/pixmaps/shadowrealm-os-logo.png\nTerminal=false\nCategories=System;\n'
    put(root, 'usr/share/applications/org.shadowrealm_os.install.desktop', entry)
    # Seed before xfdesktop starts; late file creation can leave duplicate live-overlay icons.
    put(root, 'etc/skel/Desktop/Install ShadowRealm-OS.desktop', entry, 0o755)
    diverted = ['etc/xdg/autostart/calamares-desktop-icon.desktop', 'usr/share/applications/calamares-install-debian.desktop', 'usr/share/applications/debian-installer-launcher.desktop']
    for path in diverted:
        put(root, path, '[Desktop Entry]\nType=Application\nName=ShadowRealm-OS installer entry managed separately\nExec=true\nHidden=true\nNoDisplay=true\n')
    pre = '#!/bin/sh\nset -e\n'
    post = '#!/bin/sh\nset -e\nif [ "$1" = remove ] || [ "$1" = purge ] || [ "$1" = abort-install ]; then\n'
    for path in diverted:
        path = '/'+path
        pre += f'dpkg-divert --package shadowrealm-os-installer-settings --add --rename --divert {path}.debian {path}\n'
        post += f' dpkg-divert --package shadowrealm-os-installer-settings --remove --rename --divert {path}.debian {path}\n'
    post += 'fi\n'
    put(root, 'DEBIAN/preinst', pre, 0o755)
    put(root, 'DEBIAN/postrm', post, 0o755)
    put(root, 'usr/share/doc/shadowrealm-os-installer-settings/copyright', (a.source/'LICENSE').read_text()+'\nDebian-derived installer configuration retains the following notices:\n'+(a.source/'calamares-settings-COPYRIGHT').read_text())
    put(root, 'DEBIAN/control', f'''Package: shadowrealm-os-installer-settings
Version: {version}
Section: admin
Priority: optional
Architecture: all
Maintainer: ShadowRealm-OS contributors <packages@shadowrealm-os.invalid>
Depends: calamares, calamares-settings-debian, shadowrealm-os-artwork, pkexec, sudo, x11-xserver-utils, util-linux, grub2-common, grub-pc-bin, grub-efi-amd64-bin, cryptsetup-initramfs, keyutils, isolinux, syslinux-common
Description: ShadowRealm-OS graphical live installer and offline boot configuration
''')
    subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'shadowrealm-os-installer-settings_{version}_all.deb')],check=True)
