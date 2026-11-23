//! One account worker owns the session; GTK never blocks on network or keyring work.
use async_channel::{Sender,Receiver};
use shadow_messenger_core::Connection;
use zeroize::Zeroizing;
use crate::matrix::Session;

pub enum Command {
    Login {server:String,username:String,password:Zeroizing<String>},
    Restore,
    Refresh,
    Logout,
}
pub enum Event {
    Connected,
    Rooms(Vec<Connection>),
    SignedOut,
    Error(String),
}
pub fn start()->(Sender<Command>,Receiver<Event>){
    let (commands,requests)=async_channel::bounded(4);
    let (events,updates)=async_channel::bounded(8);
    std::thread::Builder::new().name("Messenger account".into()).spawn(move||{
        let runtime=match tokio::runtime::Builder::new_multi_thread().worker_threads(2).thread_name("Messenger IO").enable_all().build(){
            Ok(runtime)=>runtime,
            Err(_)=>{let _=events.send_blocking(Event::Error("The account worker could not start.".into()));return;}
        };
        runtime.block_on(async move {
            let mut session:Option<Session>=None;
            while let Ok(command)=requests.recv().await {
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
                        Command::Logout=>{
                            if let Some(account)=session.as_ref(){account.logout().await?;}
                            session=None;let _=events.send(Event::SignedOut).await;
                        }
                    }
                    Ok(())
                }.await;
                if let Err(message)=result{if events.send(Event::Error(message)).await.is_err(){break;}}
            }
        });
    }).expect("Messenger account worker");
    (commands,updates)
}
