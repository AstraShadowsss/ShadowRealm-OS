#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Presence { Online, Away, DoNotDisturb, Invisible }

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Connection {
    pub room_id: String,
    pub name: String,
    pub unread: u64,
}

pub fn validate_homeserver(value: &str) -> Result<String, &'static str> {
    let value = value.trim();
    let remainder = value.strip_prefix("https://").ok_or("Use an HTTPS homeserver address.")?;
    if remainder.is_empty() || remainder.starts_with('/') ||
        value.chars().any(|c| c.is_control() || c.is_whitespace()) ||
        remainder.chars().any(|c| matches!(c,'@'|'?'|'#'|'\\')) {
        return Err("Enter a homeserver address without credentials, query or fragment.");
    }
    Ok(value.trim_end_matches('/').to_owned())
}

pub fn sort_connections(rooms: &mut [Connection]) {
    rooms.sort_by(|a,b| a.name.to_lowercase().cmp(&b.name.to_lowercase())
        .then_with(|| a.room_id.cmp(&b.room_id)));
}

pub fn validate_message(text: &str) -> Result<&str, &'static str> {
    if text.trim().is_empty() { return Err("Write a message first."); }
    if text.len() > 32_000 { return Err("This message is too long. Send a file instead."); }
    Ok(text)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn secure_server_policy() {
        assert_eq!(validate_homeserver(" https://matrix.example/ ").unwrap(),"https://matrix.example");
        for bad in ["http://matrix.example", "https://", "https:///path", "https://user:pass@host", "https://host?token=secret", "https://host/#secret", "https://host\nother", "https://host\\other"] {
            assert!(validate_homeserver(bad).is_err(),"{bad}");
        }
    }
    #[test]
    fn stable_connection_order() {
        let mut rooms=vec![Connection{room_id:"!b:host".into(),name:"beta".into(),unread:0},Connection{room_id:"!a:host".into(),name:"Alpha".into(),unread:2}];
        sort_connections(&mut rooms);assert_eq!(rooms[0].name,"Alpha");assert_eq!(rooms[0].unread,2);
    }
    #[test]
    fn message_validation_preserves_intentional_formatting() {
        assert!(validate_message(" \n ").is_err());
        assert!(validate_message(&"x".repeat(32_001)).is_err());
        assert_eq!(validate_message("  code\n  line 2").unwrap(),"  code\n  line 2");
    }
}
