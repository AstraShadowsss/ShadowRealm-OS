# ShadowRealm-OS updates

The revised Beta 1 image includes the signed custom package repository at:

`https://shadowrealm-os.sourceforge.io/apt`

It supplies ShadowRealm-OS desktop components and games. Debian/vendor repositories remain responsible for their packages, and Flatpak applications update separately. Open Software & Updates and refresh to review available APT updates. Updates are not installed automatically by this setup package.

## Earlier Beta 1 installations

The original image can be connected without reinstalling. Download `shadowrealm-os-archive-keyring_2026.11-1_all.deb` from the Beta 1 release folder, verify it against that folder's SHA256SUMS, then install it:

```sh
sudo apt install ./shadowrealm-os-archive-keyring_2026.11-1_all.deb
sudo apt update
```

This installs the public key, a repository-specific Signed-By entry and package pinning that excludes unrelated packages. Review offered updates through Software & Updates or APT.

Public signing-key fingerprint:

`F4D5 FDF9 049F EF1E B4F0 844B F288 9DF2 870E 9430`

Only the public key belongs in the ISO and repository. Signing private keys and host upload credentials are not included in the source or release files.

To remove this custom update source, use `sudo apt purge shadowrealm-os-archive-keyring`, then refresh APT. This removes its key and repository configuration; installed desktop components remain installed, and Debian/vendor update sources remain separate.

## Maintainer: build and publish

On Debian 13 with dpkg-deb and GnuPG:

```sh
python3 release/build-apt-repository.py reviewed-packages new-repository \
  --signing-key FULL_SIGNING_KEY_FINGERPRINT --valid-days 90
```

Use reviewed custom DEBs and increase package versions for every published change. Never publish different bytes under an existing package/version filename. Publish matching source and upstream notices with every changed package, including modified GPL components.

The builder creates package indexes, immutable by-hash copies, signed Release/InRelease metadata and an exported public key. It rejects unrelated packages, duplicate package/version/architecture entries and existing output directories.

With python3-paramiko and a configured SSH host key, the publisher uses SFTP:

```sh
python3 release/publish-apt-repository.py new-repository \
  --user YOUR_SOURCEFORGE_USER,shadowrealm-os --identity /path/to/upload-key
```

It verifies existing package bytes before reusing a filename, uploads immutable packages/indexes first, replaces metadata atomically and publishes InRelease last. Keep previous packages/by-hash files for clients already updating and for reviewed rollback packages. Package rollback is not automatic and must be tested for the affected component.

## Expiry and key maintenance

**Current metadata expires on 6 February 2027.** Sign and publish refreshed metadata before expiry, even if no package versions changed. Future publication dates change this deadline; inspect Valid-Until in InRelease. The builder defaults to 14 days; production currently uses 90 days. Do not disable signature or expiry checks to work around missed maintenance.

The signing key expires in November 2028 and needs renewal or a documented rotation before then. Maintain protected offline recovery material. Private signing storage must stay outside GitHub, SourceForge and all project/source/release bundles.

## Checks performed

- Disposable-key local repository: signature verification and isolated APT update succeeded.
- SourceForge HTTPS: APT fetched signed metadata and downloaded a package successfully.
- A real setup-package upgrade from 2026.11-0 to 2026.11-1 succeeded over signed HTTPS while preserving the existing transparency settings.
- APT rejected unsigned, signature-altered and expired metadata, and a modified package download.
- Repository-specific package pinning exposed the custom package candidates without replacing Debian's bash package.

These checks cover the repository mechanism. Every future application update still needs its own regression and upgrade tests.

## Browse packages

The [Updates & Packages page](https://shadowrealm-os.sourceforge.io/apt/) lists the current custom DEBs. It is in SourceForge project web space, separate from the ISO download listing. APT reads the signed metadata there; `apt update` refreshes the lists and `apt upgrade` installs available updates.
