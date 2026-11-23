# Shadow Messenger

A native GTK4 Matrix client under development for ShadowRealm-OS. It is not included in the public r4 installer or distributed as a finished messaging application.

## Current implementation

The native application builds and opens on Debian 13. Its account worker supports test-account sign-in, saved-session restoration, joined-room updates and sign-out without blocking GTK. A single SDK long-poll sync feeds room updates. Room selection opens an SDK-managed timeline, with a 200-event preview, older-message fetching, a composer, queued/failed status and a retry control. Drafts are kept separately while changing rooms. Saved session credentials and the SDK store passphrase go to Secret Service; the SDK encrypts private data in the local SQLite store. There is no plaintext credential fallback. The sign-in controls require an explicit test-account selection. Each room shows its encryption state; sending to an unencrypted room is blocked unless the user explicitly allows it for that selection.

Device verification, key recovery, extended history and independent-client interoperability are not complete. Do not use this build for personal conversations. A successful compiler check does not establish working end-to-end messaging.

## Stack

Rust, GTK4/gtk4-rs, GTK CSS, Matrix Rust SDK, Tokio, SDK-supported SQLite storage and Secret Service. Timeline integration uses matrix-sdk-ui 0.19.1. GIO/D-Bus notifications and Debian packaging remain planned. The primary interface does not embed a browser.

One account worker owns the session. Network and keyring work run outside GTK, with two Tokio worker threads and bounded command queues. One SDK long-poll synchronization task runs per connected account. A failed sync requires an explicit reconnect through Restore saved account. Passwords, tokens, recovery material and message content must not be logged.

## Build and checks

Build dependencies include Rust 1.96, GTK 4.8 or later development libraries, pkg-config, a C compiler, OpenSSL, SQLite and D-Bus development libraries. Cargo lockfiles are included. Original project code uses MIT; dependency licenses must be collected before binary distribution.

```sh
cargo test --locked --manifest-path core/Cargo.toml
CARGO_BUILD_JOBS=1 cargo build --locked --manifest-path native/Cargo.toml
cargo test --locked --manifest-path native/Cargo.toml
```

The graphical button check requires a running test desktop:

```sh
cargo test --locked --manifest-path native/Cargo.toml ui_tests:: -- --ignored --test-threads=1
```

The Secret Service round-trip test must run in a separate disposable keyring session, not against the owner's desktop keyring.

## Measured baseline

The unconnected development window used 200,848 KiB resident memory and 0% of one CPU core during a five-second idle sample in a software-rendered VirtualBox guest. This is a baseline for the empty shell, not a benchmark for a connected messaging session or a performance guarantee. Connected idle, synchronization, history, attachments and calls still require measurements.

## Verified development checks

A disposable loopback-only Synapse fixture passed protected login, same-device session restoration and sign-out. A two-account test confirmed that the server stored `m.room.encrypted` while the receiving SDK timeline decrypted the expected body. The actual GTK controls passed test-account login, existing-room selection, queued send, server acceptance and sign-out. The fixture uses a test-only CA hook; normal builds do not add this certificate or bypass TLS verification. The owner's desktop keyring is not used by these tests. A separate device-verification test passed cancellation without trust, refusal to confirm before numbers are available, retry, matching SAS numbers and verified-device state. The verification interface is not implemented yet. Recovery tests restored cross-signing keys on a new device, rejected an invalid key and decrypted an older message from the encrypted backup with the original device's sync stopped. Recovery uses on-demand key downloads for opened messages. Backup creation and cross-signing setup remain explicit actions; they are not enabled automatically at login. Recovery controls and authentication-challenge handling are still unfinished. These checks do not replace external-client interoperability, recovery or independent security review.

## Release gates

See [the release checklist](RELEASE_CHECKLIST.md). Live-account login/restoration, timelines, send/retry, device verification, recovery, account removal, accessibility, theme integration and independent-client interoperability must pass before installer inclusion. No ShadowRealm-operated homeserver is required; users choose their own Matrix provider.
