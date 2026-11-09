# Recover an installation made with the withdrawn r2 ISO

The r2 live image stored the filesystem root with mode 0700. After installation, system services running as ordinary accounts could not traverse `/`. This could leave a console login screen and immediately close a login even when the password was correct. Reinstalling the same image does not solve it.

The fix is to restore only the installed filesystem root to owner root, group root, mode 0755. Do not recursively change permissions: private home directories, encryption keys and other protected files must keep their own permissions.

If the installed system is inaccessible, start a Linux live USB/ISO. Identify the installed root partition with `lsblk -f`. For an encrypted install, unlock that partition using its existing disk passphrase, then mount the unlocked root filesystem. For example, replacing `/dev/ROOT_PARTITION` with the partition you verified:

```sh
sudo cryptsetup open /dev/ROOT_PARTITION shadowrealm-recovery
sudo mkdir -p /mnt/shadowrealm-recovery
sudo mount /dev/mapper/shadowrealm-recovery /mnt/shadowrealm-recovery
sudo stat -c '%a %U:%G %n' /mnt/shadowrealm-recovery
sudo chown root:root /mnt/shadowrealm-recovery
sudo chmod 0755 /mnt/shadowrealm-recovery
sudo sync
sudo umount /mnt/shadowrealm-recovery
sudo cryptsetup close shadowrealm-recovery
```

For an unencrypted installation, mount the verified root partition directly and omit the `cryptsetup` commands. Reboot from the installed disk. This does not reset your account or disk passphrase and does not erase your files.

A controlled encrypted r2 installation was repaired using this one-directory permission correction. D-Bus, LightDM, NetworkManager and the themed desktop then started, and the original test-account password worked.
