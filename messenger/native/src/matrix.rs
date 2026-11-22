use matrix_sdk::{Client, config::SyncSettings, ruma::{OwnedRoomId, events::room::message::RoomMessageEventContent}};
use shadow_messenger_core::{Connection,sort_connections,validate_homeserver,validate_message};
use zeroize::Zeroizing;

pub struct Session { client: Client }

impl Session {
    pub async fn login(server: String, username: String, password: Zeroizing<String>) -> Result<Self,String> {
        let server=validate_homeserver(&server).map_err(str::to_owned)?;
        let client=Client::builder().homeserver_url(server).build().await.map_err(|_| "Could not connect to the selected homeserver.".to_owned())?;
        client.matrix_auth().login_username(username,password.as_str())
            .initial_device_display_name("Shadow Messenger development")
            .send().await.map_err(|_| "Sign-in failed. Check the account, server and supported login method.".to_owned())?;
        Ok(Self{client})
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
        self.client.logout().await.map_err(|_| "Server sign-out could not be confirmed.".to_owned())?;Ok(())
    }
}
