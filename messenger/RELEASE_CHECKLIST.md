# Shadow Messenger release checklist

Shadow Messenger is a required part of the next installer. The current r4 image does not contain it.

- [x] Editable native GTK and Matrix adapter source.
- [x] Independent core validation and ordering tests.
- [x] Compile and run the native application on Debian stable.
- [ ] Homeserver login and clear server/account error handling.
- [x] Validate same-device session persistence and restoration against the isolated Matrix fixture, with protected Secret Service storage.
- [x] Outgoing device verification through the actual GTK controls, including explicit number comparison.
- [x] Recovery backend: cross-signing restoration and older-history decryption from encrypted backup.
- [x] Incoming prompts, cancellation and explicit number confirmation implemented through GTK.
- [ ] Resolve intermittent incoming-verification timeout in the combined fixture test.
- [x] Recovery setup/restoration controls, saved-key acknowledgement and password-authentication challenges against the private fixture.
- [ ] Broader provider authentication and independent-client verification/recovery.
- [ ] Conversation list, incoming history, send/retry and offline recovery.
- [ ] Device verification, encryption status, recovery and account removal.
- [x] Private-fixture invitation acceptance/decline and encrypted direct/group creation.
- [ ] Presence, away messages and privacy preferences.
- [ ] Attachments, notifications and detached conversations.
- [x] Twelve factory GTK4 palette styles parse; signed-out controls fit a 900 × 600 window.
- [ ] Complete theme/accessibility and connected-window small-screen coverage.
- [ ] Independent-client interoperability and live-account tests.
- [ ] Dependency lockfiles, third-party notices, Debian package and launcher.
- [ ] Actual screenshots and matching user documentation.
- [ ] Fresh-profile and encrypted-install checks before installer inclusion.

Passwords, access tokens, recovery keys and message content must not appear in logs. Failed sends must preserve drafts. A locked keyring must produce a clear prompt or error without silently falling back to unprotected storage.
