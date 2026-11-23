use matrix_sdk::{Client, config::SyncSettings, ruma::{OwnedRoomId, events::room::message::RoomMessageEventContent}};
use shadow_messenger_core::{Connection,sort_connections,validate_message};
use zeroize::Zeroizing;

pub struct Session { client: Client }

impl Session {
    pub async fn login(server: String, username: String, password: Zeroizing<String>) -> Result<Self,String> {
        let client=crate::persistence::login(server,username,password).await?;
        Ok(Self{client})
    }
    pub async fn restore() -> Result<Option<Self>,String> {
        Ok(crate::persistence::restore().await?.map(|client|Self{client}))
    }
    pub async fn connections(&self) -> Result<Vec<Connection>,String> {
        self.client.sync_once(SyncSettings::default()).await.map_err(|_| "Could not refresh conversations.".to_owned())?;
        let mut rooms=Vec::new();
        for room in self.client.joined_rooms() {
            let name=room.display_name().await.map(|n| n.to_string()).unwrap_or_else(|_| room.room_id().to_string());
            rooms.push(Connection{room_id:room.room_id().to_string(),name,unread:0});
        }
        sort_connections(&mut rooms);Ok(rooms)
    }
    pub async fn send(&self, room_id: &str, body: &str) -> Result<(),String> {
        validate_message(body).map_err(str::to_owned)?;
        let id:OwnedRoomId=room_id.parse().map_err(|_| "Choose a conversation.".to_owned())?;
        let room=self.client.get_room(&id).ok_or("Conversation unavailable.")?;
        room.send(RoomMessageEventContent::text_plain(body)).await.map_err(|_| "Message was not sent. Your text has been kept.".to_owned())?;
        Ok(())
    }
    pub async fn logout(&self) -> Result<(),String> {
        crate::persistence::forget(&self.client).await
    }
}
