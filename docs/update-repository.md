# Signed update repository — preparation

The published beta does not yet include a ShadowRealm-OS APT feed. This document and the builder prepare that work; no live repository or trusted production signing key has been deployed.

Preparation check: on Debian 13, one existing game DEB was indexed and signed with a disposable Ed25519 key. `gpgv` verified the signature and an isolated `apt-get update` accepted the signed repository. The temporary key and archive were removed afterward. This checks local archive construction, not HTTPS hosting, upgrades or production security policy.

## Build

On Debian 13, with `dpkg-deb` and GnuPG installed:

```sh
python3 release/build-apt-repository.py reviewed-packages new-repository \
  --signing-key FULL_SIGNING_KEY_FINGERPRINT
```

Supply reviewed custom DEBs only. Increase package versions for every published change. Never replace a published package with different bytes under the same version. The builder refuses existing output directories, unrelated packages, duplicate versions and unsupported architectures. It creates package indexes, immutable by-hash copies, signed Release/InRelease metadata and an exported public key. It never uploads a private key.

Repository metadata expires after 14 days by default. Refresh and sign it before expiry even when packages have not changed. Do not disable APT signature or expiry checks to work around publishing errors.

## Before going live

1. Choose and test an HTTPS hosting location; SourceForge project web is a candidate, not yet an accepted APT endpoint.
2. Create the real signing key in controlled storage, document expiry/rotation/revocation, and keep a protected offline backup. A test key must never become the public trust anchor.
3. Publish matching source and upstream notices for every changed package, including modified GPL components.
4. Upload immutable packages and by-hash files first. Publish signed metadata last; retain previous by-hash indexes long enough for clients already updating.
5. In a disposable Debian VM, test APT signature checks, a deliberately corrupted download, missing/expired signatures, version upgrades, interrupted updates and preservation of user settings. Then test the actual HTTPS host with the same checks.
6. Create a reviewed setup DEB containing the public key, a deb822 `.sources` entry using `Signed-By`, and package-specific pinning. The custom repository must not replace ordinary Debian/vendor packages.
7. Add that setup package to the next ISO and offer it once to existing beta users. Verify Update Center integration before advertising automatic custom updates.

The private key belongs outside GitHub, SourceForge and source/release bundles. Never publish a key or enable an update source merely because a repository directory was generated successfully.
