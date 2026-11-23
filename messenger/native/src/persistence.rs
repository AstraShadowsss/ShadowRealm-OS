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

pub(crate) fn client_builder(server:&str)->Result<matrix_sdk::ClientBuilder,String>{
    let builder=Client::builder().homeserver_url(server).with_encryption_settings(matrix_sdk::encryption::EncryptionSettings{auto_enable_cross_signing:false,auto_enable_backups:false,backup_download_strategy:matrix_sdk::encryption::BackupDownloadStrategy::AfterDecryptionFailure});
    #[cfg(test)]
    let builder=if let Ok(path)=std::env::var("SHADOW_MESSENGER_TEST_CA"){
        if server!="https://localhost:18448"{return Err("The test CA is restricted to the local fixture.".into());}
        let pem=fs::read(path).map_err(|_|"The local test certificate is unavailable.")?;
        let certificate=matrix_sdk::reqwest::Certificate::from_pem(&pem).map_err(|_|"Invalid local test certificate.")?;
        builder.add_root_certificates(vec![certificate])
    }else{builder};
    Ok(builder)
}

pub async fn login(server:String,username:String,password:Zeroizing<String>)->Result<Client,String>{
    let server=shadow_messenger_core::validate_homeserver(&server).map_err(str::to_owned)?;
    if saved().await?.is_some(){return Err("Restore or remove the saved account before adding another.".into());}
    let id=random_hex(16)?.to_string();let key=random_hex(32)?;let path=database_path(&id)?;
    fs::DirBuilder::new().mode(0o700).create(&path).map_err(|_|"Could not create private account storage.")?;
    let client=client_builder(&server)?.sqlite_store(path,Some(key.as_str())).build().await
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
    let client=client_builder(&server)?.sqlite_store(database_path(&account.database_id)?,Some(account.store_key.as_str())).build().await
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

#[cfg(test)]
mod matrix_integration {
    use super::*;
    #[tokio::test(flavor="multi_thread",worker_threads=2)]
    #[ignore = "requires the isolated keyring and disposable local Matrix fixture"]
    async fn login_restore_and_sign_out(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        let fixture=std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap();
        let account:serde_json::Value=serde_json::from_str(&fs::read_to_string(fixture).unwrap()).unwrap();
        assert!(restore().await.unwrap().is_none());
        let client=login(account["server"].as_str().unwrap().into(),account["username"].as_str().unwrap().into(),Zeroizing::new(account["password"].as_str().unwrap().into())).await.unwrap();
        let user=client.user_id().unwrap().to_owned();let device=client.device_id().unwrap().to_owned();
        client.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
        drop(client);
        let restored=restore().await.unwrap().unwrap();
        assert_eq!(restored.user_id(),Some(user.as_ref()));assert_eq!(restored.device_id(),Some(device.as_ref()));
        forget(&restored).await.unwrap();drop(restored);
        assert!(restore().await.unwrap().is_none());
    }
}

#[cfg(test)]
mod encrypted_message_integration {
    use super::*;
    use std::time::Duration;
    #[tokio::test(flavor="multi_thread",worker_threads=2)]
    #[ignore = "requires disposable local Matrix accounts and isolated Secret Service"]
    async fn encrypted_message_reaches_sdk_timeline(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        tokio::time::timeout(Duration::from_secs(90),async{
            let account:serde_json::Value=serde_json::from_str(&fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
            let server=account["server"].as_str().unwrap();
            let alice=login(server.into(),account["username"].as_str().unwrap().into(),Zeroizing::new(account["password"].as_str().unwrap().into())).await.unwrap();
            let bob=client_builder(server).unwrap().build().await.unwrap();
            bob.matrix_auth().login_username(account["bob_username"].as_str().unwrap(),account["bob_password"].as_str().unwrap()).send().await.unwrap();
            let a=alice.clone();let a_sync=tokio::spawn(async move{a.sync(matrix_sdk::config::SyncSettings::default().timeout(Duration::from_secs(1))).await});
            let b=bob.clone();let b_sync=tokio::spawn(async move{b.sync(matrix_sdk::config::SyncSettings::default().timeout(Duration::from_secs(1))).await});
            let room=alice.create_room(matrix_sdk::ruma::api::client::room::create_room::v3::Request::new()).await.unwrap();
            let unencrypted=crate::timeline::RoomTimeline::open(&alice,room.room_id().as_str()).await.unwrap();
            assert!(unencrypted.queue_message("Must not be sent without consent",false).await.is_err());drop(unencrypted);
            room.enable_encryption().await.unwrap();
            room.invite_user_by_id(bob.user_id().unwrap()).await.unwrap();
            let bob_room=bob.join_room_by_id(room.room_id()).await.unwrap();
            let timeline=crate::timeline::RoomTimeline::open(&alice,room.room_id().as_str()).await.unwrap();
            let body="Disposable encrypted timeline regression message";
            let sent=bob_room.send(matrix_sdk::ruma::events::room::message::RoomMessageEventContent::text_plain(body)).await.unwrap();
            let certificate=matrix_sdk::reqwest::Certificate::from_pem(&fs::read(std::env::var("SHADOW_MESSENGER_TEST_CA").unwrap()).unwrap()).unwrap();
            let http=matrix_sdk::reqwest::Client::builder().add_root_certificate(certificate).build().unwrap();
            let raw=http.get(format!("{server}/_matrix/client/v3/rooms/{}/event/{}",room.room_id(),sent.response.event_id)).bearer_auth(alice.access_token().unwrap()).send().await.unwrap().bytes().await.unwrap();
            let raw:serde_json::Value=serde_json::from_slice(&raw).unwrap();
            assert_eq!(raw["type"],"m.room.encrypted");assert!(raw["content"].get("body").is_none());
            loop{let rows=timeline.updates.recv().await.unwrap();if rows.iter().any(|message|message.body==body){break;}}
            drop(timeline);a_sync.abort();b_sync.abort();bob.logout().await.unwrap();forget(&alice).await.unwrap();
        }).await.expect("Encrypted fixture exchange exceeded its time limit");
    }
}

#[cfg(test)]
mod device_verification_integration {
    use super::*;
    use crate::verification::{VerificationFlow,State};
    use std::time::Duration;
    #[tokio::test(flavor="multi_thread",worker_threads=2)]
    #[ignore = "requires disposable Matrix accounts and isolated Secret Service"]
    async fn matching_numbers_verify_the_other_device(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        tokio::time::timeout(Duration::from_secs(90),async{
            let account:serde_json::Value=serde_json::from_str(&fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
            let server=account["server"].as_str().unwrap();let username=account["username"].as_str().unwrap();let password=account["password"].as_str().unwrap();
            let first=login(server.into(),username.into(),Zeroizing::new(password.into())).await.unwrap();
            let second=client_builder(server).unwrap().build().await.unwrap();second.matrix_auth().login_username(username,password).send().await.unwrap();
            second.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
            first.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
            let _=first.encryption().request_user_identity(second.user_id().unwrap()).await.unwrap();
            let a=first.clone();let a_sync=tokio::spawn(async move{a.sync(matrix_sdk::config::SyncSettings::default().timeout(Duration::from_secs(1))).await});
            let b=second.clone();let b_sync=tokio::spawn(async move{b.sync(matrix_sdk::config::SyncSettings::default().timeout(Duration::from_secs(1))).await});
            loop{if first.encryption().get_device(second.user_id().unwrap(),second.device_id().unwrap()).await.unwrap().is_some(){break;}tokio::time::sleep(Duration::from_millis(100)).await;}
            eprintln!("verification stage: device available");
            let cancelled=VerificationFlow::request(&first,second.user_id().unwrap(),second.device_id().unwrap()).await.unwrap();
            assert!(cancelled.confirm_match().await.is_err());
            cancelled.cancel().await.unwrap();assert!(cancelled.state()==State::Cancelled);
            assert!(!first.encryption().get_device(second.user_id().unwrap(),second.device_id().unwrap()).await.unwrap().unwrap().is_verified());
            eprintln!("verification stage: cancellation checked");
            let mut outgoing=VerificationFlow::request(&first,second.user_id().unwrap(),second.device_id().unwrap()).await.unwrap();
            let request=loop{if let Some(request)=second.encryption().get_verification_request(first.user_id().unwrap(),outgoing.flow_id()).await{break request;}tokio::time::sleep(Duration::from_millis(100)).await;};
            eprintln!("verification stage: retry received");
            let mut incoming=VerificationFlow::accept(&second,request).await.unwrap();
            while outgoing.refresh().await.unwrap()!=State::Ready{tokio::time::sleep(Duration::from_millis(100)).await;}
            eprintln!("verification stage: request ready");
            outgoing.start_numbers().await.unwrap();
            let numbers=loop{
                let a=outgoing.refresh().await.unwrap();let b=incoming.refresh().await.unwrap();
                if let (State::Compare(a),State::Compare(b))=(a,b){assert_eq!(a,b);break a;}
                tokio::time::sleep(Duration::from_millis(100)).await;
            };
            assert!(numbers.0>=1000&&numbers.1>=1000&&numbers.2>=1000);
            eprintln!("verification stage: numbers match");
            outgoing.confirm_match().await.unwrap();incoming.confirm_match().await.unwrap();
            while outgoing.refresh().await.unwrap()!=State::Verified||incoming.refresh().await.unwrap()!=State::Verified{tokio::time::sleep(Duration::from_millis(100)).await;}
            assert!(first.encryption().get_device(second.user_id().unwrap(),second.device_id().unwrap()).await.unwrap().unwrap().is_verified());
            a_sync.abort();b_sync.abort();second.logout().await.unwrap();forget(&first).await.unwrap();
        }).await.expect("Device verification exceeded its time limit");
    }
}

#[cfg(test)]
mod recovery_integration {
    use super::*;
    #[tokio::test(flavor="multi_thread",worker_threads=2)]
    #[ignore = "requires a fresh disposable account and isolated Secret Service"]
    async fn recovery_key_restores_cross_signing_on_a_new_device(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        tokio::time::timeout(std::time::Duration::from_secs(90),async{
            let account:serde_json::Value=serde_json::from_str(&fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
            let server=account["server"].as_str().unwrap();let username=account["recovery_username"].as_str().unwrap();let password=account["recovery_password"].as_str().unwrap();
            let first=login(server.into(),username.into(),Zeroizing::new(password.into())).await.unwrap();first.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
            if let Err(error)=first.encryption().bootstrap_cross_signing_if_needed(None).await{
                let response=error.as_uiaa_response().expect("Cross-signing setup failed without an authentication challenge");
                let mut auth=matrix_sdk::ruma::api::client::uiaa::Password::new(matrix_sdk::ruma::api::client::uiaa::UserIdentifier::from(first.user_id().unwrap().to_owned()),password.into());
                auth.session=response.session.clone();first.encryption().bootstrap_cross_signing(Some(matrix_sdk::ruma::api::client::uiaa::AuthData::Password(auth))).await.unwrap();
            }
            eprintln!("recovery stage: cross-signing ready");
            let sync_client=first.clone();let first_sync=tokio::spawn(async move{sync_client.sync(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(1))).await});
            let room=first.create_room(matrix_sdk::ruma::api::client::room::create_room::v3::Request::new()).await.unwrap();room.enable_encryption().await.unwrap();
            let body="Disposable backup recovery history message";
            room.send(matrix_sdk::ruma::events::room::message::RoomMessageEventContent::text_plain(body)).await.unwrap();
            eprintln!("recovery stage: encrypted event stored");
            let key=crate::recovery::enable(&first).await.unwrap();assert!(!key.is_empty());
            eprintln!("recovery stage: key created");
            tokio::time::timeout(std::time::Duration::from_secs(20),crate::recovery::wait_for_upload(&first)).await.expect("Encrypted backup upload timed out").unwrap();first_sync.abort();
            eprintln!("recovery stage: encrypted key backup uploaded");

            let second=client_builder(server).unwrap().build().await.unwrap();second.matrix_auth().login_username(username,password).send().await.unwrap();second.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
            assert!(crate::recovery::restore_key(&second,Zeroizing::new("invalid recovery key".into())).await.is_err());
            eprintln!("recovery stage: new device ready");
            crate::recovery::restore_key(&second,Zeroizing::new(key.to_string())).await.unwrap();
            eprintln!("recovery stage: identity restored");
            assert!(second.encryption().cross_signing_status().await.unwrap().is_complete());
            assert!(crate::recovery::state(&second)==matrix_sdk::encryption::recovery::RecoveryState::Enabled);
            let timeline=crate::timeline::RoomTimeline::open(&second,room.room_id().as_str()).await.unwrap();
            eprintln!("recovery stage: historical timeline open");
            loop{let messages=timeline.updates.recv().await.unwrap();if messages.iter().any(|message|message.body==body){break;}}
            drop(timeline);second.logout().await.unwrap();forget(&first).await.unwrap();
        }).await.expect("Recovery fixture exceeded its time limit");
    }
}
