#![recursion_limit = "256"]
mod matrix;
mod vault;
mod persistence;
mod worker;
mod timeline;
mod verification;
mod recovery;
mod security_ui;
mod recovery_ui;
mod conversations;
mod conversations_ui;
use gtk::{glib,prelude::*};

fn main() -> glib::ExitCode {
    let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.Development").build();
    app.connect_activate(build);
    app.run()
}

fn build(app:&gtk::Application) {
    if let Some(window)=app.windows().into_iter().find(|window|window.widget_name().as_str()=="shadow-messenger-main"){window.present();return;}
    let (commands,updates)=worker::start();
    let window=gtk::ApplicationWindow::builder().application(app).title("Shadow Messenger — Development")
        .default_width(980).default_height(650).build();
    window.set_widget_name("shadow-messenger-main");
    let commands_close=commands.clone();let updates_close=updates.clone();window.connect_destroy(move |_|{commands_close.close();updates_close.close();});
    let shell=gtk::Box::new(gtk::Orientation::Vertical,18);
    shell.set_margin_top(24);shell.set_margin_bottom(24);shell.set_margin_start(24);shell.set_margin_end(24);
    let conversation_views=std::rc::Rc::new(std::cell::RefCell::new(None::<conversations_ui::ConversationsView>));
    let conversation_button=gtk::Button::with_label("Conversations");conversation_button.set_sensitive(false);
    let views=conversation_views.clone();let parent=window.downgrade();let tx=commands.clone();conversation_button.connect_clicked(move |_|{if let Some(parent)=parent.upgrade(){let mut views=views.borrow_mut();let view=views.get_or_insert_with(||conversations_ui::ConversationsView::new(&parent,tx.clone()));view.present();let _=tx.try_send(worker::Command::Invitations);}});
    let security_views=std::rc::Rc::new(std::cell::RefCell::new(None::<security_ui::SecurityView>));
    let recovery_views=std::rc::Rc::new(std::cell::RefCell::new(None::<recovery_ui::RecoveryView>));
    let views_close=recovery_views.clone();window.connect_close_request(move |_|{if let Some(view)=views_close.borrow().as_ref(){if view.has_unsaved_key(){view.present();return gtk::glib::Propagation::Stop;}}gtk::glib::Propagation::Proceed});
    let recovery_button=gtk::Button::with_label("Account recovery");recovery_button.set_sensitive(false);
    let views=recovery_views.clone();let parent=window.downgrade();let tx=commands.clone();recovery_button.connect_clicked(move |_|{if let Some(parent)=parent.upgrade(){let mut views=views.borrow_mut();let view=views.get_or_insert_with(||recovery_ui::RecoveryView::new(&parent,tx.clone()));view.present();let _=tx.try_send(worker::Command::RecoveryStatus);}});
    let security_button=gtk::Button::with_label("Devices & security");security_button.set_sensitive(false);
    let views=security_views.clone();let parent=window.downgrade();let tx=commands.clone();security_button.connect_clicked(move |_|{if let Some(parent)=parent.upgrade(){let mut views=views.borrow_mut();let view=views.get_or_insert_with(||security_ui::SecurityView::new(&parent,tx.clone()));view.present();let _=tx.try_send(worker::Command::Devices);}});
    let title=gtk::Label::new(Some("Shadow Messenger"));title.add_css_class("title-1");title.set_xalign(0.0);title.set_hexpand(true);let header=gtk::Box::new(gtk::Orientation::Horizontal,12);header.append(&title);header.append(&conversation_button);header.append(&security_button);header.append(&recovery_button);shell.append(&header);
    let notice=gtk::Label::new(Some("Development build. Use a test account while compatibility and release checks are completed."));
    notice.set_wrap(true);notice.set_xalign(0.0);shell.append(&notice);
    let split=gtk::Paned::new(gtk::Orientation::Horizontal);split.set_vexpand(true);split.set_position(270);
    let sidebar=gtk::Box::new(gtk::Orientation::Vertical,12);
    let label=gtk::Label::new(Some("Connections"));label.set_xalign(0.0);label.add_css_class("heading");sidebar.append(&label);
    let search=gtk::SearchEntry::new();search.set_placeholder_text(Some("Search connections"));sidebar.append(&search);
    let list=gtk::ListBox::new();list.set_vexpand(true);
    let query=search.downgrade();list.set_filter_func(move|row|{let Some(query)=query.upgrade() else{return true};let query=query.text().trim().to_lowercase();query.is_empty()||row.child().and_then(|child|child.downcast::<gtk::Label>().ok()).is_some_and(|label|label.text().to_lowercase().contains(&query))});
    let filtered=list.downgrade();search.connect_search_changed(move |_|{if let Some(list)=filtered.upgrade(){list.invalidate_filter();}});
    sidebar.append(&list);split.set_start_child(Some(&sidebar));
    let room_ids=std::rc::Rc::new(std::cell::RefCell::new(Vec::<String>::new()));
    let drafts=std::rc::Rc::new(std::cell::RefCell::new(std::collections::HashMap::<String,String>::new()));
    let selected_room=std::rc::Rc::new(std::cell::RefCell::new(None::<String>));
    let content=gtk::Box::new(gtk::Orientation::Vertical,12);content.set_margin_start(18);
    let empty=gtk::Label::new(Some("No account connected"));content.append(&empty);
    let history=gtk::TextView::new();history.set_editable(false);history.set_cursor_visible(false);history.set_wrap_mode(gtk::WrapMode::WordChar);
    let history_scroll=gtk::ScrolledWindow::builder().vexpand(true).min_content_height(100).child(&history).build();content.append(&history_scroll);
    let older=gtk::Button::with_label("Load older messages");older.set_sensitive(false);content.append(&older);
    let room_encrypted=std::rc::Rc::new(std::cell::Cell::new(None::<bool>));
    let security_label=gtk::Label::new(None);security_label.set_xalign(0.0);security_label.set_wrap(true);content.append(&security_label);
    let plain_messages=gtk::CheckButton::with_label("Allow unencrypted messages in this room");plain_messages.set_visible(false);content.append(&plain_messages);
    let compose=gtk::TextView::new();compose.set_wrap_mode(gtk::WrapMode::WordChar);compose.set_sensitive(false);
    let compose_scroll=gtk::ScrolledWindow::builder().min_content_height(65).max_content_height(100).child(&compose).build();content.append(&compose_scroll);
    let send_row=gtk::Box::new(gtk::Orientation::Horizontal,8);let send=gtk::Button::with_label("Send");send.set_sensitive(false);
    let retry=gtk::Button::with_label("Retry pending messages");retry.set_sensitive(false);send_row.append(&send);send_row.append(&retry);content.append(&send_row);
    let server=gtk::Entry::builder().placeholder_text("HTTPS homeserver").build();
    let user=gtk::Entry::builder().placeholder_text("Matrix account").build();
    let password=gtk::PasswordEntry::new();password.set_show_peek_icon(true);
    for widget in [server.upcast_ref::<gtk::Widget>(),user.upcast_ref(),password.upcast_ref()] {content.append(widget);}
    let status=gtk::Label::new(Some("Use a test account only. Saved sessions use the desktop keyring and an SDK-encrypted local store."));status.set_wrap(true);status.set_xalign(0.0);content.append(&status);
    let validate=gtk::Button::with_label("Check server address");
    let status_copy=status.clone();let server_check=server.clone();validate.connect_clicked(move |_| {
        status_copy.set_text(match shadow_messenger_core::validate_homeserver(server_check.text().as_str()) {Ok(_)=>"Server address accepted. No connection was made.",Err(message)=>message});
    });content.append(&validate);
    let consent=gtk::CheckButton::with_label("Use a test account; verification and recovery are unfinished");content.append(&consent);
    let buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);
    let login=gtk::Button::with_label("Sign in");login.set_sensitive(false);
    let restore=gtk::Button::with_label("Restore saved account");
    let refresh=gtk::Button::with_label("Refresh connections");refresh.set_sensitive(false);
    let logout=gtk::Button::with_label("Sign out");logout.set_sensitive(false);
    for button in [&login,&restore,&refresh,&logout]{buttons.append(button);}content.append(&buttons);
    let login_copy=login.clone();consent.connect_toggled(move|c|login_copy.set_sensitive(c.is_active()));
    let tx=commands.clone();let status_copy=status.clone();let server_copy=server.clone();let user_copy=user.clone();let password_copy=password.clone();
    login.connect_clicked(move|button|{
        let command=worker::Command::Login{server:server_copy.text().to_string(),username:user_copy.text().to_string(),password:zeroize::Zeroizing::new(password_copy.text().to_string())};
        password_copy.set_text("");
        if tx.try_send(command).is_ok(){button.set_sensitive(false);status_copy.set_text("Signing in and protecting the session with the desktop keyring...");}
        else{status_copy.set_text("An account request is already pending.");}
    });
    for (button,kind) in [(&restore,0),(&refresh,1),(&logout,2)]{
        let tx=commands.clone();let status_copy=status.clone();let recovery_copy=recovery_views.clone();button.connect_clicked(move |_|{
            if kind==2{if let Some(view)=recovery_copy.borrow().as_ref(){if view.has_unsaved_key(){view.present();status_copy.set_text("Save and confirm your recovery key before signing out.");return;}}}
            let command=match kind{0=>worker::Command::Restore,1=>worker::Command::Refresh,_=>worker::Command::Logout};
            if tx.try_send(command).is_ok(){status_copy.set_text("Working...");}else{status_copy.set_text("An account request is already pending.");}
        });
    }
    let ids_copy=room_ids.clone();let selected_copy=selected_room.clone();let tx=commands.clone();let status_copy=status.clone();let compose_copy=compose.clone();let drafts_copy=drafts.clone();let encrypted_copy=room_encrypted.clone();let plain_copy=plain_messages.clone();let heading_copy=empty.clone();let security_copy=security_label.clone();
    list.connect_row_selected(move|_,row|{
        let Some(row)=row else{return};
        if let Some(id)=ids_copy.borrow().get(row.index() as usize).cloned(){
            if let Some(label)=row.child().and_then(|child|child.downcast::<gtk::Label>().ok()){heading_copy.set_text(&label.text());heading_copy.set_tooltip_text(Some(&id));}
            if selected_copy.borrow().as_deref()==Some(id.as_str()){return;}
            *selected_copy.borrow_mut()=Some(id.clone());encrypted_copy.set(None);plain_copy.set_active(false);plain_copy.set_visible(false);security_copy.set_text("Checking room encryption...");compose_copy.set_sensitive(true);let draft=drafts_copy.borrow().get(&id).cloned().unwrap_or_default();compose_copy.buffer().set_text(&draft);
            if tx.try_send(worker::Command::OpenRoom(id)).is_ok(){status_copy.set_text("Loading conversation...");}
        }
    });
    let tx=commands.clone();older.connect_clicked(move |_|{let _=tx.try_send(worker::Command::LoadOlder);});
    let selected_copy=selected_room.clone();let drafts_copy=drafts.clone();let send_copy=send.clone();let encrypted_copy=room_encrypted.clone();let plain_copy=plain_messages.clone();
    compose.buffer().connect_changed(move|buffer|{
        let body=buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).to_string();
        let room=selected_copy.borrow().clone();send_copy.set_sensitive(room.is_some()&&!body.trim().is_empty()&&(encrypted_copy.get()==Some(true)||(encrypted_copy.get()==Some(false)&&plain_copy.is_active())));
        if let Some(room)=room{drafts_copy.borrow_mut().insert(room,body);}
    });
    let tx=commands.clone();let selected_copy=selected_room.clone();let compose_copy=compose.clone();let status_copy=status.clone();let plain_copy=plain_messages.clone();
    send.connect_clicked(move|button|{
        if let Some(room_id)=selected_copy.borrow().clone(){let buffer=compose_copy.buffer();let body=buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).to_string();
            if tx.try_send(worker::Command::Send{room_id,body,allow_unencrypted:plain_copy.is_active()}).is_ok(){button.set_sensitive(false);status_copy.set_text("Queuing message...");}
            else{status_copy.set_text("An account request is already pending. Your draft was kept.");}
        }
    });
    let compose_copy=compose.clone();let send_copy=send.clone();let encrypted_copy=room_encrypted.clone();let selected_copy=selected_room.clone();
    plain_messages.connect_toggled(move|button|{let b=compose_copy.buffer();send_copy.set_sensitive(selected_copy.borrow().is_some()&&!b.text(&b.start_iter(),&b.end_iter(),false).trim().is_empty()&&(encrypted_copy.get()==Some(true)||(encrypted_copy.get()==Some(false)&&button.is_active())));});
    let tx=commands.clone();retry.connect_clicked(move |_|{let _=tx.try_send(worker::Command::RetryPending);});
    let security_parent=window.downgrade();let security_commands=commands.clone();
    gtk::glib::MainContext::default().spawn_local(async move {
        let mut room_signature=None;
        while let Ok(event)=updates.recv().await{
            match event{
                worker::Event::Connected=>{conversation_button.set_sensitive(true);recovery_button.set_sensitive(true);security_button.set_sensitive(true);room_signature=None;server.set_visible(false);user.set_visible(false);password.set_visible(false);validate.set_visible(false);consent.set_visible(false);login.set_visible(false);empty.set_text("Connected. Choose a conversation.");refresh.set_sensitive(true);logout.set_sensitive(true);consent.set_sensitive(false);login.set_sensitive(false);status.set_text("Connected. Loading joined conversations...");}
                worker::Event::Rooms(rooms)=>{
                    let signature:Vec<_>=rooms.iter().map(|room|(room.room_id.clone(),room.name.clone())).collect();
                    if room_signature.as_ref()==Some(&signature){continue;}room_signature=Some(signature);
                    let previous_selection=selected_room.borrow().clone();
                    while let Some(child)=list.first_child(){list.remove(&child);}
                    let count=rooms.len();*room_ids.borrow_mut()=rooms.iter().map(|room|room.room_id.clone()).collect();for room in rooms{let label=gtk::Label::new(Some(&room.name));label.set_xalign(0.0);label.set_margin_top(8);label.set_margin_bottom(8);list.append(&label);}
                    if let Some(id)=previous_selection{if let Some(index)=room_ids.borrow().iter().position(|item|item==&id){list.select_row(list.row_at_index(index as i32).as_ref());}else{*selected_room.borrow_mut()=None;compose.set_sensitive(false);send.set_sensitive(false);history.buffer().set_text("");}}
                    status.set_text(&format!("{count} joined conversations. Verification and recovery remain unfinished."));
                }
                worker::Event::Invitations(invites)=>{conversation_button.set_label(&if invites.is_empty(){"Conversations".into()}else{format!("Conversations ({} invites)",invites.len())});if let Some(view)=conversation_views.borrow().as_ref(){view.invitations(invites);}}
                worker::Event::ConversationAction(message)=>{if let Some(view)=conversation_views.borrow().as_ref(){view.action(&message);}status.set_text(&message);}
                worker::Event::ConversationCreated{room_id,message}=>{if let Some(view)=conversation_views.borrow().as_ref(){view.created(&message);}if let Some(index)=room_ids.borrow().iter().position(|id|id==&room_id){list.select_row(list.row_at_index(index as i32).as_ref());}status.set_text(&message);}
                worker::Event::RecoveryStatus{message,can_create}=>{if let Some(view)=recovery_views.borrow().as_ref(){view.status(&message,can_create);}}
                worker::Event::RecoveryKey(key)=>{if let Some(view)=recovery_views.borrow().as_ref(){view.created(key);}}
                worker::Event::RecoveryRestored=>{if let Some(view)=recovery_views.borrow().as_ref(){view.restored();}}
                worker::Event::Devices{user_id,devices}=>{if let Some(view)=security_views.borrow().as_ref(){view.devices(&user_id,devices);}}
                worker::Event::Verification{flow_id,state}=>{
                    let mut views=security_views.borrow_mut();
                    if views.is_none()&&matches!(state,verification::State::Requested{..}){if let Some(parent)=security_parent.upgrade(){*views=Some(security_ui::SecurityView::new(&parent,security_commands.clone()));}}
                    if let Some(view)=views.as_ref(){view.verification(flow_id,state);}
                }
                worker::Event::RoomSecurity{room_id,encrypted}=>{
                    if selected_room.borrow().as_deref()!=Some(room_id.as_str()){continue;}
                    room_encrypted.set(Some(encrypted));plain_messages.set_visible(!encrypted);plain_messages.set_active(false);
                    security_label.set_text(if encrypted{"Encrypted room. Verify devices before trusting identities."}else{"Not encrypted: the server can read messages sent to this room."});
                    let b=compose.buffer();send.set_sensitive(encrypted&&!b.text(&b.start_iter(),&b.end_iter(),false).trim().is_empty());
                }
                worker::Event::Timeline{room_id,messages}=>{
                    if selected_room.borrow().as_deref()!=Some(room_id.as_str()){continue;}
                    let count=messages.len();let mut text=String::new();for message in messages{text.push_str(&message.sender);if !message.state.is_empty(){text.push_str(" [");text.push_str(message.state);text.push_str("]");}text.push_str("\n");text.push_str(&message.body);text.push_str("\n\n");}
                    let adjustment=history_scroll.vadjustment();let at_end=adjustment.value()+adjustment.page_size()>=adjustment.upper()-20.0;history.buffer().set_text(&text);if at_end{gtk::glib::idle_add_local_once(move||adjustment.set_value((adjustment.upper()-adjustment.page_size()).max(0.0)));}retry.set_sensitive(true);older.set_sensitive(count<200);status.set_text(if count==200{"Showing the latest 200 events. Extended history and verification remain unfinished."}else{"Live conversation preview. Queued and failed messages are labelled; verification and recovery remain unfinished."});
                }
                worker::Event::Queued{room_id,body}=>{
                    if drafts.borrow().get(&room_id)==Some(&body){drafts.borrow_mut().remove(&room_id);}
                    let buffer=compose.buffer();if selected_room.borrow().as_deref()==Some(room_id.as_str())&&buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).as_str()==body{buffer.set_text("");}
                    status.set_text("Message queued. Its timeline status will update when the server accepts it.");
                }
                worker::Event::SignedOut=>{conversation_button.set_sensitive(false);conversation_button.set_label("Conversations");if let Some(view)=conversation_views.borrow().as_ref(){view.signed_out();}recovery_button.set_sensitive(false);if let Some(view)=recovery_views.borrow().as_ref(){view.signed_out();}if let Some(view)=security_views.borrow().as_ref(){view.signed_out();}security_button.set_sensitive(false);room_signature=None;room_encrypted.set(None);plain_messages.set_visible(false);plain_messages.set_active(false);security_label.set_text("");server.set_visible(true);user.set_visible(true);password.set_visible(true);validate.set_visible(true);consent.set_visible(true);login.set_visible(true);compose.set_sensitive(false);send.set_sensitive(false);retry.set_sensitive(false);room_ids.borrow_mut().clear();*selected_room.borrow_mut()=None;history.buffer().set_text("");older.set_sensitive(false);while let Some(child)=list.first_child(){list.remove(&child);}empty.set_text("No account connected");refresh.set_sensitive(false);logout.set_sensitive(false);consent.set_sensitive(true);login.set_sensitive(consent.is_active());status.set_text("No account connected. Choose a test account to continue development checks.");}
                worker::Event::Error(message)=>{if let Some(view)=conversation_views.borrow().as_ref(){view.error(&message);}if let Some(view)=recovery_views.borrow().as_ref(){view.error(&message);}if let Some(view)=security_views.borrow().as_ref(){view.error(&message);}status.set_text(&message);let buffer=compose.buffer();send.set_sensitive(selected_room.borrow().is_some()&&!buffer.text(&buffer.start_iter(),&buffer.end_iter(),false).trim().is_empty()&&(room_encrypted.get()==Some(true)||(room_encrypted.get()==Some(false)&&plain_messages.is_active())));if consent.is_sensitive(){login.set_sensitive(consent.is_active());}}
            }
        }
    });
    split.set_end_child(Some(&content));shell.append(&split);window.set_child(Some(&shell));window.present();
}

#[cfg(test)]
mod ui_tests {
    use super::*;
    fn descendants(widget:&gtk::Widget,out:&mut Vec<gtk::Widget>){
        out.push(widget.clone());let mut child=widget.first_child();
        while let Some(item)=child{descendants(&item,out);child=item.next_sibling();}
    }
    #[test]
    #[ignore = "requires a graphical test session"]
    fn invalid_server_is_rejected_from_the_actual_button(){
        gtk::init().unwrap();
        let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.UiTest").build();
        app.register(None::<&gtk::gio::Cancellable>).unwrap();build(&app);
        let window=app.windows().into_iter().next().unwrap();build(&app);assert_eq!(app.windows().len(),1);let mut widgets=Vec::new();descendants(window.upcast_ref(),&mut widgets);
        let server=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>())
            .find(|e|e.placeholder_text().as_deref()==Some("HTTPS homeserver")).unwrap();
        server.set_text("http://invalid.example");
        let button=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>())
            .find(|b|b.label().as_deref()==Some("Check server address")).unwrap();
        button.emit_clicked();
        assert!(widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>())
            .any(|label|label.text().contains("Use an HTTPS homeserver address.")));
        if std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").is_ok(){
            assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
            let account:serde_json::Value=serde_json::from_str(&std::fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
            let user=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>()).find(|e|e.placeholder_text().as_deref()==Some("Matrix account")).unwrap();
            let password=widgets.iter().find_map(|w|w.downcast_ref::<gtk::PasswordEntry>()).unwrap();
            let consent=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::CheckButton>()).find(|c|c.label().as_deref().is_some_and(|label|label.starts_with("Use a test account;"))).unwrap();
            let login=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|b|b.label().as_deref()==Some("Sign in")).unwrap();
            let list=widgets.iter().find_map(|w|w.downcast_ref::<gtk::ListBox>()).unwrap();
            let history=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::TextView>()).find(|v|!v.is_editable()).unwrap();
            let compose=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::TextView>()).find(|v|v.is_editable()).unwrap();
            eprintln!("GTK integration: login and peer setup");let peer=verification_peer(account.clone());wait_until(||peer.ready.try_recv().is_ok());
            server.set_text(account["server"].as_str().unwrap());user.set_text(account["username"].as_str().unwrap());password.set_text(account["password"].as_str().unwrap());consent.set_active(true);login.emit_clicked();
            wait_until(||list.row_at_index(0).is_some());
            assert!(password.text().is_empty());
            let search=widgets.iter().find_map(|widget|widget.downcast_ref::<gtk::SearchEntry>()).unwrap();search.set_text("__no_matching_fixture_room__");wait_until(||!list.row_at_index(0).unwrap().is_child_visible());search.set_text("");wait_until(||list.row_at_index(0).unwrap().is_child_visible());
            list.select_row(list.row_at_index(0).as_ref());
            wait_until(||{let b=history.buffer();!b.text(&b.start_iter(),&b.end_iter(),false).is_empty()});
            let body=format!("Disposable GTK send-button integration message {}",std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos());compose.buffer().set_text(&body);
            let send=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|b|b.label().as_deref()==Some("Send")).unwrap();
            assert!(send.is_sensitive());send.emit_clicked();
            wait_until(||{let b=compose.buffer();b.text(&b.start_iter(),&b.end_iter(),false).is_empty()});
            wait_until(||{let b=history.buffer();b.text(&b.start_iter(),&b.end_iter(),false).contains(&body)});
            wait_until(||{let b=history.buffer();let text=b.text(&b.start_iter(),&b.end_iter(),false);!text.contains("[Queued]")&&!text.contains("[Not sent]")});
            eprintln!("GTK integration: conversation invitations and creation");
            let invited=invitation_peer(account.clone());wait_until(||invited.ready.try_recv().is_ok());
            let conversation_button=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref().is_some_and(|label|label.starts_with("Conversations"))).unwrap();conversation_button.emit_clicked();
            let conversation_dialog=gtk::Window::list_toplevels().into_iter().filter_map(|w|w.downcast::<gtk::Window>().ok()).find(|w|w.title().as_deref()==Some("Conversations & invitations")).unwrap();
            let mut conversation_widgets=Vec::new();
            for (name,action) in [(&invited.accept_name,"Accept invitation"),(&invited.decline_name,"Decline invitation")]{
                wait_until(||{conversation_widgets.clear();descendants(conversation_dialog.upcast_ref(),&mut conversation_widgets);conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().starts_with(name))});
                let label=conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).find(|label|label.text().starts_with(name)).unwrap();let mut row_widgets=Vec::new();descendants(&label.parent().unwrap(),&mut row_widgets);
                row_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some(action)).unwrap().emit_clicked();
                let expected=if action.starts_with("Accept"){"Invitation accepted."}else{"Invitation declined."};
                wait_until(||{conversation_widgets.clear();descendants(conversation_dialog.upcast_ref(),&mut conversation_widgets);conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text()==expected)});
            }
            let people=conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>()).find(|entry|entry.placeholder_text().as_deref()==Some("Matrix addresses, separated by commas")).unwrap().clone();
            let create=conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some("Create encrypted conversation")).unwrap().clone();
            people.set_text("not-an-address");create.emit_clicked();wait_until(||conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().starts_with("Use full Matrix addresses")));assert!(create.is_sensitive());assert_eq!(people.text().as_str(),"not-an-address");
            people.set_text(&format!("@{}:localhost",account["bob_username"].as_str().unwrap()));create.emit_clicked();wait_until(||conversation_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().starts_with("Encrypted conversation created.")));assert!(people.text().is_empty());conversation_dialog.close();invited.done.send(()).unwrap();invited.thread.join().unwrap();
            eprintln!("GTK integration: message accepted; outgoing verification");let security=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|b|b.label().as_deref()==Some("Devices & security")).unwrap();security.emit_clicked();
            let dialog=gtk::Window::list_toplevels().into_iter().filter_map(|w|w.downcast::<gtk::Window>().ok()).find(|w|w.title().as_deref()==Some("Devices & security")).unwrap();
            let mut security_widgets=Vec::new();wait_until(||{security_widgets.clear();descendants(dialog.upcast_ref(),&mut security_widgets);security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().contains(&peer.name))});
            let label=security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).find(|label|label.text().contains(&peer.name)).unwrap();
            let row=label.parent().unwrap();let verify=row.last_child().unwrap().downcast::<gtk::Button>().unwrap();verify.emit_clicked();
            let mut comparison=None;wait_until(||{comparison=peer.numbers.try_recv().ok();comparison.is_some()});
            let (a,b,c)=comparison.unwrap();let expected=format!("{a}   {b}   {c}");
            wait_until(||security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text()==expected));
            let confirm=security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some("Numbers match")).unwrap();assert!(confirm.is_sensitive());confirm.emit_clicked();peer.confirm.send(()).unwrap();
            wait_until(||security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text()=="Device verified."));wait_until(||peer.done.try_recv().is_ok());
            let accept=security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some("Accept verification")).unwrap();
            let cancel=security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some("Cancel verification")).unwrap();
            eprintln!("GTK integration: incoming cancellation");peer.request.send(()).unwrap();wait_until(||accept.is_visible());assert!(!confirm.is_sensitive());cancel.emit_clicked();
            wait_until(||security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().contains("Verification cancelled.")));wait_until(||peer.done.try_recv().is_ok());
            eprintln!("GTK integration: incoming confirmation");peer.request.send(()).unwrap();wait_until(||accept.is_visible());accept.emit_clicked();
            let mut incoming=None;wait_until(||{incoming=peer.numbers.try_recv().ok();incoming.is_some()});let (a,b,c)=incoming.unwrap();let expected=format!("{a}   {b}   {c}");
            wait_until(||security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text()==expected));assert!(confirm.is_sensitive());confirm.emit_clicked();peer.confirm.send(()).unwrap();
            wait_until(||security_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text()=="Device verified."));wait_until(||peer.done.try_recv().is_ok());dialog.close();peer.thread.join().unwrap();
            eprintln!("GTK integration: verification complete; sign out");let logout=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|b|b.label().as_deref()==Some("Sign out")).unwrap();logout.emit_clicked();
            wait_until(||!logout.is_sensitive());assert!(!send.is_sensitive());
        }
        window.close();
    }
    #[test]
    #[ignore = "requires a fresh disposable Matrix account, graphical session and isolated Secret Service"]
    fn recovery_controls_create_and_restore_on_a_new_device(){
        assert_eq!(std::env::var("SHADOW_MESSENGER_ISOLATED_KEYRING_TEST").as_deref(),Ok("1"));
        gtk::init().unwrap();let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.RecoveryTest").build();app.register(None::<&gtk::gio::Cancellable>).unwrap();build(&app);
        let window=app.windows().into_iter().next().unwrap();let mut widgets=Vec::new();descendants(window.upcast_ref(),&mut widgets);
        let account:serde_json::Value=serde_json::from_str(&std::fs::read_to_string(std::env::var("SHADOW_MESSENGER_MATRIX_FIXTURE").unwrap()).unwrap()).unwrap();
        let server=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>()).find(|e|e.placeholder_text().as_deref()==Some("HTTPS homeserver")).unwrap();
        let user=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>()).find(|e|e.placeholder_text().as_deref()==Some("Matrix account")).unwrap();
        let password=widgets.iter().find_map(|w|w.downcast_ref::<gtk::PasswordEntry>()).unwrap();
        let consent=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::CheckButton>()).find(|c|c.label().as_deref().is_some_and(|label|label.starts_with("Use a test account;"))).unwrap();
        let button=|label:&str|widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some(label)).unwrap().clone();
        server.set_text(account["server"].as_str().unwrap());user.set_text(account["recovery_username"].as_str().unwrap());password.set_text(account["recovery_password"].as_str().unwrap());consent.set_active(true);button("Sign in").emit_clicked();wait_until(||button("Account recovery").is_sensitive());
        button("Account recovery").emit_clicked();let dialog=gtk::Window::list_toplevels().into_iter().filter_map(|w|w.downcast::<gtk::Window>().ok()).find(|w|w.title().as_deref()==Some("Account recovery")).unwrap();
        let mut recovery_widgets=Vec::new();descendants(dialog.upcast_ref(),&mut recovery_widgets);
        let recovery_button=|label:&str|recovery_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>()).find(|button|button.label().as_deref()==Some(label)).unwrap().clone();
        let entry=|name:&str|recovery_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::PasswordEntry>()).find(|entry|entry.widget_name().as_str()==name).unwrap().clone();
        let option=|label:&str|recovery_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::CheckButton>()).find(|button|button.label().as_deref()==Some(label)).unwrap().clone();
        option("Set up encrypted key backup for this account").set_active(true);wait_until(||{recovery_button("Refresh recovery status").emit_clicked();recovery_button("Create recovery key").is_sensitive()});
        entry("recovery-setup-password").set_text(account["recovery_password"].as_str().unwrap());recovery_button("Create recovery key").emit_clicked();assert!(entry("recovery-setup-password").text().is_empty());
        wait_until(||!entry("recovery-created-key").text().is_empty());let key=zeroize::Zeroizing::new(entry("recovery-created-key").text().to_string());assert!(!key.is_empty());assert!(!recovery_button("Create recovery key").is_sensitive());
        window.close();assert!(window.is_visible());button("Sign out").emit_clicked();assert!(button("Sign out").is_sensitive());
        dialog.close();assert!(dialog.is_visible());assert!(!recovery_button("Clear displayed key").is_sensitive());option("I saved my recovery key somewhere safe").set_active(true);recovery_button("Clear displayed key").emit_clicked();assert!(entry("recovery-created-key").text().is_empty());dialog.close();
        button("Sign out").emit_clicked();wait_until(||!button("Sign out").is_sensitive());
        password.set_text(account["recovery_password"].as_str().unwrap());button("Sign in").emit_clicked();wait_until(||button("Account recovery").is_sensitive());button("Account recovery").emit_clicked();
        entry("recovery-existing-key").set_text("invalid recovery key");recovery_button("Restore encrypted history").emit_clicked();assert!(entry("recovery-existing-key").text().is_empty());
        wait_until(||recovery_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().contains("The recovery key could not unlock")));
        entry("recovery-existing-key").set_text(key.as_str());recovery_button("Restore encrypted history").emit_clicked();
        wait_until(||recovery_widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>()).any(|label|label.text().starts_with("Account recovery keys restored.")));
        assert!(entry("recovery-existing-key").text().is_empty());assert!(!recovery_button("Create recovery key").is_sensitive());
        button("Sign out").emit_clicked();wait_until(||!button("Sign out").is_sensitive());assert!(!dialog.is_visible());window.close();
    }
    fn wait_until(mut condition:impl FnMut()->bool){
        let limit=std::time::Instant::now()+std::time::Duration::from_secs(60);
        while !condition(){assert!(std::time::Instant::now()<limit,"GTK integration action timed out");while gtk::glib::MainContext::default().iteration(false){}std::thread::sleep(std::time::Duration::from_millis(10));}
    }
    struct InvitationPeer {accept_name:String,decline_name:String,ready:std::sync::mpsc::Receiver<()>,done:std::sync::mpsc::Sender<()>,thread:std::thread::JoinHandle<()>}
    fn invitation_peer(account:serde_json::Value)->InvitationPeer{
        let prefix=format!("GTK invitation {}",std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos());let accept_name=format!("{prefix} accept");let decline_name=format!("{prefix} decline");let names=[accept_name.clone(),decline_name.clone()];
        let (ready_tx,ready)=std::sync::mpsc::channel();let (done,done_rx)=std::sync::mpsc::channel();
        let thread=std::thread::spawn(move||{tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build().unwrap().block_on(async move{
            tokio::time::timeout(std::time::Duration::from_secs(120),async{
                let client=crate::persistence::client_builder(account["server"].as_str().unwrap()).unwrap().build().await.unwrap();client.matrix_auth().login_username(account["bob_username"].as_str().unwrap(),account["bob_password"].as_str().unwrap()).send().await.unwrap();
                client.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();let copy=client.clone();let sync=tokio::spawn(async move{copy.sync(matrix_sdk::config::SyncSettings::default().timeout(std::time::Duration::from_secs(1))).await});
                let address=format!("@{}:localhost",account["username"].as_str().unwrap());for name in names{crate::conversations::create(&client,&name,&address).await.unwrap();}
                ready_tx.send(()).unwrap();tokio::task::spawn_blocking(move||done_rx.recv_timeout(std::time::Duration::from_secs(90)).unwrap()).await.unwrap();sync.abort();client.logout().await.unwrap();
            }).await.expect("GUI invitation peer timed out");
        });});InvitationPeer{accept_name,decline_name,ready,done,thread}
    }
    struct Peer {name:String,request:std::sync::mpsc::Sender<()>,ready:std::sync::mpsc::Receiver<()>,numbers:std::sync::mpsc::Receiver<(u16,u16,u16)>,confirm:std::sync::mpsc::Sender<()>,done:std::sync::mpsc::Receiver<()>,thread:std::thread::JoinHandle<()>}
    fn verification_peer(account:serde_json::Value)->Peer{
        let name=format!("GUI verification peer {}",std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos());let peer_name=name.clone();
        let (request,request_start)=std::sync::mpsc::channel();let (ready_tx,ready)=std::sync::mpsc::channel();let (number_tx,numbers)=std::sync::mpsc::channel();let (confirm,confirm_rx)=std::sync::mpsc::channel();let (done_tx,done)=std::sync::mpsc::channel();
        let confirm_rx=std::sync::Arc::new(std::sync::Mutex::new(confirm_rx));let request_start=std::sync::Arc::new(std::sync::Mutex::new(request_start));
        let thread=std::thread::spawn(move||{tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build().unwrap().block_on(async move{
            use std::time::Duration;
            tokio::time::timeout(Duration::from_secs(150),async{
                let client=crate::persistence::client_builder(account["server"].as_str().unwrap()).unwrap().build().await.unwrap();
                client.matrix_auth().login_username(account["username"].as_str().unwrap(),account["password"].as_str().unwrap()).initial_device_display_name(&peer_name).send().await.unwrap();client.sync_once(matrix_sdk::config::SyncSettings::default()).await.unwrap();
                let (request_tx,request_rx)=async_channel::bounded(1);
                client.add_event_handler(move|event:matrix_sdk::ruma::events::key::verification::request::ToDeviceKeyVerificationRequestEvent|{let tx=request_tx.clone();async move{let _=tx.send((event.sender,event.content.transaction_id,event.content.from_device)).await;}});
                let sync_client=client.clone();let sync=tokio::spawn(async move{sync_client.sync(matrix_sdk::config::SyncSettings::default().timeout(Duration::from_secs(1))).await});ready_tx.send(()).unwrap();
                let (user,id,device)=request_rx.recv().await.unwrap();let request=client.encryption().get_verification_request(&user,id.as_str()).await.unwrap();
                let mut flow=crate::verification::VerificationFlow::accept(&client,request).await.unwrap();
                let values=loop{if let crate::verification::State::Compare(numbers)=flow.refresh().await.unwrap(){break numbers;}tokio::time::sleep(Duration::from_millis(50)).await;};
                number_tx.send(values).unwrap();tokio::task::spawn_blocking({let confirm_rx=confirm_rx.clone();move||confirm_rx.lock().unwrap().recv_timeout(Duration::from_secs(60)).unwrap()}).await.unwrap();flow.confirm_match().await.unwrap();
                while flow.refresh().await.unwrap()!=crate::verification::State::Verified{tokio::time::sleep(Duration::from_millis(50)).await;}
                done_tx.send(()).unwrap();
                for cancel_expected in [true,false]{
                    tokio::task::spawn_blocking({let request_start=request_start.clone();move||request_start.lock().unwrap().recv_timeout(Duration::from_secs(60)).unwrap()}).await.unwrap();
                    let mut incoming=crate::verification::VerificationFlow::request(&client,&user,&device).await.unwrap();
                    if cancel_expected{
                        while incoming.refresh().await.unwrap()!=crate::verification::State::Cancelled{tokio::time::sleep(Duration::from_millis(50)).await;}
                    }else{
                        let values=loop{let state=incoming.refresh().await.unwrap();if state==crate::verification::State::Ready&&incoming.sas_handle().is_none(){incoming.start_numbers().await.unwrap();}if let crate::verification::State::Compare(numbers)=state{break numbers;}tokio::time::sleep(Duration::from_millis(50)).await;};
                        number_tx.send(values).unwrap();tokio::task::spawn_blocking({let confirm_rx=confirm_rx.clone();move||confirm_rx.lock().unwrap().recv_timeout(Duration::from_secs(60)).unwrap()}).await.unwrap();incoming.confirm_match().await.unwrap();
                        while incoming.refresh().await.unwrap()!=crate::verification::State::Verified{tokio::time::sleep(Duration::from_millis(50)).await;}
                    }done_tx.send(()).unwrap();
                }
                sync.abort();client.logout().await.unwrap();
            }).await.expect("GUI verification peer timed out");
        });});Peer{name,request,ready,numbers,confirm,done,thread}
    }

}
