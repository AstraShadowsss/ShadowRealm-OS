# Shadow Messenger development

A native GTK4 Matrix client for ShadowRealm-OS. It is not included in the installer or offered as a finished messaging application.

`core` contains account-server policy, message validation and connection ordering, with independent tests. `native` contains the GTK shell and an initial Matrix SDK adapter for password login, joined-room synchronization, sending and logout. The shell deliberately does not enable account login yet. The adapter still needs compilation and live test-account validation; no working encrypted messaging claim is made.

No ShadowRealm-operated homeserver is required. Users will choose their Matrix provider. Passwords, tokens and message contents must never be logged. Secure persistent storage, device verification, cross-signing, key backup/recovery, incoming history, account removal and error recovery are release gates, not optional polish.

## Build

Core tests: `cargo test --manifest-path core/Cargo.toml` (Rust 1.85 or later).

Native development: Rust 1.96 or later, GTK 4.8 development libraries, a C compiler, pkg-config and the Matrix SDK's platform dependencies. Run `CARGO_BUILD_JOBS=1 cargo check --manifest-path native/Cargo.toml` before attempting a GUI build. Dependency lockfiles and notices must be generated and reviewed before any binary is distributed.

The selected versions are Matrix SDK 0.19.1 and gtk4-rs 0.11.5. See the [Matrix SDK](https://docs.rs/matrix-sdk/0.19.1/matrix_sdk/) and [GTK Rust documentation](https://gtk-rs.org/gtk4-rs/stable/latest/book/). Original project code uses the repository's MIT license; dependencies retain their licenses.

## Next gates

1. Compile the adapter and native shell with the required toolchain.
2. Add Secret Service-backed session/crypto-store protection and verified account deletion.
3. Wire test-account login, incoming timelines and send/retry behavior into the UI.
4. Validate encryption, verification and recovery with independent Matrix clients.
5. Add presence/away messages, groups, detached conversations, notifications, attachments and theme following.
6. Package and capture actual application screenshots only after the relevant functionality passes.
