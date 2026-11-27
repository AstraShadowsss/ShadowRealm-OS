//! SDK-managed timelines, with one cancellable subscription per open conversation.
use std::sync::Arc;
use async_channel::Receiver;
use futures_util::StreamExt;
use matrix_sdk::{Client,ruma::{OwnedRoomId,events::room::message::{MessageType,RoomMessageEventContent}}};
use matrix_sdk_ui::timeline::{RoomExt,Timeline,TimelineItem,EventSendState};

#[derive(Clone)]
pub struct Message {
    pub id:String,
    pub sender:String,
    pub body:String,
    pub timestamp_ms:i64,
    pub state:&'static str,
    pub action:bool,
    pub own:bool,
}
pub struct RoomTimeline {
    timeline:Arc<Timeline>,
    pub updates:Receiver<Vec<Message>>,
    pub typing:Option<tokio::sync::broadcast::Receiver<Vec<matrix_sdk::ruma::OwnedUserId>>>,
    _typing_guard:Option<matrix_sdk::event_handler::EventHandlerDropGuard>,
    task:tokio::task::JoinHandle<()>,
}
impl Drop for RoomTimeline {fn drop(&mut self){self.task.abort();}}
fn rows(items:impl Iterator<Item=Arc<TimelineItem>>,own:Option<&matrix_sdk::ruma::UserId>)->Vec<Message>{
    let mut messages=Vec::with_capacity(200);
    for item in items {
        let Some(event)=item.as_event() else{continue};
        if event.content().is_redacted(){continue;}
        let message=event.content().as_message();
        let action=message.is_some_and(|message|matches!(message.msgtype(),MessageType::Emote(_)));
        let body=match message{
            Some(message)=>message.body().chars().take(12_000).collect(),
            None if event.content().is_unable_to_decrypt()=>"Encrypted message: keys unavailable. Use Devices & security or Account recovery.".into(),
            // Room creation, membership and other state events are not chat
            // messages. Showing them as “Unsupported event” made a new room
            // look broken, so leave them out of the transcript.
            None=>continue,
        };
        let state=match event.send_state(){Some(EventSendState::NotSentYet{..})=>"Queued",Some(EventSendState::SendingFailed{..})=>"Not sent",Some(EventSendState::Sent{..})=>"Sent",None=>""};
        messages.push(Message{
            id:event.event_id().map(|id|id.to_string()).unwrap_or_default(),
            sender:event.sender().to_string(),
            body,
            timestamp_ms:i64::try_from(event.timestamp().0).unwrap_or(0),
            state,
            action,
            own:own.is_some_and(|own|own==event.sender()),
        });
    }
    messages.sort_by_key(|message|message.timestamp_ms);
    let excess=messages.len().saturating_sub(200);
    if excess>0{messages.drain(..excess);}
    messages
}

impl RoomTimeline {
    pub async fn open(client:&Client,id:&str)->Result<Self,String>{
        let id:OwnedRoomId=id.parse().map_err(|_|"Choose a conversation.")?;
        let room=client.get_room(&id).ok_or("Conversation unavailable.")?;
        let timeline=Arc::new(room.timeline().await.map_err(|_|"Could not open the conversation timeline.")?);
        timeline.paginate_backwards(50).await.map_err(|_|"The conversation opened, but its history could not be loaded.")?;
        let (mut items,stream)=timeline.subscribe().await;
        let (typing_guard,typing)=room.subscribe_to_typing_notifications();
        let own=client.user_id().map(ToOwned::to_owned);
        let (sender,updates)=async_channel::bounded(4);
        let _=sender.send(rows(items.iter().cloned(),own.as_deref())).await;
        let task=tokio::spawn(async move{
            let mut stream=Box::pin(stream);
            while let Some(changes)=stream.next().await{
                for change in changes{change.apply(&mut items);}
                if sender.send(rows(items.iter().cloned(),own.as_deref())).await.is_err(){break;}
            }
        });
        Ok(Self{timeline,updates,typing:Some(typing),_typing_guard:Some(typing_guard),task})
    }
    pub fn room_id(&self)->&str{self.timeline.room().room_id().as_str()}
    pub fn retry_pending(&self){self.timeline.room().send_queue().set_enabled(true);}
    pub async fn older_messages(&self)->Result<bool,String>{
        self.timeline.paginate_backwards(50).await.map_err(|_|"Older messages could not be loaded. Try again when connected.".into())
    }
    pub async fn encrypted(&self)->Result<bool,String>{self.timeline.room().latest_encryption_state().await.map(|state|state.is_encrypted()).map_err(|_|"The room encryption state could not be checked.".into())}
    pub async fn queue_message(&self,body:&str,allow_unencrypted:bool,action:bool)->Result<(),String>{
        if !self.encrypted().await?&&!allow_unencrypted{return Err("This room is not encrypted. Explicit permission is required before sending.".into());}
        shadow_messenger_core::validate_message(body).map_err(str::to_owned)?;
        let content=if action{RoomMessageEventContent::emote_plain(body)}else{RoomMessageEventContent::text_plain(body)};
        self.timeline.send(content.into()).await
            .map_err(|_|"The message could not be queued. Try again when connected.".to_owned())?;
        Ok(())
    }
}
