# Release locations

ShadowRealm-OS 2026.11 beta 1 uses revision r2 of the installer image. Beta 1 is the release name; r2 identifies the revised ISO and GitHub tag.

| Location | Contents |
| --- | --- |
| GitHub repository, Code tab | Editable custom source, build recipes, branding masters, documentation and screenshots |
| GitHub release, Assets section | Six third-party source-archive parts, named part01 through part06 |
| SourceForge, 2026.11-beta1 folder | One ISO, SHA256SUMS, release notes, license notices, source inventories, custom-source archive and source-download/reassembly instructions |
| Project website | Screenshots, installation/documentation links and Updates & Packages |
| Signed APT feed | Versioned custom DEBs and signed indexes for installed-system updates |

## Publishing a fix

Increment the affected package version, build and test it, sign the repository metadata and publish the new immutable DEB plus indexes. Existing users can install it through Software & Updates or apt update followed by apt upgrade. A GitHub commit alone does not publish an APT update. Never overwrite a published DEB under the same filename.

Installer changes require a rebuilt ISO and new checksums, matching source and notices, plus the documented boot/installer checks. Publish it to the single intended SourceForge version folder and verify the default Download button selects the ISO.

## Hosting boundaries

The large third-party source bundle is supplied as six GitHub Release attachments, each below 2 GiB. Download all six and follow the verification/reassembly instructions in the SourceForge Sources folder. Do not commit these large parts into Git history or duplicate them on SourceForge. SourceForge's ISO and small release materials are kept below its 5 GB storage target.

Automatic GitHub-release copying into SourceForge is disabled because it created duplicate folders and redundant source downloads. Publish release files deliberately; this does not disable GitHub or APT updates. SourceForge folder READMEs use supported Markdown or plain text, with absolute image links and no raw HTML.

Private signing keys, recovery material, credentials and VM disks stay outside public uploads. The public signing key and fingerprint are intended for distribution. Original project work and third-party material retain their respective licenses.
