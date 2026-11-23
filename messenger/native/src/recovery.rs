//! Recovery keys and encrypted backup are managed by the Matrix SDK, never custom cryptography.
use matrix_sdk::{Client,encryption::recovery::RecoveryState};
use zeroize::Zeroizing;

pub fn state(client:&Client)->RecoveryState{client.encryption().recovery().state()}

/// Called only after the user explicitly requests recovery setup.
#[cfg(test)]
pub async fn enable(client:&Client)->Result<Zeroizing<String>,String>{
    enable_with_password(client,None).await
}

pub async fn enable_with_password(client:&Client,password:Option<Zeroizing<String>>)->Result<Zeroizing<String>,String>{
    match state(client){
        RecoveryState::Enabled=>return Err("Recovery is already enabled. Keep using your existing recovery key.".into()),
        RecoveryState::Incomplete=>return Err("This account already has recovery. Restore its existing key before continuing.".into()),
        RecoveryState::Unknown=>return Err("Recovery status is not ready. Wait for account sync and refresh.".into()),
        RecoveryState::Disabled=>{},
    }
    let encryption=client.encryption();
    if let Err(error)=encryption.bootstrap_cross_signing_if_needed(None).await{
        let response=error.as_uiaa_response().ok_or("Cross-signing setup could not connect or complete. No identity reset was requested.")?;
        let password=password.filter(|value|!value.is_empty()).ok_or("Your homeserver requires authentication. Enter your account password and retry setup.")?;
        if !response.flows.iter().any(|flow|flow.stages.iter().any(|stage|stage.as_str()=="m.login.password")){
            return Err("This homeserver requires an authentication method not supported here. Set up recovery with another Matrix client, then restore its key here.".into());
        }
        let user=client.user_id().ok_or("Sign in first.")?;
        let mut auth=matrix_sdk::ruma::api::client::uiaa::Password::new(matrix_sdk::ruma::api::client::uiaa::UserIdentifier::from(user.to_owned()),password.to_string());auth.session=response.session.clone();
        encryption.bootstrap_cross_signing_if_needed(Some(matrix_sdk::ruma::api::client::uiaa::AuthData::Password(auth))).await
            .map_err(|_|"Account authentication did not complete. Check the password; no identity reset was requested.")?;
    }
    if !encryption.cross_signing_status().await.is_some_and(|status|status.is_complete()){
        return Err("Verify this device or restore the existing recovery key before creating a backup.".into());
    }
    let key=encryption.recovery().enable().await.map_err(|_|"Recovery setup could not finish. Existing backup data has not been deleted.".to_owned())?;
    Ok(Zeroizing::new(key))
}

pub async fn restore_key(client:&Client,key:Zeroizing<String>)->Result<(),String>{
    if key.trim().is_empty(){return Err("Enter the recovery key for this account.".into());}
    client.encryption().recovery().recover(key.trim()).await
        .map_err(|_|"The recovery key could not unlock this account. Check the key and connection; no identity reset was requested.".into())
}

pub async fn wait_for_upload(client:&Client)->Result<(),String>{
    client.encryption().backups().wait_for_steady_state().await
        .map_err(|_|"The encrypted key backup has not finished uploading. Keep this device available and retry.".into())
}
