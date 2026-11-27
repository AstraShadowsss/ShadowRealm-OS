use matrix_sdk::{Client,RoomMemberships};
use shadow_messenger_core::{Connection,sort_connections};
use zeroize::Zeroizing;

#[derive(Clone)]
pub struct Session { client: Client }

impl Session {
    pub fn client(&self)->&Client { &self.client }
    pub async fn login(server: String, username: String, password: Zeroizing<String>) -> Result<Self,String> {
        let client=crate::persistence::login(server,username,password).await?;
        Ok(Self{client})
    }
    pub async fn register(server:String,username:String,password:Zeroizing<String>,token:Option<Zeroizing<String>>) -> Result<Self,String> {
        let client=crate::persistence::register(server,username,password,token).await?;
        Ok(Self{client})
    }
    pub async fn restore() -> Result<Option<Self>,String> {
        Ok(crate::persistence::restore().await?.map(|client|Self{client}))
    }
    pub async fn connections(&self) -> Result<Vec<Connection>,String> {
        let mut rooms=Vec::new();
        for room in self.client.joined_rooms() {
            let name=room.display_name().await.map(|n| n.to_string()).unwrap_or_else(|_| room.room_id().to_string());
            let members=room.members_no_sync(RoomMemberships::JOIN).await.map(|members|members.len() as u64).unwrap_or(0);
            rooms.push(Connection{room_id:room.room_id().to_string(),name,unread:0,direct:members==2,members});
        }
        sort_connections(&mut rooms);Ok(rooms)
    }
    pub async fn logout(&self) -> Result<(),String> {
        crate::persistence::forget(&self.client).await
    }
}
