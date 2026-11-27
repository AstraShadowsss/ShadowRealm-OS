//! The signed-in shell: AIM buddy list and Discord-style navigation in one window.
use std::{cell::{Cell,RefCell},collections::HashMap,rc::Rc};
use async_channel::Sender;
use gtk::prelude::*;
use shadow_messenger_core::{Buddy,Connection,Presence};
use crate::worker::Command;
use crate::appearance;

#[derive(Clone)]
pub struct Actions {
    pub open_chat:Rc<dyn Fn(String,String)>,
    pub conversations:Rc<dyn Fn()>,
    pub security:Rc<dyn Fn()>,
    pub recovery:Rc<dyn Fn()>,
    pub preferences:Rc<dyn Fn()>,
    pub away:Rc<dyn Fn()>,
    pub logout:Rc<dyn Fn()>,
    pub avatar:Rc<dyn Fn()>,
}
#[derive(Clone,Copy,PartialEq,Eq)]
enum Filter { All, Direct, Groups }
#[derive(Clone)]
struct RowInfo {room_id:String,name:String,direct:bool}

fn dot_class(presence:Presence)->&'static str{
    match presence{Presence::Online=>"messenger-dot-online",Presence::Away=>"messenger-dot-away",Presence::DoNotDisturb=>"messenger-dot-dnd",Presence::Invisible=>"messenger-dot-invisible",Presence::Offline=>"messenger-dot-offline",Presence::Unknown=>"messenger-dot-unknown"}
}
fn nav_item(text:&str)->gtk::Button{
    let button=gtk::Button::with_label(text);button.add_css_class("messenger-nav-item");button.set_halign(gtk::Align::Fill);button
}
fn mark(buttons:&[gtk::Button],active:&gtk::Button){
    for button in buttons{button.remove_css_class("active");}
    active.add_css_class("active");
}

pub struct Shell {
    pub root:gtk::Box,
    pub connections:gtk::Button,
    pub conversations:gtk::Button,
    pub groups:gtk::Button,
    pub activity:gtk::Button,
    pub avatar:gtk::Stack,
    avatar_initials:gtk::Label,
    avatar_picture:gtk::Image,
    avatar_button:gtk::Button,
    pub name:gtk::Label,
    pub presence_button:gtk::MenuButton,
    pub status_entry:gtk::Entry,
    pub status_line:gtk::Label,
    pub notice:gtk::Label,
    pub search:gtk::SearchEntry,
    pub heading:gtk::Label,
    pub list:gtk::ListBox,
    empty:gtk::Label,
    pub logout:gtk::Button,
    pub rooms:Rc<RefCell<Vec<Connection>>>,
    pub buddies:Rc<RefCell<HashMap<String,Buddy>>>,
    rows:Rc<RefCell<Vec<RowInfo>>>,
    filter:Rc<Cell<Filter>>,
    presence:Rc<Cell<Presence>>,
    activity_list:gtk::ListBox,
    activity_count:Rc<Cell<u64>>,
    commands:Sender<Command>,
    actions:Actions,
}

impl Shell {
    pub fn new(commands:&Sender<Command>,rooms:Rc<RefCell<Vec<Connection>>>,buddies:Rc<RefCell<HashMap<String,Buddy>>>,actions:Actions)->Self{
        let root=gtk::Box::new(gtk::Orientation::Horizontal,16);root.set_margin_top(16);root.set_margin_bottom(16);root.set_margin_start(16);root.set_margin_end(16);

        let nav=gtk::Box::new(gtk::Orientation::Vertical,4);nav.add_css_class("messenger-nav");nav.set_size_request(196,-1);nav.set_valign(gtk::Align::Fill);
        let connections=nav_item("Connections");let conversations=nav_item("Conversations");let groups=nav_item("Groups");let activity=nav_item("Activity");let away=nav_item("Away Message");let settings=nav_item("Preferences");
        for button in [&connections,&conversations,&groups,&activity,&away,&settings]{nav.append(button);}
        let spacer=gtk::Box::new(gtk::Orientation::Vertical,0);spacer.set_vexpand(true);nav.append(&spacer);
        nav.append(&gtk::Separator::new(gtk::Orientation::Horizontal));
        let security_button=gtk::Button::with_label("Devices & security");security_button.add_css_class("flat");security_button.add_css_class("messenger-small-button");
        let recovery_button=gtk::Button::with_label("Account recovery");recovery_button.add_css_class("flat");recovery_button.add_css_class("messenger-small-button");
        let logout=gtk::Button::with_label("Sign out");logout.add_css_class("flat");logout.add_css_class("messenger-small-button");
        for button in [&security_button,&recovery_button,&logout]{button.set_halign(gtk::Align::Fill);nav.append(button);}
        root.append(&nav);

        let profile=gtk::Box::new(gtk::Orientation::Vertical,10);profile.add_css_class("messenger-profile");profile.set_size_request(264,-1);
        let avatar_initials=gtk::Label::new(None);avatar_initials.add_css_class("messenger-avatar");
        let avatar_picture=gtk::Image::from_icon_name("avatar-default-symbolic");avatar_picture.set_pixel_size(76);avatar_picture.set_halign(gtk::Align::Center);avatar_picture.set_valign(gtk::Align::Center);avatar_picture.add_css_class("messenger-avatar-picture");
        let avatar=gtk::Stack::new();avatar.set_size_request(80,80);avatar.set_overflow(gtk::Overflow::Hidden);
        avatar.add_named(&avatar_initials,Some("initials"));avatar.add_named(&avatar_picture,Some("picture"));avatar.set_visible_child_name("initials");
        let avatar_frame=gtk::AspectFrame::builder().ratio(1.0).obey_child(false).xalign(0.5).yalign(0.5).child(&avatar).build();
        avatar_frame.set_size_request(80,80);avatar_frame.set_halign(gtk::Align::Center);avatar_frame.set_valign(gtk::Align::Center);
        let avatar_button=gtk::Button::with_label("Change picture…");avatar_button.add_css_class("flat");avatar_button.add_css_class("messenger-small-button");avatar_button.set_visible(false);
        {let action=actions.avatar.clone();avatar_button.connect_clicked(move|_|action());}
        let name=gtk::Label::new(Some("Not signed in"));name.add_css_class("messenger-page-title");name.set_halign(gtk::Align::Center);name.set_wrap(true);
        let presence=gtk::MenuButton::new();presence.set_label("Offline");presence.set_halign(gtk::Align::Center);presence.add_css_class("messenger-small-button");
        let status_entry=gtk::Entry::builder().placeholder_text("What's on your mind?").max_length(160).build();
        let popover=gtk::Popover::new();let options=gtk::Box::new(gtk::Orientation::Vertical,2);options.set_margin_top(6);options.set_margin_bottom(6);options.set_margin_start(6);options.set_margin_end(6);
        let presence_cell=Rc::new(Cell::new(Presence::Offline));
        for option in [Presence::Online,Presence::Away,Presence::DoNotDisturb,Presence::Invisible]{
            let button=gtk::Button::new();button.add_css_class("flat");let line=gtk::Box::new(gtk::Orientation::Horizontal,8);
            let dot=gtk::Label::new(Some("●"));dot.add_css_class(dot_class(option));let text=gtk::Label::new(Some(option.label()));text.set_xalign(0.0);
            line.append(&dot);line.append(&text);button.set_child(Some(&line));
            let tx=commands.clone();let popover_copy=popover.clone();let entry=status_entry.clone();
            button.connect_clicked(move|_|{
                let _=tx.try_send(Command::SetStatus{presence:option,message:entry.text().to_string()});popover_copy.popdown();
            });
            options.append(&button);
        }
        popover.set_child(Some(&options));presence.set_popover(Some(&popover));
        let set_status=gtk::Button::with_label("Set status");set_status.add_css_class("suggested-action");
        let hint=gtk::Label::new(Some("Your status is published through Matrix presence. Do Not Disturb silences alerts."));hint.set_wrap(true);hint.set_xalign(0.0);hint.add_css_class("messenger-muted");
        let status_line=gtk::Label::new(Some("Offline"));status_line.set_wrap(true);status_line.set_xalign(0.0);status_line.add_css_class("messenger-muted");
        let custom=gtk::Button::with_label("Custom Away Message…");custom.add_css_class("flat");custom.add_css_class("messenger-small-button");
        for widget in [avatar_frame.upcast_ref::<gtk::Widget>(),avatar_button.upcast_ref(),name.upcast_ref(),presence.upcast_ref(),status_entry.upcast_ref(),set_status.upcast_ref(),custom.upcast_ref(),hint.upcast_ref(),status_line.upcast_ref()]{profile.append(widget);}
        root.append(&profile);

        let tx=commands.clone();let entry=status_entry.clone();let current=presence_cell.clone();
        let publish=Rc::new(move||{let _=tx.try_send(Command::SetStatus{presence:current.get(),message:entry.text().to_string()});});
        let publish_copy=publish.clone();set_status.connect_clicked(move|_|publish_copy());
        let publish_copy=publish.clone();status_entry.connect_activate(move|_|publish_copy());
        let action=actions.away.clone();custom.connect_clicked(move|_|action());

        let right=gtk::Box::new(gtk::Orientation::Vertical,8);right.set_hexpand(true);right.set_valign(gtk::Align::Fill);
        let pager=gtk::Stack::new();pager.set_vexpand(true);pager.set_transition_type(gtk::StackTransitionType::Crossfade);
        let connections_page=gtk::Box::new(gtk::Orientation::Vertical,8);
        let search=gtk::SearchEntry::new();search.set_placeholder_text(Some("Search connections…"));connections_page.append(&search);
        let header=gtk::Box::new(gtk::Orientation::Horizontal,8);let heading=gtk::Label::new(Some("Connections (0)"));heading.add_css_class("messenger-page-title");heading.set_xalign(0.0);heading.set_hexpand(true);
        let add=gtk::Button::with_label("New chat / Invite");add.set_tooltip_text(Some("Start a conversation, invite people or review invitations"));add.add_css_class("messenger-small-button");
        let add_action=actions.conversations.clone();add.connect_clicked(move|_|add_action());
        header.append(&heading);header.append(&add);connections_page.append(&header);
        let empty=gtk::Label::new(Some("No conversations yet. Use + to start a private conversation or review invitations."));empty.set_wrap(true);empty.set_xalign(0.0);empty.add_css_class("messenger-muted");connections_page.append(&empty);
        let list=gtk::ListBox::new();list.set_selection_mode(gtk::SelectionMode::Single);list.add_css_class("messenger-connection-list");
        let scroll=gtk::ScrolledWindow::builder().child(&list).vexpand(true).hscrollbar_policy(gtk::PolicyType::Never).build();connections_page.append(&scroll);
        pager.add_named(&connections_page,Some("connections"));

        let activity_page=gtk::Box::new(gtk::Orientation::Vertical,8);
        let activity_title=gtk::Label::new(Some("Activity"));activity_title.add_css_class("messenger-page-title");activity_title.set_xalign(0.0);activity_page.append(&activity_title);
        let activity_hint=gtk::Label::new(Some("Messages and mentions from this session. Choose an item to open the conversation."));activity_hint.set_wrap(true);activity_hint.set_xalign(0.0);activity_hint.add_css_class("messenger-muted");activity_page.append(&activity_hint);
        let activity_list=gtk::ListBox::new();activity_list.set_selection_mode(gtk::SelectionMode::None);
        let activity_scroll=gtk::ScrolledWindow::builder().child(&activity_list).vexpand(true).hscrollbar_policy(gtk::PolicyType::Never).build();activity_page.append(&activity_scroll);
        pager.add_named(&activity_page,Some("activity"));
        right.append(&pager);
        let notice=gtk::Label::new(Some("Development build. Use a test account while compatibility and release checks are completed."));notice.set_wrap(true);notice.set_xalign(0.0);notice.add_css_class("messenger-notice");notice.set_margin_top(6);right.append(&notice);
        root.append(&right);

        let filter=Rc::new(Cell::new(Filter::All));let rows=Rc::new(RefCell::new(Vec::<RowInfo>::new()));
        let rows_filter=rows.clone();let filter_copy=filter.clone();let search_copy=search.clone();
        list.set_filter_func(move|row|{
            let Some(info)=rows_filter.borrow().get(row.index() as usize).cloned() else{return true};
            match filter_copy.get(){Filter::All=>{},Filter::Direct if !info.direct=>return false,Filter::Groups if info.direct=>return false,_=>{}}
            let query=search_copy.text().trim().to_lowercase();query.is_empty()||info.name.to_lowercase().contains(&query)
        });
        let search_list=list.clone();search.connect_search_changed(move|_|search_list.invalidate_filter());
        let rows_open=rows.clone();let open_action=actions.open_chat.clone();
        list.connect_row_selected(move|_,row|{if let Some(row)=row{if let Some(info)=rows_open.borrow().get(row.index() as usize).cloned(){(open_action)(info.room_id,info.name);}}});

        let activity_count=Rc::new(Cell::new(0u64));
        let nav_buttons=vec![connections.clone(),conversations.clone(),groups.clone(),activity.clone(),away.clone(),settings.clone()];
        {
            let filter=filter.clone();let pager=pager.clone();let buttons=nav_buttons.clone();let button=connections.clone();let target=list.clone();
            connections.connect_clicked(move|_|{filter.set(Filter::All);pager.set_visible_child_name("connections");mark(&buttons,&button);target.invalidate_filter();});
        }
        {
            let filter=filter.clone();let pager=pager.clone();let buttons=nav_buttons.clone();let button=groups.clone();let target=list.clone();
            groups.connect_clicked(move|_|{filter.set(Filter::Groups);pager.set_visible_child_name("connections");mark(&buttons,&button);target.invalidate_filter();});
        }
        {
            let filter=filter.clone();let pager=pager.clone();let buttons=nav_buttons.clone();let button=conversations.clone();let target=list.clone();let action=actions.conversations.clone();
            conversations.connect_clicked(move|_|{filter.set(Filter::Direct);pager.set_visible_child_name("connections");mark(&buttons,&button);target.invalidate_filter();action();});
        }
        {
            let pager=pager.clone();let buttons=nav_buttons.clone();let button=activity.clone();let count=activity_count.clone();let label=activity.clone();
            activity.connect_clicked(move|_|{pager.set_visible_child_name("activity");mark(&buttons,&button);count.set(0);label.set_label("Activity");});
        }
        {
            let action=actions.away.clone();away.connect_clicked(move|_|action());
        }
        {
            let action=actions.preferences.clone();settings.connect_clicked(move|_|action());
        }
        let security_action=actions.security.clone();security_button.connect_clicked(move|_|security_action());
        let recovery_action=actions.recovery.clone();recovery_button.connect_clicked(move|_|recovery_action());

        // The connection rows and activity feed are filled from the account events.
        let shell=Self{root,connections,conversations,groups,activity,avatar,avatar_initials,avatar_picture,avatar_button,name,presence_button:presence,status_entry,status_line,notice,search,heading,list,empty,logout,rooms,buddies,rows,filter,presence:presence_cell,activity_list,activity_count,commands:commands.clone(),actions};
        shell.render();
        shell
    }
    pub fn set_identity(&self,display_name:&str,user_id:&str){
        let name=if display_name.trim().is_empty(){shadow_messenger_core::display_name(user_id)}else{display_name.to_owned()};
        self.name.set_text(&name);self.name.set_tooltip_text(Some(user_id));self.avatar_initials.set_text(&shadow_messenger_core::initials(&name));
        if self.avatar.visible_child_name().as_deref()!=Some("picture"){self.avatar.set_visible_child_name("initials");}
        self.avatar_button.set_visible(true);
    }
    pub fn set_presence(&self,presence:Presence,message:&str){
        self.presence.set(presence);self.presence_button.set_label(presence.label());
        let line=if message.trim().is_empty(){presence.label().to_owned()}else{format!("{} · {}",presence.label(),message)};
        self.status_line.set_text(&line);
        if self.status_entry.text().as_str()!=message{self.status_entry.set_text(message);}
    }
    pub fn set_rooms(&self,rooms:Vec<Connection>){*self.rooms.borrow_mut()=rooms;self.render();}
    pub fn set_buddies(&self,buddies:Vec<Buddy>){*self.buddies.borrow_mut()=buddies.into_iter().map(|buddy|(buddy.room_id.clone(),buddy)).collect();self.render();}
    pub fn set_avatar(&self,bytes:&[u8]){
        if let Ok(texture)=gtk::gdk::Texture::from_bytes(&gtk::glib::Bytes::from(bytes)){self.avatar_picture.set_paintable(Some(&texture));self.avatar.set_visible_child_name("picture");}
    }
    pub fn set_invitations(&self,invites:usize){self.conversations.set_label(&if invites==0{"Conversations".into()}else{format!("Conversations ({invites})")});}
    pub fn set_notice(&self,message:&str){self.notice.set_text(message);}
    pub fn push_activity(&self,room_id:&str,room_name:&str,sender:&str,body:&str,mention:bool,time:&str){
        let row=gtk::Button::new();row.add_css_class("messenger-activity-row");row.set_halign(gtk::Align::Fill);
        let content=gtk::Box::new(gtk::Orientation::Vertical,2);content.set_margin_start(4);content.set_margin_end(4);
        let top=gtk::Box::new(gtk::Orientation::Horizontal,6);let title=gtk::Label::new(Some(&format!("{room_name} · {}",shadow_messenger_core::display_name(sender))));title.add_css_class("messenger-activity-title");title.set_xalign(0.0);title.set_hexpand(true);title.set_ellipsize(gtk::pango::EllipsizeMode::End);
        top.append(&title);if mention{let badge=gtk::Label::new(Some("mention"));badge.add_css_class("messenger-badge");badge.set_tooltip_text(Some("You were mentioned"));top.append(&badge);}
        let stamp=gtk::Label::new(Some(time));stamp.add_css_class("messenger-activity-time");top.append(&stamp);
        let preview=gtk::Label::new(Some(body));preview.add_css_class("messenger-activity-body");preview.set_xalign(0.0);preview.set_ellipsize(gtk::pango::EllipsizeMode::End);
        content.append(&top);content.append(&preview);row.set_child(Some(&content));
        let open=self.actions.open_chat.clone();let id=room_id.to_owned();let name=room_name.to_owned();row.connect_clicked(move|_|(open)(id.clone(),name.clone()));
        self.activity_list.prepend(&row);
        let mut count=0;let mut child=self.activity_list.first_child();
        while let Some(current)=child{count+=1;child=current.next_sibling();}
        while count>60{if let Some(last)=self.activity_list.last_child(){self.activity_list.remove(&last);count-=1;}else{break;}}
        let count=self.activity_count.get()+1;self.activity_count.set(count);self.activity.set_label(&format!("Activity ({count})"));
    }
    fn render(&self){
        while let Some(child)=self.list.first_child(){self.list.remove(&child);}
        self.rows.borrow_mut().clear();
        let rooms=self.rooms.borrow().clone();
        for room in &rooms{self.append_room(room);}
        self.heading.set_text(&format!("Connections ({})",rooms.len()));
        self.empty.set_visible(rooms.is_empty());
        self.list.invalidate_filter();
    }
    fn append_room(&self,room:&Connection){
        let row_box=gtk::Box::new(gtk::Orientation::Horizontal,10);
        let avatar=gtk::Label::new(Some(&shadow_messenger_core::initials(&room.name)));avatar.add_css_class("messenger-avatar-small");avatar.set_valign(gtk::Align::Center);
        let info=gtk::Box::new(gtk::Orientation::Vertical,1);info.set_hexpand(true);
        let name=gtk::Label::new(Some(&room.name));name.add_css_class("messenger-connection-name");name.set_xalign(0.0);name.set_ellipsize(gtk::pango::EllipsizeMode::End);
        let subtitle=gtk::Box::new(gtk::Orientation::Horizontal,5);
        if room.direct{
            if let Some(buddy)=self.buddies.borrow().values().find(|buddy|buddy.room_id==room.room_id){
                let dot=gtk::Label::new(Some("●"));dot.add_css_class(dot_class(buddy.presence));dot.set_tooltip_text(Some(buddy.presence.label()));
                let text=if buddy.status.trim().is_empty(){buddy.presence.label().to_owned()}else{format!("{} · {}",buddy.presence.label(),buddy.status)};
                let label=gtk::Label::new(Some(&text));label.add_css_class("messenger-connection-subtitle");label.set_xalign(0.0);label.set_ellipsize(gtk::pango::EllipsizeMode::End);
                subtitle.append(&dot);subtitle.append(&label);
            }else{let label=gtk::Label::new(Some("Direct message"));label.add_css_class("messenger-connection-subtitle");label.set_xalign(0.0);subtitle.append(&label);}
        }else{
            let label=gtk::Label::new(Some(&format!("Group · {} member{}",room.members,if room.members==1{""}else{"s"})));label.add_css_class("messenger-connection-subtitle");label.set_xalign(0.0);subtitle.append(&label);
        }
        info.append(&name);info.append(&subtitle);
        let open=gtk::Button::with_label("Open");open.add_css_class("messenger-small-button");open.set_valign(gtk::Align::Center);
        let action=self.actions.open_chat.clone();let id=room.room_id.clone();let room_name=room.name.clone();open.connect_clicked(move|_|(action)(id.clone(),room_name.clone()));
        row_box.append(&avatar);row_box.append(&info);row_box.append(&open);row_box.add_css_class("messenger-connection-row");
        let row=gtk::ListBoxRow::new();row.set_child(Some(&row_box));row.set_widget_name(&format!("connection:{}",room.room_id));
        self.list.append(&row);
        self.rows.borrow_mut().push(RowInfo{room_id:room.room_id.clone(),name:room.name.clone(),direct:room.direct});
    }
    pub fn select(&self,room_id:&str){
        let index={self.rows.borrow().iter().position(|row|row.room_id==room_id)};
        if let Some(index)=index{if let Some(row)=self.list.row_at_index(index as i32){self.list.select_row(Some(&row));}}
    }
    pub fn signed_out(&self){
        self.rooms.borrow_mut().clear();self.buddies.borrow_mut().clear();self.render();
        self.name.set_text("Not signed in");self.name.set_tooltip_text(None);self.avatar_initials.set_text("");self.avatar_picture.set_icon_name(Some("avatar-default-symbolic"));self.avatar.set_visible_child_name("initials");self.avatar_button.set_visible(false);
        self.presence.set(Presence::Offline);self.presence_button.set_label("Offline");self.status_entry.set_text("");self.status_line.set_text("Offline");
        self.notice.set_text("No account connected. Choose a test account to continue development checks.");
        self.conversations.set_label("Conversations");self.activity.set_label("Activity");self.activity_count.set(0);
        while let Some(child)=self.activity_list.first_child(){self.activity_list.remove(&child);}
        self.search.set_text("");
    }
}

pub fn away_dialog(parent:&gtk::Window,commands:&Sender<Command>){
    let window=gtk::Window::builder().title("Custom Away Message").transient_for(parent).modal(true).default_width(480).default_height(340).build();
    window.add_css_class("messenger-window");
    let root=gtk::Box::new(gtk::Orientation::Vertical,10);root.set_margin_top(18);root.set_margin_bottom(18);root.set_margin_start(18);root.set_margin_end(18);
    let title=gtk::Label::new(Some("Custom away message"));title.add_css_class("messenger-page-title");title.set_xalign(0.0);
    let note=gtk::Label::new(Some("Shown to people who can see your presence. Up to 160 characters. Leave it empty to clear it."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");
    let view=gtk::TextView::new();view.set_wrap_mode(gtk::WrapMode::WordChar);view.set_left_margin(10);view.set_right_margin(10);view.set_top_margin(8);view.set_bottom_margin(8);
    let scroll=gtk::ScrolledWindow::builder().child(&view).min_content_height(110).build();scroll.add_css_class("messenger-composer-frame");
    let status=gtk::Label::new(None);status.set_wrap(true);status.set_xalign(0.0);status.add_css_class("messenger-muted");
    let buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);buttons.set_halign(gtk::Align::End);
    let cancel=gtk::Button::with_label("Cancel");let save=gtk::Button::with_label("Set away message");save.add_css_class("suggested-action");
    buttons.append(&cancel);buttons.append(&save);
    for widget in [title.upcast_ref::<gtk::Widget>(),note.upcast_ref(),scroll.upcast_ref(),status.upcast_ref(),buttons.upcast_ref()]{root.append(widget);}
    window.set_child(Some(&root));
    let window_copy=window.clone();cancel.connect_clicked(move|_|{window_copy.close();});
    let tx=commands.clone();let label=status.clone();let buffer=view.buffer();let window_copy=window.clone();
    save.connect_clicked(move|_|{
        let text=buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).to_string();
        match shadow_messenger_core::validate_status(&text){
            Ok(message)=>{
                if tx.try_send(Command::SetStatus{presence:Presence::Away,message:message.to_owned()}).is_ok(){window_copy.close();}
                else{label.set_text("An account request is already pending. Try again when it finishes.");}
            }
            Err(message)=>label.set_text(message),
        }
    });
    window.present();
}
