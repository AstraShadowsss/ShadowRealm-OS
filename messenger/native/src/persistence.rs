//! SDK-encrypted local stores. Session tokens and store keys stay in Secret Service.
use std::{fs,io::Read,os::unix::fs::{DirBuilderExt,PermissionsExt},path::PathBuf};
use matrix_sdk::{Client,authentication::matrix::MatrixSession};
use serde::{Serialize,Deserialize};
use zeroize::{Zeroize,Zeroizing};
use crate::vault::Vault;

#[derive(Serialize,Deserialize)]
pub struct SavedAccount {
    version:u8,
    server:String,
    database_id:String,
    store_key:String,
    session:MatrixSession,
}
impl Drop for SavedAccount {fn drop(&mut self){self.store_key.zeroize();}}

fn data_root()->Result<PathBuf,String>{
    let root=std::env::var_os("XDG_DATA_HOME").map(PathBuf::from).filter(|p|p.is_absolute())
        .or_else(||std::env::var_os("HOME").map(PathBuf::from).filter(|p|p.is_absolute()).map(|p|p.join(".local/share")))
        .ok_or("The user data directory is unavailable.")?.join("shadow-messenger/accounts");
    fs::DirBuilder::new().recursive(true).mode(0o700).create(&root).map_err(|_|"Could not create private account storage.")?;
    let m=fs::symlink_metadata(&root).map_err(|_|"Account storage is unavailable.")?;
    if !m.is_dir() || m.permissions().mode()&0o077!=0 {return Err("Account storage must be a private directory.".into());}
    Ok(root)
}
fn database_path(id:&str)->Result<PathBuf,String>{
    if id.len()!=32 || !id.bytes().all(|c|c.is_ascii_hexdigit()){return Err("Saved account metadata is invalid.".into());}
    Ok(data_root()?.join(id))
}
fn random_hex(count:usize)->Result<Zeroizing<String>,String>{
    let mut bytes=Zeroizing::new(vec![0u8;count]);
    fs::File::open("/dev/urandom").and_then(|mut f|f.read_exact(&mut bytes)).map_err(|_|"Secure random data is unavailable.")?;
    Ok(Zeroizing::new(bytes.iter().map(|b|format!("{b:02x}")).collect()))
}
async fn saved()->Result<Option<Zeroizing<String>>,String>{
    tokio::task::spawn_blocking(||Vault::primary_account()?.load()).await
        .map_err(|_|"The keyring request could not finish.".to_owned())?.map_err(str::to_owned)
}

pub async fn login(server:String,username:String,password:Zeroizing<String>)->Result<Client,String>{
    let server=shadow_messenger_core::validate_homeserver(&server).map_err(str::to_owned)?;
    if saved().await?.is_some(){return Err("Restore or remove the saved account before adding another.".into());}
    let id=random_hex(16)?.to_string();let key=random_hex(32)?;let path=database_path(&id)?;
    fs::DirBuilder::new().mode(0o700).create(&path).map_err(|_|"Could not create private account storage.")?;
    let client=Client::builder().homeserver_url(&server).sqlite_store(path,Some(key.as_str())).build().await
        .map_err(|_|"Could not open the encrypted account store or connect to the homeserver.")?;
    client.matrix_auth().login_username(username,password.as_str()).initial_device_display_name("Shadow Messenger").send().await
        .map_err(|_|"Sign-in failed. Check the account, homeserver and supported login method.")?;
    let session=client.matrix_auth().session().ok_or("The server did not return an account session.")?;
    let account=SavedAccount{version:1,server,database_id:id,store_key:key.to_string(),session};
    let json=Zeroizing::new(serde_json::to_string(&account).map_err(|_|"The account session could not be saved.")?);
    let result=tokio::task::spawn_blocking(move||Vault::primary_account()?.save(json.as_str())).await
        .map_err(|_|"The keyring request could not finish.".to_owned())?;
    if result.is_err(){let _=client.logout().await;return Err("Sign-in was cancelled because the desktop keyring could not save the session.".into());}
    Ok(client)
}

pub async fn restore()->Result<Option<Client>,String>{
    let Some(json)=saved().await? else{return Ok(None)};
    if json.len()>1_000_000{return Err("Saved account metadata is invalid.".into());}
    let account:SavedAccount=serde_json::from_str(json.as_str()).map_err(|_|"Saved account metadata is invalid.")?;
    if account.version!=1{return Err("This saved account version is not supported.".into());}
    let server=shadow_messenger_core::validate_homeserver(&account.server).map_err(str::to_owned)?;
    let client=Client::builder().homeserver_url(server).sqlite_store(database_path(&account.database_id)?,Some(account.store_key.as_str())).build().await
        .map_err(|_|"Could not unlock the encrypted account store.")?;
    client.restore_session(account.session.clone()).await.map_err(|_|"The saved account could not be restored.")?;
    Ok(Some(client))
}

pub async fn forget(client:&Client)->Result<(),String>{
    client.logout().await.map_err(|_|"Server sign-out failed. The saved account has been kept so you can retry.")?;
    tokio::task::spawn_blocking(||Vault::primary_account()?.remove()).await
        .map_err(|_|"The keyring request could not finish.".to_owned())?.map_err(str::to_owned)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_account_path_traversal_before_opening_storage() {
        for id in ["", "../account", "/tmp/account", "0000000000000000000000000000000/", "gggggggggggggggggggggggggggggggg"] {
            assert!(database_path(id).is_err());
        }
    }
    #[test]
    fn store_keys_use_operating_system_randomness() {
        let a=random_hex(32).unwrap();let b=random_hex(32).unwrap();
        assert_eq!(a.len(),64);assert!(a.bytes().all(|c|c.is_ascii_hexdigit()));assert_ne!(a.as_str(),b.as_str());
    }
}
