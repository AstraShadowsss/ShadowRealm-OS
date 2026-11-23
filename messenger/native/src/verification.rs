//! Verification uses the SDK's SAS protocol. Matching is always an explicit user action.
use matrix_sdk::{Client,ruma::{UserId,DeviceId},encryption::verification::{VerificationRequest,SasVerification,Verification}};

pub struct VerificationFlow {
    client:Client,
    request:VerificationRequest,
    sas:Option<SasVerification>,
}
#[derive(Clone,PartialEq,Eq)]
pub enum State {Waiting,Ready,Compare((u16,u16,u16)),Verified,Cancelled}
impl VerificationFlow {
    pub async fn request(client:&Client,user:&UserId,device:&DeviceId)->Result<Self,String>{
        let _=client.encryption().request_user_identity(user).await.map_err(|_|"Could not refresh the selected user's device keys.")?;
        let peer=client.encryption().get_device(user,device).await.map_err(|_|"Could not load the selected device.")?
            .ok_or("The selected device is unavailable. Refresh devices first.")?;
        let request=peer.request_verification().await.map_err(|_|"The verification request could not be sent.")?;
        Ok(Self{client:client.clone(),request,sas:None})
    }
    pub async fn accept(client:&Client,request:VerificationRequest)->Result<Self,String>{
        request.accept().await.map_err(|_|"The verification request could not be accepted.")?;
        Ok(Self{client:client.clone(),request,sas:None})
    }
    pub fn request_handle(&self)->VerificationRequest{self.request.clone()}
    pub fn sas_handle(&self)->Option<SasVerification>{self.sas.clone()}
    pub fn flow_id(&self)->&str{self.request.flow_id()}
    pub async fn refresh(&mut self)->Result<State,String>{
        if self.sas.is_none(){
            if let Some(Verification::SasV1(sas))=self.client.encryption().get_verification(self.request.other_user_id(),self.request.flow_id()).await{
                sas.accept().await.map_err(|_|"Verification negotiation failed. Cancel and try again.")?;
                self.sas=Some(sas);
            }
        }
        Ok(self.state())
    }
    pub fn state(&self)->State{
        if self.request.is_cancelled()||self.sas.as_ref().is_some_and(|s|s.is_cancelled()){return State::Cancelled;}
        if self.request.is_done()||self.sas.as_ref().is_some_and(|s|s.is_done()){return State::Verified;}
        if let Some(numbers)=self.sas.as_ref().and_then(|s|s.decimals()){return State::Compare(numbers);}
        if self.request.is_ready(){State::Ready}else{State::Waiting}
    }
    pub async fn start_numbers(&mut self)->Result<(),String>{
        self.sas=self.request.start_sas().await.map_err(|_|"Number verification could not start.")?;
        if self.sas.is_none(){return Err("The other device must accept the request first.".into());}
        Ok(())
    }
    pub async fn confirm_match(&self)->Result<(),String>{
        let sas=self.sas.as_ref().filter(|s|s.decimals().is_some()&&!s.is_cancelled()).ok_or("The comparison numbers are not ready.")?;
        sas.confirm().await.map_err(|_|"The verification match could not be confirmed.".into())
    }
    pub async fn cancel(&self)->Result<(),String>{
        if let Some(sas)=self.sas.as_ref(){sas.cancel().await}else{self.request.cancel().await}
            .map_err(|_|"The verification cancellation could not be sent.".into())
    }
}

#[derive(Clone)]
pub struct DeviceInfo {pub id:String,pub name:String,pub verified:bool,pub current:bool}
pub async fn own_devices(client:&Client)->Result<(String,Vec<DeviceInfo>),String>{
    let user=client.user_id().ok_or("Sign in first.")?;
    let _=client.encryption().request_user_identity(user).await.map_err(|_|"Device keys could not be refreshed.")?;
    let devices=client.encryption().get_user_devices(user).await.map_err(|_|"Devices could not be loaded.")?;
    let mut devices:Vec<_>=devices.devices().map(|device|DeviceInfo{id:device.device_id().to_string(),name:device.display_name().unwrap_or("Unnamed Matrix device").to_owned(),verified:device.is_verified(),current:Some(device.device_id())==client.device_id()}).collect();
    devices.sort_by(|a,b|b.current.cmp(&a.current).then_with(||a.name.to_lowercase().cmp(&b.name.to_lowercase())).then_with(||a.id.cmp(&b.id)));
    Ok((user.to_string(),devices))
}
