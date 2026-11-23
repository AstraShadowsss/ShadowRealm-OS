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
    Devices,
    VerifyDevice{user_id:String,device_id:String},
    VerificationTick(String),
    ConfirmVerification(String),
    CancelVerification(String),
    Logout,
}
pub enum Event {
    Connected,
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
                        Command::Devices=>{
                            let account=session.as_ref().ok_or("Sign in first.")?;
                            let (user_id,devices)=crate::verification::own_devices(account.client()).await?;
                            let _=events.send(Event::Devices{user_id,devices}).await;
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
                            if state==crate::verification::State::Ready&&flow.sas_handle().is_none(){flow.start_numbers().await?;state=flow.state();}
                            if !sas_observed{if let Some(sas)=flow.sas_handle(){let tx=internal_commands.clone();let id=id.clone();verification_tasks.push(tokio::spawn(async move{use futures_util::StreamExt;let mut changes=Box::pin(sas.changes());while changes.next().await.is_some(){if tx.send(Command::VerificationTick(id.clone())).await.is_err(){break;}}}));sas_observed=true;}}
                            if matches!(state,crate::verification::State::Verified|crate::verification::State::Cancelled){for task in verification_tasks.drain(..){task.abort();}}
                            let _=events.send(Event::Verification{flow_id:id,state}).await;
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
                if sync_task.is_none(){if let Some(account)=session.as_ref(){sync_task=Some(start_sync(account.clone(),events.clone()));}}
                if let Err(message)=result{if events.send(Event::Error(message)).await.is_err(){break;}}
            }
        });
    }).expect("Messenger account worker");
    (commands,updates)
}

fn start_sync(account:Session,events:Sender<Event>)->tokio::task::JoinHandle<()>{
    tokio::spawn(async move{
        let client=account.client().clone();let updates=events.clone();
        let result=client.sync_with_callback(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(30)),move |_|{
            let account=account.clone();let updates=updates.clone();
            async move{
                match account.connections().await{
                    Ok(rooms)=>if updates.send(Event::Rooms(rooms)).await.is_err(){return matrix_sdk::LoopCtrl::Break;},
                    Err(message)=>{let _=updates.send(Event::Error(message)).await;}
                }
                matrix_sdk::LoopCtrl::Continue
            }
        }).await;
        if result.is_err(){let _=events.send(Event::Error("Conversation sync stopped. Restore the saved account to reconnect.".into())).await;}
    })
}
