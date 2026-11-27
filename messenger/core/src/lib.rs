#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Presence { Online, Away, DoNotDisturb, Invisible, Offline, Unknown }

impl Presence {
    pub fn label(self) -> &'static str {
        match self {
            Presence::Online => "Online",
            Presence::Away => "Away",
            Presence::DoNotDisturb => "Do Not Disturb",
            Presence::Invisible => "Invisible",
            Presence::Offline => "Offline",
            Presence::Unknown => "Status unavailable",
        }
    }
    /// Sort key for a buddy list: available people first, then the rest by name.
    pub fn rank(self) -> u8 {
        match self {
            Presence::Online => 0,
            Presence::Away => 1,
            Presence::DoNotDisturb => 2,
            Presence::Offline => 3,
            Presence::Invisible => 4,
            Presence::Unknown => 5,
        }
    }
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Connection {
    pub room_id: String,
    pub name: String,
    pub unread: u64,
    pub direct: bool,
    pub members: u64,
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Buddy {
    pub user_id: String,
    pub name: String,
    pub room_id: String,
    pub presence: Presence,
    pub status: String,
}

pub const MAX_STATUS: usize = 160;
pub const GROUP_WINDOW_MS: i64 = 5 * 60 * 1000;

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

pub fn sort_buddies(buddies: &mut [Buddy]) {
    buddies.sort_by(|a,b| a.presence.rank().cmp(&b.presence.rank())
        .then_with(|| a.name.to_lowercase().cmp(&b.name.to_lowercase()))
        .then_with(|| a.user_id.cmp(&b.user_id)));
}

pub fn validate_message(text: &str) -> Result<&str, &'static str> {
    if text.trim().is_empty() { return Err("Write a message first."); }
    if text.len() > 32_000 { return Err("This message is too long. Send a file instead."); }
    Ok(text)
}

/// Away messages and status lines. Empty clears the status.
pub fn validate_status(text: &str) -> Result<&str, &'static str> {
    let text = text.trim();
    if text.chars().count() > MAX_STATUS {
        return Err("Keep your status message to 160 characters or fewer.");
    }
    if text.chars().any(|c| c.is_control() && c != '\n' && c != '\t') {
        return Err("Status messages cannot contain control characters.");
    }
    Ok(text)
}

/// `@alex:provider.example` becomes `alex`; other values are left alone.
pub fn display_name(user_id: &str) -> String {
    let local = user_id.strip_prefix('@').unwrap_or(user_id);
    let local = local.split(':').next().unwrap_or(local);
    if local.is_empty() { user_id.to_owned() } else { local.to_owned() }
}

/// One or two initials for an avatar badge.
pub fn initials(name: &str) -> String {
    let mut letters = name.split_whitespace()
        .filter_map(|word| word.chars().find(|c| c.is_alphanumeric()))
        .take(2)
        .flat_map(char::to_uppercase)
        .collect::<String>();
    if letters.is_empty() { letters.push('?'); }
    letters
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct ChatMessage {
    pub id: String,
    pub sender: String,
    pub body: String,
    pub timestamp_ms: i64,
    pub state: &'static str,
    pub action: bool,
    pub own: bool,
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct DisplayMessage {
    pub id: String,
    pub sender: String,
    pub body: String,
    pub timestamp_ms: i64,
    pub state: &'static str,
    pub action: bool,
    pub own: bool,
    pub grouped: bool,
    pub day_break: bool,
}

/// Collapse consecutive messages from one sender into a group, and mark local
/// day boundaries. The caller supplies its own local-day numbering so the
/// result follows the desktop timezone.
pub fn group_messages<F>(messages: &[ChatMessage], day_of: F) -> Vec<DisplayMessage>
where F: Fn(i64) -> i64 {
    let mut rows = Vec::with_capacity(messages.len());
    let mut previous: Option<&ChatMessage> = None;
    let mut previous_day: Option<i64> = None;
    for message in messages {
        let day = day_of(message.timestamp_ms);
        let grouped = previous.is_some_and(|last| {
            previous_day == Some(day)
                && last.sender == message.sender
                && last.action == message.action
                && last.state.is_empty()
                && message.state.is_empty()
                && message.timestamp_ms >= last.timestamp_ms
                && message.timestamp_ms - last.timestamp_ms <= GROUP_WINDOW_MS
        });
        rows.push(DisplayMessage {
            id: message.id.clone(),
            sender: message.sender.clone(),
            body: message.body.clone(),
            timestamp_ms: message.timestamp_ms,
            state: message.state,
            action: message.action,
            own: message.own,
            grouped,
            day_break: previous_day != Some(day),
        });
        previous_day = Some(day);
        previous = Some(message);
    }
    rows
}

pub fn notification_body(body: &str) -> String {
    let clean = body.split_whitespace().collect::<Vec<_>>().join(" ");
    let mut text = clean.chars().take(180).collect::<String>();
    if clean.chars().count() > 180 { text.push('…'); }
    text
}

/// True when a message address or display name is mentioned.
pub fn mentions(body: &str, own_user: &str, own_name: &str) -> bool {
    let body = body.to_lowercase();
    (own_user.contains(':') && body.contains(&own_user.to_lowercase()))
        || (!own_name.is_empty() && (body.contains(&format!("@{}", own_name.to_lowercase()))
            || body.contains(&own_name.to_lowercase())))
}

#[derive(Debug, PartialEq, Eq)]
pub enum Slash<'a> {
    Me(&'a str),
    Away(&'a str),
    Back,
    Status(&'a str),
    Shrug(String),
    Help,
}

/// Parses composer commands. `None` means ordinary message text; `Some(Err)`
/// is a command that should be explained instead of sent.
pub fn parse_slash(input: &str) -> Option<Result<Slash<'_>, &'static str>> {
    let text = input.trim();
    let mut parts = text.splitn(2, char::is_whitespace);
    let command = parts.next()?.to_ascii_lowercase();
    if !command.starts_with('/') { return None; }
    let rest = parts.next().unwrap_or("").trim();
    Some(match command.as_str() {
        "/me" if rest.is_empty() => Err("Write what you are doing after /me."),
        "/me" => Ok(Slash::Me(rest)),
        "/away" => Ok(Slash::Away(rest)),
        "/back" => Ok(Slash::Back),
        "/status" => Ok(Slash::Status(rest)),
        "/shrug" => Ok(Slash::Shrug(rest.to_owned())),
        "/help" => Ok(Slash::Help),
        _ => Err("Unknown command. Try /me, /away, /back, /status or /shrug."),
    })
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
        let mut rooms=vec![
            Connection{room_id:"!b:host".into(),name:"beta".into(),unread:0,direct:false,members:3},
            Connection{room_id:"!a:host".into(),name:"Alpha".into(),unread:2,direct:true,members:2},
        ];
        sort_connections(&mut rooms);assert_eq!(rooms[0].name,"Alpha");assert_eq!(rooms[0].unread,2);
    }
    #[test]
    fn message_validation_preserves_intentional_formatting() {
        assert!(validate_message(" \n ").is_err());
        assert!(validate_message(&"x".repeat(32_001)).is_err());
        assert_eq!(validate_message("  code\n  line 2").unwrap(),"  code\n  line 2");
    }
    #[test]
    fn status_limits_and_presence_order() {
        assert_eq!(validate_status("  Back in 10 minutes  ").unwrap(),"Back in 10 minutes");
        assert_eq!(validate_status("").unwrap(),"");
        assert!(validate_status(&"x".repeat(MAX_STATUS+1)).is_err());
        assert!(validate_status("bad\u{7}bell").is_err());
        let mut buddies=vec![
            Buddy{user_id:"@z:host".into(),name:"Zed".into(),room_id:"!z:host".into(),presence:Presence::Offline,status:String::new()},
            Buddy{user_id:"@a:host".into(),name:"Amy".into(),room_id:"!a:host".into(),presence:Presence::Online,status:"At lunch".into()},
            Buddy{user_id:"@b:host".into(),name:"Bob".into(),room_id:"!b:host".into(),presence:Presence::Away,status:String::new()},
        ];
        sort_buddies(&mut buddies);
        assert_eq!(buddies[0].name,"Amy");assert_eq!(buddies[1].name,"Bob");assert_eq!(buddies[2].name,"Zed");
        assert_eq!(Presence::DoNotDisturb.label(),"Do Not Disturb");
    }
    #[test]
    fn names_and_initials() {
        assert_eq!(display_name("@AlexR:matrix.example"),"AlexR");
        assert_eq!(display_name("plain"),"plain");
        assert_eq!(initials("Alex Rivera"),"AR");
        assert_eq!(initials("shadowuser"),"S");
        assert_eq!(initials("  "),"?");
    }
    #[test]
    fn consecutive_messages_group_but_state_changes_and_days_break() {
        let messages=vec![
            ChatMessage{id:"1".into(),sender:"@a:host".into(),body:"one".into(),timestamp_ms:1_000,state:"",action:false,own:false},
            ChatMessage{id:"2".into(),sender:"@a:host".into(),body:"two".into(),timestamp_ms:2_000,state:"",action:false,own:false},
            ChatMessage{id:"3".into(),sender:"@b:host".into(),body:"three".into(),timestamp_ms:3_000,state:"",action:false,own:false},
            ChatMessage{id:"4".into(),sender:"@b:host".into(),body:"four".into(),timestamp_ms:4_000,state:"Queued",action:false,own:false},
            ChatMessage{id:"5".into(),sender:"@b:host".into(),body:"five".into(),timestamp_ms:4_100,state:"",action:false,own:false},
            ChatMessage{id:"6".into(),sender:"@a:host".into(),body:"next day".into(),timestamp_ms:90_000_000,state:"",action:false,own:false},
        ];
        let rows=group_messages(&messages,|ms|ms/86_400_000);
        assert!(!rows[0].grouped);assert!(rows[0].day_break);
        assert!(rows[1].grouped);assert!(!rows[1].day_break);
        assert!(!rows[2].grouped);
        assert!(!rows[3].grouped);
        assert!(!rows[4].grouped);
        assert!(rows[5].day_break);
    }
    #[test]
    fn slash_commands_are_explicit() {
        assert!(parse_slash("hello").is_none());
        assert_eq!(parse_slash("/me waves").unwrap().unwrap(),Slash::Me("waves"));
        assert_eq!(parse_slash("/away Lunch").unwrap().unwrap(),Slash::Away("Lunch"));
        assert_eq!(parse_slash("  /back ").unwrap().unwrap(),Slash::Back);
        assert_eq!(parse_slash("/status building").unwrap().unwrap(),Slash::Status("building"));
        assert_eq!(parse_slash("/shrug oh well").unwrap().unwrap(),Slash::Shrug("oh well".into()));
        assert!(parse_slash("/me   ").unwrap().is_err());
        assert!(parse_slash("/unknown").unwrap().is_err());
        assert_eq!(parse_slash("/HELP").unwrap().unwrap(),Slash::Help);
    }
    #[test]
    fn notifications_stay_short_and_mentions_match() {
        assert_eq!(notification_body("hello\n  there"),"hello there");
        assert!(notification_body(&"x".repeat(400)).chars().count()==181);
        assert!(mentions("hey @alex:example.org look","@Alex:example.org","Alex"));
        assert!(mentions("ping @Alex","@alex:example.org","Alex"));
        assert!(!mentions("nothing here","@alex:example.org","Alex"));
    }
}
