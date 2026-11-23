//! One account worker owns the session; GTK never blocks on network or keyring work.
use async_channel::{Sender,Receiver};
use shadow_messenger_core::Connection;
use zeroize::Zeroizing;
use crate::matrix::Session;

pub enum Command {
    Login {server:String,username:String,password:Zeroizing<String>},
    Restore,
    Refresh,
    OpenRoom(String),
    LoadOlder,
    Send{room_id:String,body:String,allow_unencrypted:bool},
    RetryPending,
    Invitations,
    RespondInvitation{room_id:String,accept:bool},
    CreateConversation{name:String,people:String},
    Devices,
    RecoveryStatus,
    EnableRecovery(Option<Zeroizing<String>>),
    RestoreRecovery(Zeroizing<String>),
    IncomingVerification{for_device:String,request:matrix_sdk::encryption::verification::VerificationRequest,peer_device:String},
    AcceptVerification(String),
    VerifyDevice{user_id:String,device_id:String},
    VerificationTick(String),
    ConfirmVerification(String),
    CancelVerification(String),
    Logout,
}
pub enum Event {
    Connected,
    Invitations(Vec<crate::conversations::Invitation>),
    ConversationAction(String),
    ConversationCreated{room_id:String,message:String},
    RecoveryStatus{message:String,can_create:bool},
    RecoveryKey(Zeroizing<String>),
    RecoveryRestored,
    Devices{user_id:String,devices:Vec<crate::verification::DeviceInfo>},
    Verification{flow_id:String,state:crate::verification::State},
    Queued{room_id:String,body:String},
    RoomSecurity{room_id:String,encrypted:bool},
    Rooms(Vec<Connection>),
    SignedOut,
    Timeline{room_id:String,messages:Vec<crate::timeline::Message>},
    Error(String),
}
pub fn start()->(Sender<Command>,Receiver<Event>){
    let (commands,requests)=async_channel::bounded(4);
    let (events,updates)=async_channel::bounded(8);
    let internal_commands=commands.clone();
    std::thread::Builder::new().name("Messenger account".into()).spawn(move||{
        let runtime=match tokio::runtime::Builder::new_multi_thread().worker_threads(2).thread_name("Messenger IO").enable_all().build(){
            Ok(runtime)=>runtime,
            Err(_)=>{let _=events.send_blocking(Event::Error("The account worker could not start.".into()));return;}
        };
        runtime.block_on(async move {
            let mut session:Option<Session>=None;
            let mut verification:Option<crate::verification::VerificationFlow>=None;
            let mut verification_tasks:Vec<tokio::task::JoinHandle<()>>=Vec::new();
            let mut sas_observed=false;

            let mut sync_task:Option<tokio::task::JoinHandle<()>>=None;
            let mut timeline:Option<crate::timeline::RoomTimeline>=None;
            let mut forward:Option<tokio::task::JoinHandle<()>>=None;
            while let Ok(command)=requests.recv().await {
                if sync_task.as_ref().is_some_and(|task|task.is_finished()){sync_task=None;}
                let result:Result<(),String>=async {
                    match command {
                        Command::Login{server,username,password}=>{
                            if session.is_some(){return Err("Sign out before adding another account.".into());}
                            session=Some(Session::login(server,username,password).await?);
                            let _=events.send(Event::Connected).await;
                            let rooms=session.as_ref().unwrap().connections().await?;
                            let _=events.send(Event::Rooms(rooms)).await;
                        }
                        Command::Restore=>{
                            if session.is_none(){session=Session::restore().await?;}
                            if let Some(account)=session.as_ref(){
                                let _=events.send(Event::Connected).await;
                                let _=events.send(Event::Rooms(account.connections().await?)).await;
                            }else{let _=events.send(Event::SignedOut).await;}
                        }
                        Command::Refresh=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;
                            let _=events.send(Event::Rooms(account.connections().await?)).await;
                        }
                        Command::OpenRoom(room_id)=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;
                            let opened=crate::timeline::RoomTimeline::open(account.client(),&room_id).await?;
                            let _=events.send(Event::RoomSecurity{room_id:room_id.clone(),encrypted:opened.encrypted().await?}).await;
                            if let Some(task)=forward.take(){task.abort();}
                            let messages=opened.updates.clone();let events=events.clone();
                            forward=Some(tokio::spawn(async move{
                                while let Ok(messages)=messages.recv().await{
                                    if events.send(Event::Timeline{room_id:room_id.clone(),messages}).await.is_err(){break;}
                                }
                            }));
                            timeline=Some(opened);
                        }
                        Command::LoadOlder=>{
                            timeline.as_ref().ok_or("Choose a conversation first.")?.older_messages().await?;
                        }
                        Command::Send{room_id,body,allow_unencrypted}=>{
                            let opened=timeline.as_ref().ok_or("Choose a conversation first.")?;
                            if opened.room_id()!=room_id{return Err("The selected conversation changed. Your draft was kept.".into());}
                            opened.queue_message(&body,allow_unencrypted).await?;let _=events.send(Event::Queued{room_id,body}).await;
                        }
                        Command::RetryPending=>{
                            timeline.as_ref().ok_or("Choose a conversation first.")?.retry_pending();
                        }
                        Command::Invitations=>{
                            let client=session.as_ref().ok_or("Sign in first.")?.client();let _=events.send(Event::Invitations(crate::conversations::invitations(client).await)).await;
                        }
                        Command::RespondInvitation{room_id,accept}=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;crate::conversations::respond(account.client(),&room_id,accept).await?;
                            let _=events.send(Event::Invitations(crate::conversations::invitations(account.client()).await)).await;
                            let _=events.send(Event::Rooms(account.connections().await?)).await;
                            let _=events.send(Event::ConversationAction(if accept{"Invitation accepted."}else{"Invitation declined."}.into())).await;
                        }
                        Command::CreateConversation{name,people}=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;let (room_id,message)=crate::conversations::create(account.client(),&name,&people).await?;
                            let _=events.send(Event::Rooms(account.connections().await?)).await;let _=events.send(Event::ConversationCreated{room_id,message}).await;
                        }
                        Command::RecoveryStatus=>{
                            let client=session.as_ref().ok_or("Sign in first.")?.client();
                            use matrix_sdk::encryption::recovery::RecoveryState;
                            let (message,can_create)=match crate::recovery::state(client){
                                RecoveryState::Unknown=>("Recovery status is not ready. Wait for account sync, then refresh.",false),
                                RecoveryState::Disabled=>("Recovery is not configured for this account. Set it up here, or restore an existing key if you already have one.",true),
                                RecoveryState::Incomplete=>("This account has recovery. Restore the existing key to unlock encrypted history on this device.",false),
                                RecoveryState::Enabled=>("Recovery is enabled on this device. Keep your existing key in a safe place.",false),
                            };let _=events.send(Event::RecoveryStatus{message:message.into(),can_create}).await;
                        }
                        Command::EnableRecovery(password)=>{
                            let client=session.as_ref().ok_or("Sign in first.")?.client();
                            let key=crate::recovery::enable_with_password(client,password).await?;
                            let _=events.send(Event::RecoveryKey(key)).await;
                            tokio::time::timeout(std::time::Duration::from_secs(30),crate::recovery::wait_for_upload(client)).await
                                .map_err(|_|"Keep your recovery key. Backup upload is still pending; keep this device available and check your connection.")??;
                            let _=events.send(Event::RecoveryStatus{message:"Encrypted key backup uploaded. Save your recovery key somewhere safe before closing.".into(),can_create:false}).await;
                        }
                        Command::RestoreRecovery(key)=>{
                            let client=session.as_ref().ok_or("Sign in first.")?.client();crate::recovery::restore_key(client,key).await?;
                            let _=events.send(Event::RecoveryRestored).await;
                        }
                        Command::Devices=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;
                            let (user_id,devices)=crate::verification::own_devices(account.client()).await?;
                            let _=events.send(Event::Devices{user_id,devices}).await;
                        }
                        Command::IncomingVerification{for_device,request,peer_device}=>{
                            let Some(account)=session.as_ref().filter(|account|account.client().device_id().is_some_and(|device|device.as_str()==for_device)) else{return Ok(())};
                            if verification.as_ref().is_some_and(|flow|!matches!(flow.state(),crate::verification::State::Verified|crate::verification::State::Cancelled)){
                                request.cancel().await.map_err(|_|"Another verification is active; the incoming request could not be declined.")?;return Ok(());
                            }
                            for task in verification_tasks.drain(..){task.abort();}sas_observed=false;
                            let flow=crate::verification::VerificationFlow::incoming(account.client(),request,peer_device);
                            verification_tasks.push(observe_request(&flow,internal_commands.clone()));
                            let _=events.send(Event::Verification{flow_id:flow.flow_id().to_owned(),state:flow.state()}).await;verification=Some(flow);
                        }
                        Command::AcceptVerification(id)=>{
                            let flow=verification.as_mut().filter(|flow|flow.flow_id()==id).ok_or("This verification is no longer active.")?;
                            flow.accept_pending().await?;let _=internal_commands.try_send(Command::VerificationTick(id));
                        }
                        Command::VerifyDevice{user_id,device_id}=>{
                            if verification.as_ref().is_some_and(|flow|!matches!(flow.state(),crate::verification::State::Verified|crate::verification::State::Cancelled)){return Err("Finish or cancel the current verification first.".into());}
                            for task in verification_tasks.drain(..){task.abort();}sas_observed=false;
                            let user:matrix_sdk::ruma::OwnedUserId=user_id.parse().map_err(|_|"Invalid Matrix account.")?;
                            let device:matrix_sdk::ruma::OwnedDeviceId=device_id.into();
                            let flow=crate::verification::VerificationFlow::request(session.as_ref().ok_or("Sign in first.")?.client(),&user,&device).await?;
                            let request=flow.request_handle();let tx=internal_commands.clone();let id=flow.flow_id().to_owned();
                            verification_tasks.push(tokio::spawn(async move{use futures_util::StreamExt;let mut changes=Box::pin(request.changes());while changes.next().await.is_some(){if tx.send(Command::VerificationTick(id.clone())).await.is_err(){break;}}}));
                            let _=events.send(Event::Verification{flow_id:flow.flow_id().to_owned(),state:flow.state()}).await;
                            verification=Some(flow);
                        }
                        Command::VerificationTick(id)=>{
                            let Some(flow)=verification.as_mut().filter(|flow|flow.flow_id()==id) else{return Ok(())};
                            let mut state=flow.refresh().await?;
                            if state==crate::verification::State::Ready&&flow.sas_handle().is_none()&&flow.request_handle().we_started(){flow.start_numbers().await?;state=flow.state();}
                            if !sas_observed{if let Some(sas)=flow.sas_handle(){let tx=internal_commands.clone();let id=id.clone();verification_tasks.push(tokio::spawn(async move{use futures_util::StreamExt;let mut changes=Box::pin(sas.changes());while changes.next().await.is_some(){if tx.send(Command::VerificationTick(id.clone())).await.is_err(){break;}}}));sas_observed=true;}}
                            if matches!(state,crate::verification::State::Verified|crate::verification::State::Cancelled){for task in verification_tasks.drain(..){task.abort();}}
                            let verified=state==crate::verification::State::Verified;
                            let _=events.send(Event::Verification{flow_id:id,state}).await;
                            if verified{if let Some(account)=session.as_ref(){if let Ok((user_id,devices))=crate::verification::own_devices(account.client()).await{let _=events.send(Event::Devices{user_id,devices}).await;}}}
                        }
                        Command::ConfirmVerification(id)=>{
                            let flow=verification.as_ref().filter(|flow|flow.flow_id()==id).ok_or("This verification is no longer active.")?;
                            flow.confirm_match().await?;
                        }
                        Command::CancelVerification(id)=>{
                            let flow=verification.as_ref().filter(|flow|flow.flow_id()==id).ok_or("This verification is no longer active.")?;
                            flow.cancel().await?;let _=events.send(Event::Verification{flow_id:id,state:crate::verification::State::Cancelled}).await;
                            for task in verification_tasks.drain(..){task.abort();}
                        }
                        Command::Logout=>{
                            if let Some(account)=session.as_ref(){account.logout().await?;}
                            if let Some(task)=forward.take(){task.abort();}if let Some(task)=sync_task.take(){task.abort();}for task in verification_tasks.drain(..){task.abort();}verification=None;timeline=None;session=None;let _=events.send(Event::SignedOut).await;
                        }
                    }
                    Ok(())
                }.await;
                if sync_task.is_none(){if let Some(account)=session.as_ref(){sync_task=Some(start_sync(account.clone(),events.clone(),internal_commands.clone()));}}
                if let Err(message)=result{if events.send(Event::Error(message)).await.is_err(){break;}}
            }
        });
    }).expect("Messenger account worker");
    (commands,updates)
}

fn start_sync(account:Session,events:Sender<Event>,commands:Sender<Command>)->tokio::task::JoinHandle<()>{
    tokio::spawn(async move{
        let client=account.client().clone();let updates=events.clone();
        let handler_client=client.clone();let handle=client.add_event_handler(move|event:matrix_sdk::ruma::events::key::verification::request::ToDeviceKeyVerificationRequestEvent|{
            let client=handler_client.clone();let commands=commands.clone();async move{
                if let (Some(device),Some(request))=(client.device_id(),client.encryption().get_verification_request(&event.sender,event.content.transaction_id.as_str()).await){
                    if request.we_started(){return;}
                    let _=commands.send(Command::IncomingVerification{for_device:device.to_string(),request,peer_device:event.content.from_device.to_string()}).await;
                }
            }
        });let _handler_guard=client.event_handler_drop_guard(handle);
        let result=client.sync_with_callback(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(30)),move |_|{
            let account=account.clone();let updates=updates.clone();
            async move{
                match account.connections().await{
                    Ok(rooms)=>if updates.send(Event::Rooms(rooms)).await.is_err(){return matrix_sdk::LoopCtrl::Break;},
                    Err(message)=>{let _=updates.send(Event::Error(message)).await;}
                }
                if updates.send(Event::Invitations(crate::conversations::invitations(account.client()).await)).await.is_err(){return matrix_sdk::LoopCtrl::Break;}
                matrix_sdk::LoopCtrl::Continue
            }
        }).await;
        if result.is_err(){let _=events.send(Event::Error("Conversation sync stopped. Restore the saved account to reconnect.".into())).await;}
    })
}

fn observe_request(flow:&crate::verification::VerificationFlow,commands:Sender<Command>)->tokio::task::JoinHandle<()>{
    let request=flow.request_handle();let id=flow.flow_id().to_owned();tokio::spawn(async move{use futures_util::StreamExt;let mut changes=Box::pin(request.changes());while changes.next().await.is_some(){if commands.send(Command::VerificationTick(id.clone())).await.is_err(){break;}}})
}
