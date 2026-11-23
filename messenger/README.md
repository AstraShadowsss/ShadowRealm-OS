# Shadow Messenger

A native GTK4 Matrix client under development for ShadowRealm-OS. It is not included in the public r4 installer or distributed as a finished messaging application.

## Current implementation

The native application builds and opens on Debian 13. Its account worker supports test-account sign-in, saved-session restoration, joined-room refresh and sign-out without blocking GTK. Saved session credentials and the SDK store passphrase go to Secret Service; the SDK encrypts private data in the local SQLite store. There is no plaintext credential fallback. The sign-in controls require an explicit test-account selection.

Conversation timelines, device verification, key recovery and interoperability testing are not complete. Do not use this build for personal conversations. A successful compiler check does not establish working end-to-end messaging.

## Stack

Rust, GTK4/gtk4-rs, GTK CSS, Matrix Rust SDK, Tokio, SDK-supported SQLite storage and Secret Service. Timeline integration will use matrix-sdk-ui. GIO/D-Bus notifications and Debian packaging remain planned. The primary interface does not embed a browser.

One account worker owns the session. Network and keyring work run outside GTK, with two Tokio worker threads and bounded command queues. No background synchronization loop is enabled yet. Passwords, tokens, recovery material and message content must not be logged.

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

## Release gates

See [the release checklist](RELEASE_CHECKLIST.md). Live-account login/restoration, timelines, send/retry, device verification, recovery, account removal, accessibility, theme integration and independent-client interoperability must pass before installer inclusion. No ShadowRealm-operated homeserver is required; users choose their own Matrix provider.
