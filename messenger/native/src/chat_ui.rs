//! A detached conversation window: AIM-style separate chat, Discord-style grouped bubbles.
use std::{cell::{Cell,RefCell},collections::HashMap,rc::Rc,time::{Duration,Instant}};
use async_channel::Sender;
use gtk::prelude::*;
use shadow_messenger_core::{self,ChatMessage,DisplayMessage,Slash};
use crate::{timeline::Message,worker::Command};

#[derive(Clone,PartialEq,Eq)]
struct RoomRef {id:String,name:String}

pub struct ChatWindow {
    window:gtk::Window,
    heading:gtk::Label,
    subtitle:gtk::Label,
    avatar:gtk::Label,
    transcript:gtk::ListBox,
    scroll:gtk::ScrolledWindow,
    empty:gtk::Label,
    typing:gtk::Label,
    older:gtk::Button,
    composer:gtk::TextView,
    send:gtk::Button,
    plain:gtk::CheckButton,
    security:gtk::Label,
    status:gtk::Label,
    room:Rc<RefCell<Option<RoomRef>>>,
    drafts:Rc<RefCell<HashMap<String,String>>>,
    encrypted:Rc<Cell<Option<bool>>>,
    peer_status:Rc<RefCell<String>>,
    typing_generation:Rc<Cell<u64>>,
    typing_active:Rc<Cell<bool>>,
    typing_sent:Rc<Cell<Option<Instant>>>,
    hidden_hooks:Rc<RefCell<Vec<Rc<dyn Fn()>>>>,
    commands:Sender<Command>,
}

fn text_of(view:&gtk::TextView)->String{
    let buffer=view.buffer();
    buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).to_string()
}
fn local_day(milliseconds:i64)->i64{
    let seconds=milliseconds.div_euclid(1000);
    gtk::glib::DateTime::from_unix_local(seconds).map(|date|date.year() as i64*1000+date.day_of_year() as i64)
        .unwrap_or_else(|_|milliseconds.div_euclid(86_400_000))
}
fn time_label(milliseconds:i64)->String{
    gtk::glib::DateTime::from_unix_local(milliseconds.div_euclid(1000))
        .ok().and_then(|date|date.format("%H:%M").ok()).map(|text|text.to_string()).unwrap_or_default()
}
fn day_label(milliseconds:i64)->String{
    let Ok(date)=gtk::glib::DateTime::from_unix_local(milliseconds.div_euclid(1000)) else{return String::new()};
    if let Ok(now)=gtk::glib::DateTime::now_local(){
        if date.year()==now.year()&&date.day_of_year()==now.day_of_year(){return "Today".into();}
        if let Ok(yesterday)=now.add_days(-1){
            if date.year()==yesterday.year()&&date.day_of_year()==yesterday.day_of_year(){return "Yesterday".into();}
        }
    }
    date.format("%A, %B %d").map(|text|text.replace(" 0"," ")).unwrap_or_default()
}
fn invite_dialog(parent:&gtk::Window,room_id:&str,commands:&Sender<Command>){
    // Keep the dialog in the same application as the conversation so it
    // receives keyboard input reliably on every window manager.
    let app=parent.application().expect("conversation window belongs to the application");
    let window:gtk::Window=gtk::ApplicationWindow::builder().application(&app).title("Invite people").transient_for(parent).destroy_with_parent(true).default_width(460).default_height(280).build().upcast();
    window.add_css_class("messenger-window");window.set_size_request(380,240);
    let root=gtk::Box::new(gtk::Orientation::Vertical,10);root.set_margin_top(20);root.set_margin_bottom(20);root.set_margin_start(20);root.set_margin_end(20);
    let heading=gtk::Label::new(Some("Invite people to this conversation"));heading.add_css_class("messenger-page-title");heading.set_xalign(0.0);root.append(&heading);
    let note=gtk::Label::new(Some("Enter full Matrix addresses such as @name:provider.example, separated by commas. They receive an invitation they can accept or decline."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");root.append(&note);
    let entry=gtk::Entry::builder().placeholder_text("@name:provider.example").build();root.append(&entry);
    let send=gtk::Button::with_label("Send invitations");send.add_css_class("suggested-action");root.append(&send);
    let status=gtk::Label::new(Some("Invitations are sent through your homeserver."));status.set_wrap(true);status.set_xalign(0.0);status.add_css_class("messenger-muted");root.append(&status);
    window.set_child(Some(&root));
    let dispatch=Rc::new({let entry=entry.clone();let status=status.clone();let commands=commands.clone();let room_id=room_id.to_owned();move||{
        let people=entry.text().to_string();
        if people.trim().is_empty(){status.set_text("Enter at least one Matrix address.");return;}
        if commands.try_send(Command::Invite{room_id:room_id.clone(),people}).is_ok(){status.set_text("Sending invitations…");}else{status.set_text("An account request is already pending. Retry when it finishes.");}
    }});
    {let dispatch=dispatch.clone();send.connect_clicked(move|_|dispatch());}
    {let dispatch=dispatch.clone();entry.connect_activate(move|_|dispatch());}
    window.present();entry.grab_focus();
}

fn set_send_state(compose:&gtk::TextView,send:&gtk::Button,encrypted:&Cell<Option<bool>>,plain:&gtk::CheckButton){
    let allowed=encrypted.get()==Some(true)||(encrypted.get()==Some(false)&&plain.is_active());
    send.set_sensitive(allowed&&!text_of(compose).trim().is_empty());
}

impl ChatWindow {
    pub fn new(app:&gtk::Application,commands:Sender<Command>)->Self{
        // A conversation is its own top-level application window: it keeps a
        // panel entry so it can be minimized and restored independently.
        let window:gtk::Window=gtk::ApplicationWindow::builder().application(app).title("Conversation")
            .default_width(720).default_height(620).build().upcast();
        window.add_css_class("messenger-window");window.add_css_class("messenger-chat-window");window.set_size_request(430,380);
        let avatar=gtk::Label::new(Some("? "));avatar.add_css_class("messenger-avatar-chat");avatar.set_valign(gtk::Align::Center);
        let heading=gtk::Label::new(Some("Conversation"));heading.add_css_class("messenger-chat-heading");heading.set_xalign(0.0);
        let subtitle=gtk::Label::new(Some("Not connected"));subtitle.add_css_class("messenger-chat-subtitle");subtitle.set_xalign(0.0);
        let identity=gtk::Box::new(gtk::Orientation::Horizontal,10);let names=gtk::Box::new(gtk::Orientation::Vertical,0);names.set_hexpand(true);names.append(&heading);names.append(&subtitle);
        identity.append(&avatar);identity.append(&names);identity.set_margin_top(10);identity.set_margin_bottom(4);identity.set_margin_start(16);identity.set_margin_end(16);
        let menu=gtk::MenuButton::builder().label("Menu").build();menu.add_css_class("messenger-header-button");
        let menu_box=gtk::Box::new(gtk::Orientation::Vertical,4);menu_box.set_margin_top(8);menu_box.set_margin_bottom(8);menu_box.set_margin_start(8);menu_box.set_margin_end(8);
        let older_menu=gtk::Button::with_label("Load older messages");older_menu.add_css_class("flat");
        let retry_menu=gtk::Button::with_label("Retry pending messages");retry_menu.add_css_class("flat");
        let invite_menu=gtk::Button::with_label("Invite people…");invite_menu.add_css_class("flat");
        let minimize_menu=gtk::Button::with_label("Minimize");minimize_menu.add_css_class("flat");
        let close_menu=gtk::Button::with_label("Close conversation");close_menu.add_css_class("flat");
        for button in [&older_menu,&retry_menu,&invite_menu,&minimize_menu,&close_menu]{menu_box.append(button);}
        let popover=gtk::Popover::new();popover.set_child(Some(&menu_box));menu.set_popover(Some(&popover));identity.append(&menu);

        let root=gtk::Box::new(gtk::Orientation::Vertical,0);root.append(&identity);
        let toolbar=gtk::Box::new(gtk::Orientation::Horizontal,8);toolbar.set_margin_top(2);toolbar.set_margin_bottom(4);toolbar.set_margin_start(16);toolbar.set_margin_end(16);
        let older=gtk::Button::with_label("Load older messages");older.add_css_class("flat");older.add_css_class("messenger-small-button");older.set_sensitive(false);
        let typing=gtk::Label::new(None);typing.add_css_class("messenger-typing");typing.set_xalign(0.0);typing.set_hexpand(true);
        toolbar.append(&older);toolbar.append(&typing);root.append(&toolbar);

        let transcript=gtk::ListBox::new();transcript.set_selection_mode(gtk::SelectionMode::None);transcript.add_css_class("messenger-transcript");
        transcript.set_widget_name("transcript");transcript.set_valign(gtk::Align::Start);
        let empty=gtk::Label::new(Some("Choose a conversation."));empty.add_css_class("messenger-empty");empty.set_wrap(true);empty.set_margin_top(48);
        let body=gtk::Box::new(gtk::Orientation::Vertical,0);body.append(&empty);body.append(&transcript);
        let scroll=gtk::ScrolledWindow::builder().vexpand(true).hscrollbar_policy(gtk::PolicyType::Never)
            .vscrollbar_policy(gtk::PolicyType::Automatic).child(&body).build();root.append(&scroll);

        let security=gtk::Label::new(None);security.set_xalign(0.0);security.set_wrap(true);security.add_css_class("messenger-security");security.set_margin_start(16);security.set_margin_end(16);security.set_visible(false);root.append(&security);
        let plain=gtk::CheckButton::with_label("Allow unencrypted messages in this conversation");plain.set_visible(false);plain.set_margin_start(16);plain.set_margin_end(16);root.append(&plain);

        let composer_row=gtk::Box::new(gtk::Orientation::Horizontal,8);composer_row.set_margin_top(10);composer_row.set_margin_bottom(10);composer_row.set_margin_start(16);composer_row.set_margin_end(16);
        let composer=gtk::TextView::new();composer.add_css_class("messenger-composer");composer.set_left_margin(12);composer.set_right_margin(12);composer.set_top_margin(10);composer.set_bottom_margin(10);
        composer.set_wrap_mode(gtk::WrapMode::WordChar);composer.set_sensitive(false);composer.set_widget_name("composer");
        composer.set_tooltip_text(Some("Enter sends. Shift+Enter adds a new line."));
        let composer_scroll=gtk::ScrolledWindow::builder().child(&composer).min_content_height(44).max_content_height(110).vexpand(false).build();
        composer_scroll.set_hexpand(true);composer_scroll.add_css_class("messenger-composer-frame");
        let send=gtk::Button::with_label("Send");send.add_css_class("suggested-action");send.set_sensitive(false);send.set_valign(gtk::Align::End);
        composer_row.append(&composer_scroll);composer_row.append(&send);root.append(&composer_row);
        let status=gtk::Label::new(None);status.add_css_class("messenger-status-line");status.set_xalign(0.0);status.set_wrap(true);
        status.set_margin_start(16);status.set_margin_end(16);status.set_margin_bottom(8);root.append(&status);
        window.set_child(Some(&root));

        let room=Rc::new(RefCell::new(None::<RoomRef>));let drafts=Rc::new(RefCell::new(HashMap::new()));
        let encrypted=Rc::new(Cell::new(None::<bool>));let peer_status=Rc::new(RefCell::new(String::new()));
        let typing_generation=Rc::new(Cell::new(0));let typing_active=Rc::new(Cell::new(false));let typing_sent=Rc::new(Cell::new(None::<Instant>));

        let command=commands.clone();let room_copy=room.clone();let buffer=composer.clone();let status_copy=status.clone();let plain_copy=plain.clone();let active=typing_active.clone();let sent=typing_sent.clone();
        send.connect_clicked(move|button|{
            let Some(current)=room_copy.borrow().clone() else{return};
            let text=text_of(&buffer);
            if text.trim().is_empty(){return;}
            button.set_sensitive(false);
            match shadow_messenger_core::parse_slash(&text){
                Some(Err(message))=>{status_copy.set_text(message);button.set_sensitive(true);return;}
                Some(Ok(Slash::Help))=>{status_copy.set_text("Commands: /me action, /away [message], /back, /status [message], /shrug [message].");button.set_sensitive(true);return;}
                Some(Ok(Slash::Away(message)))=>{
                    if command.try_send(Command::SetStatus{presence:shadow_messenger_core::Presence::Away,message:message.to_owned()}).is_ok(){
                        buffer.buffer().set_text("");status_copy.set_text("Away message updated.");}else{status_copy.set_text("An account request is already pending.");}
                    button.set_sensitive(true);return;
                }
                Some(Ok(Slash::Back))=>{
                    if command.try_send(Command::SetStatus{presence:shadow_messenger_core::Presence::Online,message:String::new()}).is_ok(){
                        buffer.buffer().set_text("");status_copy.set_text("You are back online.");}else{status_copy.set_text("An account request is already pending.");}
                    button.set_sensitive(true);return;
                }
                Some(Ok(Slash::Status(message)))=>{
                    if command.try_send(Command::SetStatus{presence:shadow_messenger_core::Presence::Online,message:message.to_owned()}).is_ok(){
                        buffer.buffer().set_text("");status_copy.set_text("Status updated.");}else{status_copy.set_text("An account request is already pending.");}
                    button.set_sensitive(true);return;
                }
                _=>{}
            }
            let (body,action)=match shadow_messenger_core::parse_slash(&text){
                Some(Ok(Slash::Me(body)))=>(body.to_owned(),true),
                Some(Ok(Slash::Shrug(rest)))=>((if rest.is_empty(){"¯\\_(ツ)_/¯".to_owned()}else{format!("{rest} ¯\\_(ツ)_/¯")}),false),
                _=>(text.clone(),false),
            };
            if command.try_send(Command::Send{room_id:current.id.clone(),body,allow_unencrypted:plain_copy.is_active(),action}).is_ok(){
                if active.replace(false){let _=command.try_send(Command::Typing{room_id:current.id.clone(),typing:false});}
                sent.set(None);buffer.buffer().set_text("");status_copy.set_text("Queuing message…");
            }else{status_copy.set_text("An account request is already pending. Your draft was kept.");button.set_sensitive(true);}
        });

        let send_key=send.clone();
        let keys=gtk::EventControllerKey::new();
        keys.connect_key_pressed(move|_,key,_,modifiers|{
            if matches!(key,gtk::gdk::Key::Return|gtk::gdk::Key::KP_Enter)&&!modifiers.contains(gtk::gdk::ModifierType::SHIFT_MASK){
                if send_key.is_sensitive(){send_key.emit_clicked();return gtk::glib::Propagation::Stop;}
            }
            gtk::glib::Propagation::Proceed
        });
        composer.add_controller(keys);

        let room_copy=room.clone();let drafts_copy=drafts.clone();let send_copy=send.clone();let encrypted_copy=encrypted.clone();let plain_copy=plain.clone();let command=commands.clone();let active=typing_active.clone();let sent=typing_sent.clone();let composer_view=composer.clone();
        composer.buffer().connect_changed(move|buffer|{
            let body=buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).to_string();
            if let Some(current)=room_copy.borrow().clone(){drafts_copy.borrow_mut().insert(current.id.clone(),body.clone());}
            set_send_state(&composer_view,&send_copy,&encrypted_copy,&plain_copy);
            if body.trim().is_empty(){
                if active.replace(false){if let Some(current)=room_copy.borrow().clone(){let _=command.try_send(Command::Typing{room_id:current.id,typing:false});}sent.set(None);}
            }else if sent.get().is_none_or(|at|at.elapsed()>Duration::from_secs(4)){
                if let Some(current)=room_copy.borrow().clone(){if command.try_send(Command::Typing{room_id:current.id,typing:true}).is_ok(){sent.set(Some(Instant::now()));active.set(true);}}
            }
        });
        let send_copy=send.clone();let encrypted_copy=encrypted.clone();let composer_copy=composer.clone();let plain_for_toggle=plain.clone();
        plain.connect_toggled(move|_|set_send_state(&composer_copy,&send_copy,&encrypted_copy,&plain_for_toggle));
        let command=commands.clone();older.connect_clicked(move|_|{let _=command.try_send(Command::LoadOlder);});
        let command=commands.clone();older_menu.connect_clicked(move|_|{let _=command.try_send(Command::LoadOlder);});
        let command=commands.clone();retry_menu.connect_clicked(move|_|{let _=command.try_send(Command::RetryPending);});
        {let window=window.clone();minimize_menu.connect_clicked(move|_|window.minimize());}
        {let window=window.clone();let room=room.clone();let commands=commands.clone();invite_menu.connect_clicked(move|_|{
            let Some(room_id)=room.borrow().as_ref().map(|room|room.id.clone()) else{return};
            invite_dialog(&window,&room_id,&commands);
        });}
        let hidden_hooks=Rc::new(RefCell::new(Vec::<Rc<dyn Fn()>>::new()));
        let window_copy=window.clone();let hooks=hidden_hooks.clone();close_menu.connect_clicked(move|_|{window_copy.hide();for hook in hooks.borrow().iter(){(hook)();}});
        let hooks=hidden_hooks.clone();window.connect_close_request(move|window|{window.hide();for hook in hooks.borrow().iter(){(hook)();}gtk::glib::Propagation::Stop});

        Self{window,heading,subtitle,avatar,transcript,scroll,empty,typing,older,composer,send,plain,security,status,room,drafts,encrypted,peer_status,typing_generation,typing_active,typing_sent,hidden_hooks,commands}
    }
    pub fn present(&self){self.window.present();}
    pub fn notice(&self,message:&str){self.status.set_text(message);}
    pub fn window(&self)->&gtk::Window{&self.window}
    pub fn is_visible(&self)->bool{self.window.is_visible()}
    /// Called after this window is hidden so dependent windows can return to
    /// the main window instead of staying attached to a hidden chat.
    pub fn on_hide(&self,hook:impl Fn()+ 'static){self.hidden_hooks.borrow_mut().push(Rc::new(hook));}
    pub fn is_active(&self)->bool{self.window.is_active()}
    pub fn room_id(&self)->Option<String>{self.room.borrow().as_ref().map(|room|room.id.clone())}
    pub fn open(&self,room_id:&str,name:&str){
        let previous=self.room.borrow().clone();
        if previous.as_ref().is_some_and(|room|room.id==room_id){self.present();return;}
        if let Some(previous)=previous{self.drafts.borrow_mut().insert(previous.id,text_of(&self.composer));}
        *self.room.borrow_mut()=Some(RoomRef{id:room_id.to_owned(),name:name.to_owned()});
        self.heading.set_text(name);self.window.set_title(Some(&format!("{name} – Conversation")));
        self.avatar.set_text(&shadow_messenger_core::initials(name));
        self.encrypted.set(None);*self.peer_status.borrow_mut()=String::new();
        self.security.set_visible(false);self.plain.set_visible(false);self.plain.set_active(false);
        self.empty.set_text("Loading conversation…");self.empty.set_visible(true);
        while let Some(child)=self.transcript.first_child(){self.transcript.remove(&child);}
        let draft=self.drafts.borrow().get(room_id).cloned().unwrap_or_default();
        self.composer.buffer().set_text(&draft);self.composer.set_sensitive(true);
        self.older.set_sensitive(false);self.typing.set_text("");self.status.set_text("");
        self.send.set_sensitive(false);self.update_subtitle();self.present();
    }
    pub fn set_peer_status(&self,status:&str){*self.peer_status.borrow_mut()=status.to_owned();self.update_subtitle();}
    fn update_subtitle(&self){
        let encryption=match self.encrypted.get(){Some(true)=>"Encrypted",Some(false)=>"Not encrypted",None=>"Connecting…"};
        let peer=self.peer_status.borrow().clone();
        let text=if peer.is_empty(){encryption.to_owned()}else{format!("{peer} · {encryption}")};
        self.subtitle.set_text(&text);
    }
    pub fn security(&self,room_id:&str,encrypted:bool){
        if self.room.borrow().as_ref().is_none_or(|room|room.id!=room_id){return;}
        self.encrypted.set(Some(encrypted));self.plain.set_visible(!encrypted);self.plain.set_active(false);
        self.security.set_visible(true);
        self.security.set_text(if encrypted{"End-to-end encrypted by Matrix. Verify devices before trusting a new identity."}else{"Not encrypted: your provider can read this conversation."});
        set_send_state(&self.composer,&self.send,&self.encrypted,&self.plain);self.update_subtitle();
    }
    pub fn typing(&self,room_id:&str,users:&[String]){
        if self.room.borrow().as_ref().is_none_or(|room|room.id!=room_id){return;}
        let names=users.iter().map(|user|shadow_messenger_core::display_name(user)).collect::<Vec<_>>();
        let text=match names.len(){0=>String::new(),1=>format!("{} is typing…",names[0]),2=>format!("{} and {} are typing…",names[0],names[1]),_=>"Several people are typing…".into()};
        self.typing.set_text(&text);
        let generation=self.typing_generation.get()+1;self.typing_generation.set(generation);
        let label=self.typing.clone();let counter=self.typing_generation.clone();
        gtk::glib::timeout_add_seconds_local(6,move||{if counter.get()==generation{label.set_text("");}gtk::glib::ControlFlow::Break});
    }
    pub fn messages(&self,room_id:&str,messages:&[Message]){
        if self.room.borrow().as_ref().is_none_or(|room|room.id!=room_id){return;}
        self.empty.set_visible(messages.is_empty());if messages.is_empty(){self.empty.set_text("No messages yet. Say hello.");}
        self.typing.set_text("");self.typing_generation.set(self.typing_generation.get()+1);
        let adjustment=self.scroll.vadjustment();let at_end=adjustment.value()+adjustment.page_size()>=adjustment.upper()-24.0;
        while let Some(child)=self.transcript.first_child(){self.transcript.remove(&child);}
        let messages=messages.iter().map(|message|ChatMessage{id:message.id.clone(),sender:message.sender.clone(),body:message.body.clone(),timestamp_ms:message.timestamp_ms,state:message.state,action:message.action,own:message.own}).collect::<Vec<_>>();
        for row in shadow_messenger_core::group_messages(&messages,local_day){self.append(&row);}
        self.older.set_sensitive(messages.len()>=200);
        self.status.set_text(if messages.len()>=200{"Showing the latest 200 events. Load older messages for more."}else{""});
        if at_end{let adjustment=adjustment.clone();gtk::glib::idle_add_local_once(move||adjustment.set_value((adjustment.upper()-adjustment.page_size()).max(0.0)));}
    }
    fn append(&self,message:&DisplayMessage){
        if message.day_break{
            let label=gtk::Label::new(Some(&day_label(message.timestamp_ms)));label.add_css_class("messenger-day");label.set_halign(gtk::Align::Center);
            let row=gtk::ListBoxRow::new();row.set_selectable(false);row.set_activatable(false);row.set_child(Some(&label));row.add_css_class("messenger-day-row");self.transcript.append(&row);
        }
        let line=gtk::Box::new(gtk::Orientation::Horizontal,8);line.add_css_class("messenger-message-row");
        let name=shadow_messenger_core::display_name(&message.sender);
        if !message.own{
            if message.grouped{let spacer=gtk::Box::new(gtk::Orientation::Vertical,0);spacer.set_size_request(32,-1);line.append(&spacer);}
            else{let avatar=gtk::Label::new(Some(&shadow_messenger_core::initials(&name)));avatar.add_css_class("messenger-avatar-small");avatar.set_valign(gtk::Align::Start);avatar.set_tooltip_text(Some(&message.sender));line.append(&avatar);}
        }
        let bubble=gtk::Box::new(gtk::Orientation::Vertical,3);bubble.add_css_class("messenger-bubble");
        bubble.add_css_class(if message.own{"messenger-bubble-out"}else{"messenger-bubble-in"});
        if !message.grouped&&!message.own{let sender=gtk::Label::new(Some(&name));sender.add_css_class("messenger-sender");sender.set_xalign(0.0);bubble.append(&sender);}
        let text=if message.action{format!("* {name} {}",message.body)}else{message.body.clone()};
        let body=gtk::Label::new(Some(&text));
        body.set_wrap(true);body.set_wrap_mode(gtk::pango::WrapMode::WordChar);body.set_selectable(true);body.set_xalign(0.0);body.set_max_width_chars(64);
        body.add_css_class("messenger-body");if message.action{body.add_css_class("messenger-action");}bubble.append(&body);
        let footer=gtk::Box::new(gtk::Orientation::Horizontal,6);footer.set_halign(if message.own{gtk::Align::End}else{gtk::Align::Start});
        let time=gtk::Label::new(Some(&time_label(message.timestamp_ms)));time.add_css_class("messenger-time");footer.append(&time);
        if message.state=="Queued"{let state=gtk::Label::new(Some("sending…"));state.add_css_class("messenger-time");footer.append(&state);}
        if message.state=="Not sent"{let state=gtk::Label::new(Some("not sent"));state.add_css_class("messenger-error");footer.append(&state);}
        bubble.append(&footer);
        if message.own{let spacer=gtk::Box::new(gtk::Orientation::Vertical,0);spacer.set_hexpand(true);line.append(&spacer);line.append(&bubble);}
        else{line.append(&bubble);let spacer=gtk::Box::new(gtk::Orientation::Vertical,0);spacer.set_hexpand(true);line.append(&spacer);}
        let row=gtk::ListBoxRow::new();row.set_selectable(false);row.set_activatable(false);row.set_child(Some(&line));self.transcript.append(&row);
    }
    pub fn queued(&self,room_id:&str,body:&str){
        if self.room.borrow().as_ref().is_none_or(|room|room.id!=room_id){return;}
        self.drafts.borrow_mut().remove(room_id);
        if text_of(&self.composer)==body{self.composer.buffer().set_text("");}
        self.status.set_text("Message queued. Its timeline status will update when the server accepts it.");
    }
    pub fn error(&self,message:&str){if self.window.is_visible(){self.status.set_text(message);}}
    pub fn signed_out(&self){
        *self.room.borrow_mut()=None;self.drafts.borrow_mut().clear();self.encrypted.set(None);self.typing_active.set(false);self.typing_sent.set(None);
        self.window.hide();for hook in self.hidden_hooks.borrow().iter(){(hook)();}
        self.heading.set_text("Conversation");self.subtitle.set_text("Not connected");self.composer.buffer().set_text("");self.composer.set_sensitive(false);
        self.send.set_sensitive(false);self.typing.set_text("");self.status.set_text("");self.security.set_visible(false);self.plain.set_visible(false);self.plain.set_active(false);
        self.empty.set_text("Choose a conversation.");self.empty.set_visible(true);while let Some(child)=self.transcript.first_child(){self.transcript.remove(&child);}
    }
    #[allow(dead_code)]
    pub fn retry(&self){let _=self.commands.try_send(Command::RetryPending);}
}
