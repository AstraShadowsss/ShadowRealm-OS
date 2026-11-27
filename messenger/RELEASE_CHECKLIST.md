# Shadow Messenger release checklist

Shadow Messenger is included in the private r5 development image as a test-account preview. It is not part of the public r4 image and must not be called production-ready.

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
- [x] Two-account incoming notification and mention priority in the fixture; Do Not Disturb suppression was checked.
- [ ] Notification click opens the conversation. A click was tried but did not open the main conversation. The notification now carries an explicit **Open** action button as well as the default action; the click still needs a fresh desktop test.
- [ ] Attachments, calls and notification behaviour while the application is closed.
- [x] Twelve factory GTK4 palette styles parse; signed-out controls fit a 900 × 600 window.
- [x] Auxiliary windows open above the active conversation: Preferences, Conversations, Devices & security and Custom Away Message were checked with X11 transient/stacking properties. Preferences returns to the main window when the conversation is hidden.
- [x] Main, conversation and Preferences windows use native Xfwm4 frames and controls; compared with the system Terminal at 1280 × 800 in the Neon theme.
- [ ] Complete theme/accessibility and connected-window small-screen coverage. The signed-in shell was checked at 1180 × 720 in Neon, White/Silver/Gold and Professional; switches inherit the palette accent. Small-screen, keyboard-only and screen-reader passes remain.
- [ ] Independent-client interoperability and live-account tests.
- [x] Dependency lockfiles, Debian package builder, launcher and a theme-generated icon family; package contents and runtime dependencies inspected.
- [x] Icon family covers menu, dock, desktop shortcut and window icon through the shared `shadow-messenger-app` name in all twelve palettes, with a hicolor fallback.
- [ ] Install the rebuilt 0.1.1 package from a fresh r5 image and confirm the icon, keyring dependency and launcher in the installed desktop.
- [ ] Third-party notices and license collection for binary distribution.
- [ ] Actual screenshots and matching user documentation.
- [ ] Fresh-profile and encrypted-install checks before installer inclusion.

Passwords, access tokens, recovery keys and message content must not appear in logs. Failed sends must preserve drafts. A locked keyring must produce a clear prompt or error without silently falling back to unprotected storage.
