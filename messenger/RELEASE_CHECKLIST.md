# Shadow Messenger release checklist

Shadow Messenger is a required part of the next installer. The current r4 image does not contain it.

- [x] Editable native GTK and Matrix adapter source.
- [x] Independent core validation and ordering tests.
- [x] Compile and run the native application on Debian stable.
- [ ] Homeserver login and clear server/account error handling against a live provider.
- [x] Account creation: registration UIA (dummy, password, token), dedicated Create account window and clear provider-policy messages; one end-to-end GUI registration and restore against the isolated Synapse fixture.
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
- [x] Presence, custom away messages and notification privacy preferences.
- [x] Notifications, notification sounds, Activity feed and detached conversation windows.
- [ ] Two-account incoming notification, mention priority and notification click actions.
- [ ] Attachments, calls and notification behaviour while the application is closed.
- [x] Twelve factory GTK4 palette styles parse; signed-out controls fit a 900 × 600 window.
- [x] Auxiliary windows open above the active conversation: Preferences, Conversations, Devices & security and Custom Away Message were checked with X11 transient/stacking properties. Preferences returns to the main window when the conversation is hidden.
- [x] Main, conversation and Preferences windows use native Xfwm4 frames and controls; compared with the system Terminal at 1280 × 800 in the Neon theme.
- [ ] Complete theme/accessibility and connected-window small-screen coverage. The signed-in shell was checked at 1180 × 720 in Neon, White/Silver/Gold and Professional; switches inherit the palette accent. Small-screen, keyboard-only and screen-reader passes remain.
- [ ] Independent-client interoperability and live-account tests.
- [x] Dependency lockfiles, Debian package builder, launcher and icon; package contents and runtime dependencies inspected.
- [ ] Third-party notices and license collection for binary distribution.
- [ ] Actual screenshots and matching user documentation.
- [ ] Fresh-profile and encrypted-install checks before installer inclusion.

Passwords, access tokens, recovery keys and message content must not appear in logs. Failed sends must preserve drafts. A locked keyring must produce a clear prompt or error without silently falling back to unprotected storage.
