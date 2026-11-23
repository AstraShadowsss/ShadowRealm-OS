//! SDK-managed timelines, with one cancellable subscription per open conversation.
use std::sync::Arc;
use async_channel::Receiver;
use futures_util::StreamExt;
use matrix_sdk::{Client,ruma::{OwnedRoomId,events::room::message::RoomMessageEventContent}};
use matrix_sdk_ui::timeline::{RoomExt,Timeline,TimelineItem,EventSendState};

#[derive(Clone)]
pub struct Message {pub sender:String,pub body:String,pub state:&'static str}
pub struct RoomTimeline {
    timeline:Arc<Timeline>,
    pub updates:Receiver<Vec<Message>>,
    task:tokio::task::JoinHandle<()>,
}
impl Drop for RoomTimeline {fn drop(&mut self){self.task.abort();}}
fn rows(items:impl Iterator<Item=Arc<TimelineItem>>)->Vec<Message>{
    let mut messages=std::collections::VecDeque::with_capacity(200);
    for item in items {
        let Some(event)=item.as_event() else{continue};
        let body=event.content().as_message()
            .map(|message|message.body().chars().take(12_000).collect())
            .unwrap_or_else(||if event.content().is_unable_to_decrypt(){"Encrypted message: keys unavailable. Use Devices & security or Account recovery.".into()}else if event.content().is_redacted(){"Message removed.".into()}else{"[Unsupported event]".into()});
        if messages.len()==200{messages.pop_front();}
        let state=match event.send_state(){Some(EventSendState::NotSentYet{..})=>"Queued",Some(EventSendState::SendingFailed{..})=>"Not sent",Some(EventSendState::Sent{..})=>"Sent",None=>""};
        messages.push_back(Message{sender:event.sender().to_string(),body,state});
    }
    messages.into_iter().collect()
}

impl RoomTimeline {
    pub async fn open(client:&Client,id:&str)->Result<Self,String>{
        let id:OwnedRoomId=id.parse().map_err(|_|"Choose a conversation.")?;
        let room=client.get_room(&id).ok_or("Conversation unavailable.")?;
        let timeline=Arc::new(room.timeline().await.map_err(|_|"Could not open the conversation timeline.")?);
        timeline.paginate_backwards(50).await.map_err(|_|"The conversation opened, but its history could not be loaded.".to_owned())?;
        let (mut items,stream)=timeline.subscribe().await;
        let (sender,updates)=async_channel::bounded(4);
        let _=sender.send(rows(items.iter().cloned())).await;
        let task=tokio::spawn(async move{
            let mut stream=Box::pin(stream);
            while let Some(changes)=stream.next().await{
                for change in changes{change.apply(&mut items);}
                if sender.send(rows(items.iter().cloned())).await.is_err(){break;}
            }
        });
        Ok(Self{timeline,updates,task})
    }
    pub fn room_id(&self)->&str{self.timeline.room().room_id().as_str()}
    pub fn retry_pending(&self){self.timeline.room().send_queue().set_enabled(true);}
    pub async fn older_messages(&self)->Result<bool,String>{
        self.timeline.paginate_backwards(50).await.map_err(|_|"Older messages could not be loaded. Try again when connected.".into())
    }
    pub async fn encrypted(&self)->Result<bool,String>{self.timeline.room().latest_encryption_state().await.map(|state|state.is_encrypted()).map_err(|_|"The room encryption state could not be checked.".into())}
    pub async fn queue_message(&self,body:&str,allow_unencrypted:bool)->Result<(),String>{
        if !self.encrypted().await?&&!allow_unencrypted{return Err("This room is not encrypted. Explicit permission is required before sending.".into());}
        shadow_messenger_core::validate_message(body).map_err(str::to_owned)?;
        self.timeline.send(RoomMessageEventContent::text_plain(body).into()).await
            .map_err(|_|"The message could not be queued. Try again when connected.".to_owned())?;
        Ok(())
    }
}
