# Shadow Messenger

A native GTK4 Matrix client under development for ShadowRealm-OS. It is not included in the public r4 installer or distributed as a finished messaging application.

## Current implementation

The native application builds and opens on Debian 13. Its account worker supports test-account sign-in, saved-session restoration, joined-room updates and sign-out without blocking GTK. A single SDK long-poll sync feeds room updates. Room selection opens an SDK-managed timeline, with a 200-event preview, older-message fetching, a composer, queued/failed status and a retry control. Drafts are kept separately while changing rooms. The conversations window lists invitations with their sender and supports accepting or declining them. New direct conversations and private groups confirm encryption before inviting participants; malformed addresses are rejected before room creation. Saved session credentials and the SDK store passphrase go to Secret Service; the SDK encrypts private data in the local SQLite store. There is no plaintext credential fallback. The sign-in controls require an explicit test-account selection. Each room shows its encryption state; sending to an unencrypted room is blocked unless the user explicitly allows it for that selection.

Device verification and recovery controls are implemented and tested against a private fixture. Extended history, independent-client interoperability and the rest of the release checklist are not complete. Do not use this build for personal conversations. A successful compiler check does not establish working end-to-end messaging.

Incoming SAS verification has an intermittent timeout in the combined fixture test. Successful isolated runs do not resolve that failure; verification reliability remains a release blocker.

The development window follows the selected desktop palette through GTK4 application styles, including its account dialogs. It uses rounded surfaces, client-side window controls, a scrolling connection list and wrapping action groups. The signed-out layout passed a 900 × 600 resize check, and all twelve factory palette styles parsed without errors. These checks do not establish the final design or complete accessibility coverage.

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

`tests/palette-windows.py` checks live palette switching in an isolated configuration using the installed development launcher. It captures the twelve window variants and checks their content backgrounds against the factory palette. It requires the X11 desktop, `wmctrl`, Python GI/GDK3 and the installed development binary. It does not change the active user's appearance settings.

## Measured baseline

The unconnected development window used 200,848 KiB resident memory and 0% of one CPU core during a five-second idle sample in a software-rendered VirtualBox guest. This is a baseline for the empty shell, not a benchmark for a connected messaging session or a performance guarantee. Connected idle, synchronization, history, attachments and calls still require measurements.

## Verified development checks

A disposable loopback-only Synapse fixture passed protected login, same-device session restoration and sign-out. A two-account test confirmed that the server stored `m.room.encrypted` while the receiving SDK timeline decrypted the expected body. The actual GTK controls passed test-account login, existing-room selection, queued send, server acceptance and sign-out. The fixture uses a test-only CA hook; normal builds do not add this certificate or bypass TLS verification. The owner's desktop keyring is not used by these tests. A separate device-verification test passed cancellation without trust, refusal to confirm before numbers are available, retry, matching SAS numbers and verified-device state. The GTK device-security window passed outgoing verification against a second SDK device, including comparison of the displayed numbers and explicit confirmation. Room filtering, single-window activation and closing the account worker were also checked. Incoming requests show the account and device, require acceptance, support cancellation, and still require an explicit number match. The GTK fixture passed both declined and confirmed incoming requests. Recovery tests restored cross-signing keys on a new device, rejected an invalid key and decrypted an older message from the encrypted backup with the original device's sync stopped. Recovery uses on-demand key downloads for opened messages. Backup creation and cross-signing setup remain explicit actions; they are not enabled automatically at login. The GTK recovery controls passed password-authenticated setup, saving-key acknowledgement, invalid-key rejection and restoration on a new device. Closing or signing out is blocked until a newly displayed key has been acknowledged as saved. Existing recovery cannot be overwritten through setup. Unsupported provider authentication methods produce an explanation rather than resetting the identity. These checks do not replace external-client interoperability, broader provider coverage or independent security review.

## Release gates

See [the release checklist](RELEASE_CHECKLIST.md). Live-account login/restoration, timelines, send/retry, device verification, recovery, account removal, accessibility, theme integration and independent-client interoperability must pass before installer inclusion. No ShadowRealm-operated homeserver is required; users choose their own Matrix provider.
