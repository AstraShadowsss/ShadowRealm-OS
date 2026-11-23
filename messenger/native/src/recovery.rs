//! Recovery keys and encrypted backup are managed by the Matrix SDK, never custom cryptography.
use matrix_sdk::{Client,encryption::recovery::RecoveryState};
use zeroize::Zeroizing;

pub fn state(client:&Client)->RecoveryState{client.encryption().recovery().state()}

/// Called only after the user explicitly requests recovery setup.
pub async fn enable(client:&Client)->Result<Zeroizing<String>,String>{
    let encryption=client.encryption();
    encryption.bootstrap_cross_signing_if_needed(None).await
        .map_err(|_|"Cross-signing setup requires authentication. Existing identities have not been reset.".to_owned())?;
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
