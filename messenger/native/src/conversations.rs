use matrix_sdk::{Client,RoomState,ruma::{OwnedRoomId,OwnedUserId}};

#[derive(Clone,PartialEq,Eq)]
pub struct Invitation {pub room_id:String,pub name:String,pub inviter:String}

pub async fn invitations(client:&Client)->Vec<Invitation>{
    let mut result=Vec::new();
    for room in client.invited_rooms(){
        let name=room.display_name().await.map(|name|name.to_string()).unwrap_or_else(|_|room.room_id().to_string());
        let inviter=room.invite_details().await.map(|details|details.inviter_id.to_string()).unwrap_or_else(|_|"Inviter unavailable".into());
        result.push(Invitation{room_id:room.room_id().to_string(),name,inviter});
    }
    result.sort_by(|a,b|a.name.to_lowercase().cmp(&b.name.to_lowercase()).then_with(||a.room_id.cmp(&b.room_id)));result
}

pub async fn respond(client:&Client,id:&str,accept:bool)->Result<(),String>{
    let id:OwnedRoomId=id.parse().map_err(|_|"This invitation is invalid.")?;
    let room=client.get_room(&id).filter(|room|room.state()==RoomState::Invited).ok_or("This invitation is no longer available. Refresh conversations.")?;
    if accept{room.join().await.map_err(|_|"The invitation could not be accepted. Check your connection and refresh.".to_owned())}
    else{room.leave().await.map_err(|_|"The invitation could not be declined. Check your connection and refresh.".to_owned())}
}

fn participants(input:&str,own:&str)->Result<Vec<OwnedUserId>,String>{
    let mut users=std::collections::BTreeSet::new();
    for value in input.split(|c:char|c==','||c.is_whitespace()).filter(|value|!value.is_empty()){
        let user:OwnedUserId=value.parse().map_err(|_|"Use full Matrix addresses, such as @name:provider.example, separated by commas or spaces.")?;
        if user.as_str()==own{return Err("Add another person's Matrix address, not your own account.".into());}
        users.insert(user);if users.len()>20{return Err("Invite up to 20 people when creating a conversation.".into());}
    }
    if users.is_empty(){return Err("Enter at least one Matrix address.".into());}Ok(users.into_iter().collect())
}

pub async fn invite(client:&Client,room_id:&str,input:&str)->Result<String,String>{
    let users=participants(input,client.user_id().ok_or("Sign in first.")?.as_str())?;
    let id:OwnedRoomId=room_id.parse().map_err(|_|"This conversation is invalid.")?;
    let room=client.get_room(&id).ok_or("Open the conversation again before inviting someone.")?;
    let mut sent=0;let mut failed=Vec::new();
    for user in users{match room.invite_user_by_id(&user).await{Ok(_)=>sent+=1,Err(_)=>failed.push(user.to_string())}}
    Ok(if failed.is_empty(){format!("Invited {sent} {}. They can accept from their invitations.",if sent==1{"person"}else{"people"})}
        else{format!("Invited {sent}. These invitations did not complete: {}. Check the addresses and connection.",failed.join(", "))})
}

pub async fn create(client:&Client,name:&str,input:&str)->Result<(String,String),String>{
    let users=participants(input,client.user_id().ok_or("Sign in first.")?.as_str())?;
    let name=name.trim();if name.chars().count()>80||name.chars().any(char::is_control){return Err("Use a conversation name of up to 80 characters without control characters.".into());}
    let mut request=matrix_sdk::ruma::api::client::room::create_room::v3::Request::new();
    request.is_direct=users.len()==1;if !name.is_empty(){request.name=Some(name.into());}
    let room=client.create_room(request).await.map_err(|_|"The private conversation could not be created. Check your connection before retrying.")?;
    room.enable_encryption().await.map_err(|_|"A private empty conversation was created, but encryption setup did not finish. Nobody was invited. Refresh your conversation list before retrying.")?;
    if !room.latest_encryption_state().await.map_err(|_|"Encryption could not be checked. Nobody was invited.")?.is_encrypted(){return Err("Encryption was not confirmed. Nobody was invited.".into());}
    let mut failed=Vec::new();for user in users{if room.invite_user_by_id(&user).await.is_err(){failed.push(user.to_string());}}
    let status=if failed.is_empty(){"Encrypted conversation created. Invitations sent.".into()}else{format!("Encrypted conversation created. These invitations did not complete: {}. Check the addresses and connection.",failed.join(", "))};
    Ok((room.room_id().to_string(),status))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn participant_addresses_are_validated_before_room_creation(){
        assert!(participants("","@me:example.org").is_err());assert!(participants("friend","@me:example.org").is_err());assert!(participants("@me:example.org","@me:example.org").is_err());
        let users=participants("@b:example.org, @a:example.org @b:example.org","@me:example.org").unwrap();assert_eq!(users.len(),2);assert_eq!(users[0].as_str(),"@a:example.org");
        let many=(0..21).map(|n|format!("@user{n}:example.org")).collect::<Vec<_>>().join(",");assert!(participants(&many,"@me:example.org").is_err());
    }
    #[tokio::test(flavor="multi_thread",worker_threads=2)]
    #[ignore = "requires isolated keyring and disposable Matrix accounts"]
    async fn encrypted_creation_and_invitation_accept_decline(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        tokio::time::timeout(std::time::Duration::from_secs(90),async{
            let account:serde_json::Value=serde_json::from_str(&std::fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
            let first=crate::persistence::login(account["server"].as_str().unwrap().into(),account["username"].as_str().unwrap().into(),zeroize::Zeroizing::new(account["password"].as_str().unwrap().into())).await.unwrap();
            let second=crate::persistence::client_builder(account["server"].as_str().unwrap()).unwrap().build().await.unwrap();
            second.matrix_auth().login_username(account["bob_username"].as_str().unwrap(),account["bob_password"].as_str().unwrap()).send().await.unwrap();
            first.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();second.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
            let a=first.clone();let first_sync=tokio::spawn(async move{a.sync(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(1))).await});
            let b=second.clone();let second_sync=tokio::spawn(async move{b.sync(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(1))).await});
            for accept in [true,false]{
                let (id,status)=create(&first,"Disposable encrypted invitation",second.user_id().unwrap().as_str()).await.unwrap();assert!(status.ends_with("Invitations sent."));
                loop{if invitations(&second).await.iter().any(|invite|invite.room_id==id){break;}tokio::time::sleep(std::time::Duration::from_millis(50)).await;}
                respond(&second,&id,accept).await.unwrap();let id:OwnedRoomId=id.parse().unwrap();
                if accept{let room=second.get_room(&id).unwrap();assert!(room.latest_encryption_state().await.unwrap().is_encrypted());assert_eq!(room.state(),RoomState::Joined);}
                else{assert!(second.get_room(&id).is_none_or(|room|room.state()==RoomState::Left));assert!(!invitations(&second).await.iter().any(|invite|invite.room_id==id.as_str()));}
            }
            first_sync.abort();second_sync.abort();second.logout().await.unwrap();crate::persistence::forget(&first).await.unwrap();
        }).await.expect("Conversation fixture exceeded its time limit");
    }
}
