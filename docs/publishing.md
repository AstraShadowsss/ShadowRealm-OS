# Release locations

ShadowRealm-OS 2026.11 beta 1 uses revision r4 of the installer image. Beta 1 is the release name; r4 identifies the current installer. The unchanged third-party source parts remain attached to the r2 GitHub tag; do not duplicate their 11.4 GB of data.

| Location | Contents |
| --- | --- |
| GitHub repository, Code tab | Editable custom source, build recipes, branding masters, documentation and screenshots |
| GitHub release, Assets section | Six third-party source-archive parts, named part01 through part06 |
| SourceForge, 2026.11-beta1 folder | One ISO, SHA256SUMS, release notes, license notices, source inventories, custom-source archive and source-download/reassembly instructions |
| Project website | Screenshots, installation/documentation links and Updates & Packages |
| Signed APT feed | Versioned custom DEBs and signed indexes for installed-system updates |

A release folder is not a package mirror. Keep only the ISO, checksums, release notes, license notices, source inventories and source-download instructions there. Custom DEBs belong in the signed APT pool. Two current builds (desktop 0.2.20 and Terminal 0.2.3) were manually placed in the 2026.11-beta1 folder; they are not signed update metadata and should be moved to the pool through the normal repository publisher or removed. Do not point users at a bare DEB in a release folder as an update mechanism.

## Publishing a fix

Increment the affected package version, build and test it, sign the repository metadata and publish the new immutable DEB plus indexes. Existing users can install it through Software & Updates or apt update followed by apt upgrade. A GitHub commit alone does not publish an APT update. Never overwrite a published DEB under the same filename.

Installer changes require a rebuilt ISO and new checksums, matching source and notices, plus the documented boot/installer checks. Publish it to the single intended SourceForge version folder and verify the default Download button selects the ISO.

## Building the r5 image

The image must carry packages newer than the published feed, or every fresh install immediately needs updates. Desktop 0.2.21, security 0.2.1, installer settings 0.2.2, artwork 0.2.6 and Messenger 0.1.0 are the r5 source versions. The signed trixie feed currently publishes desktop 0.2.19+window1.icon1.clean3+refresh1+launch1, security 0.2.0, Terminal 0.2.3 and artwork 0.2.6+window1.icon1.clean3. Desktop 0.2.21 and security 0.2.1 sort above it; artwork 0.2.6 is the published package that must be reused because the committed artwork source cannot yet reproduce it. Keep incrementing versions whenever shipped content changes.

1. Build every custom package on a disposable Debian 13 builder, following the commands in `docs/build-guide.md`. Run them from the repository root, not from inside `components/`, so relative artwork paths such as `branding/professional-masters` resolve.
2. Check each DEB version with `dpkg-deb -f <deb> Version` before continuing.
3. Publish desktop 0.2.21 (dock shelf and reopenable Welcome Summary) and security 0.2.1 (scoped Docker forwarding) to the signed feed before advertising those changes. The signed feed still has desktop 0.2.19+window1.icon1.clean3+refresh1+launch1 and security 0.2.0; the desktop 0.2.20 and Terminal 0.2.3 DEBs in the SourceForge release folder are not a signed update.
4. Build the live image, then run `release/shadowrealm-os-live/check-iso.sh` and the installer checks in `docs/installation.md`.
5. Install the image in a clean VM, run `sudo apt update` and confirm no custom package is offered as an upgrade. If one is, the image is older than the feed and must not be published.
6. Publish the ISO with new checksums, matching source and notices to the single SourceForge version folder.

Shadow Messenger 0.1.0 is included in the r5 image and in the signed package feed. Its package installs the GTK4 client, a theme-generated `shadow-messenger-app` icon in every ShadowRealm-OS palette, and a `gnome-keyring` dependency. Keep r5 unpublished until the remaining release checklist gates and a fresh installed-image test pass.

## Hosting boundaries

The large third-party source bundle is supplied as six GitHub Release attachments, each below 2 GiB. Download all six and follow the verification/reassembly instructions in the SourceForge Sources folder. Do not commit these large parts into Git history or duplicate them on SourceForge. SourceForge's ISO and small release materials are kept below its 5 GB storage target.

Automatic GitHub-release copying into SourceForge is disabled because it created duplicate folders and redundant source downloads. Publish release files deliberately; this does not disable GitHub or APT updates. SourceForge folder READMEs use supported Markdown or plain text, with absolute image links and no raw HTML.

Private signing keys, recovery material, credentials and VM disks stay outside public uploads. The public signing key and fingerprint are intended for distribution. Original project work and third-party material retain their respective licenses.
