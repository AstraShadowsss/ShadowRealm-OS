# Shadow Messenger release checklist

Shadow Messenger is a required part of the next installer. The current r4 image does not contain it.

- [x] Editable native GTK and Matrix adapter source.
- [x] Independent core validation and ordering tests.
- [x] Compile and run the native application on Debian stable.
- [ ] Homeserver login and clear server/account error handling.
- [x] Validate same-device session persistence and restoration against the isolated Matrix fixture, with protected Secret Service storage.
- [x] Outgoing device verification through the actual GTK controls, including explicit number comparison.
- [x] Recovery backend: cross-signing restoration and older-history decryption from encrypted backup.
- [ ] Incoming verification prompts, recovery controls and authentication challenges.
- [ ] Conversation list, incoming history, send/retry and offline recovery.
- [ ] Device verification, encryption status, recovery and account removal.
- [ ] Contacts/groups, presence and away messages.
- [ ] Attachments, notifications and detached conversations.
- [ ] System theme following and readable small-screen layouts.
- [ ] Independent-client interoperability and live-account tests.
- [ ] Dependency lockfiles, third-party notices, Debian package and launcher.
- [ ] Actual screenshots and matching user documentation.
- [ ] Fresh-profile and encrypted-install checks before installer inclusion.

Passwords, access tokens, recovery keys and message content must not appear in logs. Failed sends must preserve drafts. A locked keyring must produce a clear prompt or error without silently falling back to unprotected storage.
