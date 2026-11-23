//! Persistent credentials use Secret Service only; there is no plaintext fallback.
use keyring::{Entry, Error};
use zeroize::Zeroizing;

const SERVICE: &str = "org.shadowrealm_os.Messenger";

pub struct Vault { entry: Entry }
impl Vault {
    pub fn primary_account() -> Result<Self, &'static str> {
        Entry::new(SERVICE, "primary-account")
            .map(|entry| Self { entry })
            .map_err(|_| "The desktop keyring could not be opened.")
    }
    pub fn load(&self) -> Result<Option<Zeroizing<String>>, &'static str> {
        match self.entry.get_password() {
            Ok(value) => Ok(Some(Zeroizing::new(value))),
            Err(Error::NoEntry) => Ok(None),
            Err(_) => Err("Unlock the desktop keyring to restore this account."),
        }
    }
    pub fn save(&self, serialized_session: &str) -> Result<(), &'static str> {
        self.entry.set_password(serialized_session)
            .map_err(|_| "The account was not saved. Unlock the desktop keyring and try again.")
    }
    pub fn remove(&self) -> Result<(), &'static str> {
        match self.entry.delete_credential() {
            Ok(()) | Err(Error::NoEntry) => Ok(()),
            Err(_) => Err("The saved account could not be removed from the desktop keyring."),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    #[ignore = "requires a separate disposable Secret Service session"]
    fn secret_service_round_trip(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        let vault=Vault{entry:Entry::new(SERVICE,"storage-regression").unwrap()};
        assert!(vault.load().unwrap().is_none());
        vault.save("non-sensitive test session payload").unwrap();
        assert_eq!(vault.load().unwrap().unwrap().as_str(),"non-sensitive test session payload");
        vault.remove().unwrap();assert!(vault.load().unwrap().is_none());
    }
}
