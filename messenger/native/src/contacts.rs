//! Matrix presence for the buddy list. Presence can be disabled by a provider,
//! so a failed lookup is shown as unknown rather than invented.
use futures_util::future::join_all;
use matrix_sdk::{Client,RoomMemberships,ruma::{OwnedUserId,api::client::presence::get_presence,presence::PresenceState}};
use shadow_messenger_core::{Buddy,Presence};

pub struct BuddyList {
    pub own_user:String,
    pub own_presence:Presence,
    pub own_message:String,
    pub buddies:Vec<Buddy>,
}

fn map_presence(state:PresenceState)->Presence{
    match state {
        PresenceState::Online=>Presence::Online,
        PresenceState::Unavailable=>Presence::Away,
        PresenceState::Offline=>Presence::Offline,
        _=>Presence::Unknown,
    }
}

pub fn matrix_presence(presence:Presence)->PresenceState{
    match presence {
        Presence::Online=>PresenceState::Online,
        Presence::Away|Presence::DoNotDisturb=>PresenceState::Unavailable,
        Presence::Invisible|Presence::Offline=>PresenceState::Offline,
        Presence::Unknown=>PresenceState::Online,
    }
}

pub async fn buddies(client:&Client,own_presence:Presence,own_message:&str)->Result<BuddyList,String>{
    let own_user=client.user_id().ok_or("Sign in first.")?.to_owned();
    let mut peers=Vec::<(OwnedUserId,String,String)>::new();
    for room in client.joined_rooms(){
        let Ok(members)=room.members_no_sync(RoomMemberships::JOIN).await else{continue};
        if members.len()!=2{continue;}
        let Some(peer)=members.iter().find(|member|member.user_id()!=own_user) else{continue};
        if peers.iter().any(|(id,_,_)|id==peer.user_id()){continue;}
        let name=peer.display_name().map(str::to_owned)
            .unwrap_or_else(||shadow_messenger_core::display_name(peer.user_id().as_str()));
        peers.push((peer.user_id().to_owned(),name,room.room_id().to_string()));
    }
    let lookups=peers.iter().map(|(user,name,room)| async {
        let (presence,status)=match client.send(get_presence::v3::Request::new(user.clone())).await {
            Ok(response)=>(map_presence(response.presence),response.status_msg.unwrap_or_default()),
            Err(_)=>(Presence::Unknown,String::new()),
        };
        Buddy{user_id:user.to_string(),name:name.clone(),room_id:room.clone(),presence,status}
    });
    let mut buddies=join_all(lookups).await;
    shadow_messenger_core::sort_buddies(&mut buddies);
    Ok(BuddyList{own_user:own_user.to_string(),own_presence,own_message:own_message.to_owned(),buddies})
}
