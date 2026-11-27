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
mod appearance;
mod contacts;
mod chat_ui;
mod preferences_ui;
mod registration_ui;
mod settings;
mod shell;
mod sound;
use std::{cell::{Cell,RefCell},collections::{HashMap,HashSet},rc::Rc};
use async_channel::Sender;
use gtk::{glib,prelude::*};
use gtk::glib::variant::ToVariant;
use shadow_messenger_core::{Buddy,Connection,Presence};
use worker::{Command,Event};

fn main() -> glib::ExitCode {
    let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.Development").build();
    app.connect_activate(build);
    app.run()
}

struct Login {
    root:gtk::Box,
    server:gtk::Entry,
    user:gtk::Entry,
    password:gtk::PasswordEntry,
    consent:gtk::CheckButton,
    login:gtk::Button,
    restore:gtk::Button,
    refresh:gtk::Button,
    logout:gtk::Button,
    validate:gtk::Button,
    status:gtk::Label,
    create_account:gtk::Button,
    help:gtk::Button,
}

fn login_page(commands:&Sender<Command>)->Login{
    let root=gtk::Box::new(gtk::Orientation::Vertical,0);root.set_vexpand(true);
    let card=gtk::Box::new(gtk::Orientation::Vertical,10);card.add_css_class("messenger-card");card.set_halign(gtk::Align::Center);card.set_valign(gtk::Align::Center);card.set_size_request(460,-1);
    let brand_row=gtk::Box::new(gtk::Orientation::Horizontal,10);
    let brand=appearance::brand_logo(52);brand.set_valign(gtk::Align::Center);
    let titles=gtk::Box::new(gtk::Orientation::Vertical,0);
    let title=gtk::Label::new(Some("Shadow Messenger"));title.add_css_class("messenger-page-title");title.set_xalign(0.0);
    let subtitle=gtk::Label::new(Some("Secure Messaging for ShadowRealm-OS"));subtitle.add_css_class("messenger-muted");subtitle.set_xalign(0.0);
    titles.append(&title);titles.append(&subtitle);brand_row.append(&brand);brand_row.append(&titles);card.append(&brand_row);
    let notice=gtk::Label::new(Some("Development build. Use a test account while compatibility and release checks are completed."));notice.set_wrap(true);notice.set_xalign(0.0);notice.add_css_class("messenger-notice");card.append(&notice);
    let help=gtk::Button::with_label("How does this work?");help.add_css_class("flat");help.set_halign(gtk::Align::Start);card.append(&help);
    let server=gtk::Entry::builder().placeholder_text("HTTPS homeserver").build();
    let user=gtk::Entry::builder().placeholder_text("Matrix account").build();
    let password=gtk::PasswordEntry::new();password.set_show_peek_icon(true);password.set_placeholder_text(Some("Password"));
    let consent=gtk::CheckButton::with_label("Use a test account; verification and recovery are unfinished");
    for widget in [server.upcast_ref::<gtk::Widget>(),user.upcast_ref(),password.upcast_ref(),consent.upcast_ref()]{card.append(widget);}
    let buttons=gtk::FlowBox::builder().selection_mode(gtk::SelectionMode::None).min_children_per_line(1).max_children_per_line(2).column_spacing(8).row_spacing(6).build();
    let login=gtk::Button::with_label("Sign in");login.add_css_class("suggested-action");login.set_sensitive(false);login.set_hexpand(true);
    let restore=gtk::Button::with_label("Restore saved account");
    let refresh=gtk::Button::with_label("Refresh connections");
    let logout=gtk::Button::with_label("Sign out");logout.set_sensitive(false);
    for button in [&login,&restore,&refresh,&logout]{buttons.insert(button,-1);}
    card.append(&buttons);
    let validate=gtk::Button::with_label("Check server address");validate.set_halign(gtk::Align::Start);card.append(&validate);
    let status=gtk::Label::new(Some("Use a test account only. Saved sessions use the desktop keyring and an SDK-encrypted local store."));status.set_wrap(true);status.set_xalign(0.0);status.add_css_class("messenger-muted");card.append(&status);
    let create_account=gtk::Button::with_label("Create a new account…");create_account.set_halign(gtk::Align::Start);card.append(&create_account);
    let create_note=gtk::Label::new(Some("Opens a separate form. Account creation depends on the homeserver; providers can disable it or require a sign-up page."));create_note.set_wrap(true);create_note.set_xalign(0.0);create_note.add_css_class("messenger-muted");card.append(&create_note);
    let scroller=gtk::ScrolledWindow::builder().hscrollbar_policy(gtk::PolicyType::Never).vscrollbar_policy(gtk::PolicyType::Automatic).child(&card).build();
    scroller.set_vexpand(true);root.append(&scroller);

    let login_copy=login.clone();consent.connect_toggled(move|consent|login_copy.set_sensitive(consent.is_active()));
    let tx=commands.clone();let status_copy=status.clone();let server_copy=server.clone();let user_copy=user.clone();let password_copy=password.clone();
    login.connect_clicked(move|button|{
        let command=Command::Login{server:server_copy.text().to_string(),username:user_copy.text().to_string(),password:zeroize::Zeroizing::new(password_copy.text().to_string())};
        password_copy.set_text("");
        if tx.try_send(command).is_ok(){button.set_sensitive(false);status_copy.set_text("Signing in and protecting the session with the desktop keyring...");}
        else{status_copy.set_text("An account request is already pending.");}
    });
    let login_from_password=login.clone();password.connect_activate(move|_|{if login_from_password.is_sensitive(){login_from_password.emit_clicked();}});
    let status_copy=status.clone();let server_copy=server.clone();
    validate.connect_clicked(move|_|{status_copy.set_text(match shadow_messenger_core::validate_homeserver(server_copy.text().as_str()){Ok(_)=>"Server address accepted. No connection was made.",Err(message)=>message});});
    let tx=commands.clone();let status_copy=status.clone();
    restore.connect_clicked(move|_|{if tx.try_send(Command::Restore).is_ok(){status_copy.set_text("Restoring the saved account...");}else{status_copy.set_text("An account request is already pending.");}});
    let tx=commands.clone();let status_copy=status.clone();
    refresh.connect_clicked(move|_|{if tx.try_send(Command::Refresh).is_ok(){status_copy.set_text("Refreshing connections...");}else{status_copy.set_text("An account request is already pending.");}});
    Login{root,server,user,password,consent,login,restore,refresh,logout,validate,status,create_account,help}
}

fn presence_line(buddy:&Buddy)->String{
    if buddy.status.trim().is_empty(){buddy.presence.label().to_owned()}else{format!("{} · {}",buddy.presence.label(),buddy.status)}
}
fn time_now()->String{
    glib::DateTime::now_local().ok().and_then(|date|date.format("%H:%M").ok()).map(|text|text.to_string()).unwrap_or_default()
}
fn notify(app:&gtk::Application,room_id:&str,title:&str,body:&str,mention:bool){
    let notification=gtk::gio::Notification::new(title);
    notification.set_body(Some(body));
    if mention{notification.set_priority(gtk::gio::NotificationPriority::High);}
    notification.set_default_action_and_target_value("app.open-room",Some(&room_id.to_variant()));
    app.send_notification(Some(&format!("shadow-messenger:{room_id}")),&notification);
}
fn add_action(window:&gtk::ApplicationWindow,name:&str,callback:impl Fn()+ 'static){
    let action=gtk::gio::SimpleAction::new(name,None);action.connect_activate(move|_,_|callback());window.add_action(&action);
}
fn chat_in_front(chat:&Rc<RefCell<Option<chat_ui::ChatWindow>>>)->Option<gtk::Window>{
    // A hidden chat can still report itself visible for a moment; only use it
    // as a parent while its window is actually mapped on screen.
    chat.borrow().as_ref().filter(|view|view.is_visible()&&view.window().is_mapped()).map(|view|view.window().clone())
}
fn raise_target(main:&gtk::ApplicationWindow,preferences:&Rc<RefCell<Option<preferences_ui::Preferences>>>,chat:&Rc<RefCell<Option<chat_ui::ChatWindow>>>)->gtk::Window{
    if let Some(view)=preferences.borrow().as_ref().filter(|view|view.is_visible()&&view.window().is_mapped()){return view.window().clone();}
    if let Some(window)=chat_in_front(chat){return window;}
    main.clone().upcast()
}
fn guide_section(root:&gtk::Box,title:&str,body:&str){
    let heading=gtk::Label::new(Some(title));heading.set_xalign(0.0);heading.add_css_class("messenger-section");root.append(&heading);
    let text=gtk::Label::new(Some(body));text.set_wrap(true);text.set_xalign(0.0);text.add_css_class("messenger-body");root.append(&text);
}
fn how_it_works(parent:&gtk::Window){
    let window=gtk::Window::builder().title("How Shadow Messenger Works").transient_for(parent).modal(true).default_width(640).default_height(640).build();
    window.add_css_class("messenger-window");
    let root=gtk::Box::new(gtk::Orientation::Vertical,10);root.set_margin_top(22);root.set_margin_bottom(22);root.set_margin_start(22);root.set_margin_end(22);
    let header=gtk::Box::new(gtk::Orientation::Horizontal,14);header.append(&appearance::brand_logo(60));
    let titles=gtk::Box::new(gtk::Orientation::Vertical,0);
    let title=gtk::Label::new(Some("How Shadow Messenger works"));title.add_css_class("messenger-page-title");title.set_xalign(0.0);
    let subtitle=gtk::Label::new(Some("A plain-language guide to Matrix"));subtitle.add_css_class("messenger-muted");subtitle.set_xalign(0.0);
    titles.append(&title);titles.append(&subtitle);header.append(&titles);root.append(&header);
    guide_section(&root,"A chat app, not a social network","Shadow Messenger is a native chat app for ShadowRealm-OS. It connects to Matrix, an open messaging protocol. Matrix is not one company's chat service: your account lives on a homeserver, and different homeservers can talk to each other.");
    guide_section(&root,"Accounts, homeservers and addresses","Your account has an address like @you:example.org. A room has an address like #team:example.org. A homeserver stores your account data and delivers your messages. It can be run by a community, an organisation, or you. To start, enter the HTTPS address of a homeserver and sign in, or create an account if that server allows it.");
    guide_section(&root,"Rooms and direct messages","Every conversation is a room, whether it is a direct chat or a group. You can invite people, accept or decline invitations, and leave a room. Messages are delivered to the homeservers used by the people in that room.");
    guide_section(&root,"What encryption protects","Rooms marked as encrypted use Matrix end-to-end encryption. The message is locked on the sender's device and only members' devices can unlock it, so the homeserver stores ciphertext rather than readable text. An unencrypted room can be read by the homeserver, which is why Shadow Messenger warns before you send in one. Never share your recovery key.");
    guide_section(&root,"Devices, verification and storage","Each sign-in is a separate device. Verify a new device from an existing trusted device or with your recovery key so other people can trust it. Shadow Messenger keeps your saved session in the desktop keyring and its local message store is encrypted by the Matrix SDK. Signing out removes the session from this device; your account remains on the homeserver.");
    guide_section(&root,"A development build","Shadow Messenger is still being tested. Use test accounts, not personal conversations. Your homeserver's operator controls availability, message retention and account recovery, and different providers may require different sign-up steps.");
    let close=gtk::Button::with_label("Close");close.set_halign(gtk::Align::End);let window_copy=window.clone();close.connect_clicked(move|_|{window_copy.close();});root.append(&close);
    let scroller=gtk::ScrolledWindow::builder().hscrollbar_policy(gtk::PolicyType::Never).vscrollbar_policy(gtk::PolicyType::Automatic).vexpand(true).child(&root).build();
    window.set_child(Some(&scroller));window.present();
}
fn about(parent:&gtk::Window){
    let window=gtk::Window::builder().title("About Shadow Messenger").transient_for(parent).modal(true).default_width(440).default_height(320).build();
    window.add_css_class("messenger-window");
    let root=gtk::Box::new(gtk::Orientation::Vertical,10);root.set_margin_top(22);root.set_margin_bottom(22);root.set_margin_start(22);root.set_margin_end(22);
    let header=gtk::Box::new(gtk::Orientation::Horizontal,14);header.append(&appearance::brand_logo(52));
    let titles=gtk::Box::new(gtk::Orientation::Vertical,0);
    let title=gtk::Label::new(Some("Shadow Messenger"));title.add_css_class("messenger-page-title");title.set_xalign(0.0);
    let version=gtk::Label::new(Some(&format!("Development build {}",env!("CARGO_PKG_VERSION"))));version.set_xalign(0.0);version.add_css_class("messenger-muted");
    titles.append(&title);titles.append(&version);header.append(&titles);root.append(&header);
    let note=gtk::Label::new(Some("A native GTK4 Matrix client for ShadowRealm-OS. Encrypted rooms use Matrix end-to-end encryption. This development build is not ready for personal conversations."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");
    let license=gtk::Label::new(Some("Original project code is MIT licensed. Dependency licenses must be collected before binary distribution."));license.set_wrap(true);license.set_xalign(0.0);license.add_css_class("messenger-muted");
    let close=gtk::Button::with_label("Close");close.set_halign(gtk::Align::End);let window_copy=window.clone();close.connect_clicked(move|_|{window_copy.close();});
    for widget in [note.upcast_ref::<gtk::Widget>(),license.upcast_ref(),close.upcast_ref()]{root.append(widget);}
    window.set_child(Some(&root));window.present();
}

fn build(app:&gtk::Application){
    if let Some(window)=app.windows().into_iter().find(|window|window.widget_name().as_str()=="shadow-messenger-main"){window.present();return;}
    if let Some(display)=gtk::gdk::Display::default(){let css=gtk::CssProvider::new();css.load_from_data(include_str!("style.css"));gtk::style_context_add_provider_for_display(&display,&css,gtk::STYLE_PROVIDER_PRIORITY_APPLICATION);}
    let (commands,updates)=worker::start();
    let window=gtk::ApplicationWindow::builder().application(app).title("Shadow Messenger").default_width(1180).default_height(760).build();
    window.set_widget_name("shadow-messenger-main");appearance::attach(&window);
    let signed_in=Rc::new(Cell::new(false));
    let chat=Rc::new(RefCell::new(None::<chat_ui::ChatWindow>));
    let selected=Rc::new(RefCell::new(None::<String>));
    let rooms=Rc::new(RefCell::new(Vec::<Connection>::new()));
    let buddies=Rc::new(RefCell::new(HashMap::<String,Buddy>::new()));
    let own_user=Rc::new(RefCell::new(String::new()));
    let own_name=Rc::new(RefCell::new(String::new()));
    let own_presence=Rc::new(Cell::new(Presence::Offline));
    let loaded=Rc::new(RefCell::new(HashSet::<String>::new()));
    let last_ids=Rc::new(RefCell::new(HashMap::<String,String>::new()));
    let account_label=Rc::new(RefCell::new("Not signed in".to_owned()));

    let conversation_views=Rc::new(RefCell::new(None::<conversations_ui::ConversationsView>));
    let security_views=Rc::new(RefCell::new(None::<security_ui::SecurityView>));
    let recovery_views=Rc::new(RefCell::new(None::<recovery_ui::RecoveryView>));
    let preferences=Rc::new(RefCell::new(None::<preferences_ui::Preferences>));
    let registration_views=Rc::new(RefCell::new(None::<registration_ui::RegistrationView>));

    let open_chat:Rc<dyn Fn(String,String)> = {
        let window=window.clone();let commands=commands.clone();let chat=chat.clone();let selected=selected.clone();let buddies=buddies.clone();let app=app.clone();let loaded=loaded.clone();let last_ids=last_ids.clone();
        let preferences=preferences.clone();let conversation_views=conversation_views.clone();let security_views=security_views.clone();let recovery_views=recovery_views.clone();let registration_views=registration_views.clone();let hooked=Rc::new(Cell::new(false));
        Rc::new(move|room_id,name|{
            app.withdraw_notification(&format!("shadow-messenger:{room_id}"));
            if selected.borrow().as_deref()==Some(room_id.as_str()){if let Some(view)=chat.borrow().as_ref(){view.present();}return;}
            let buddy= buddies.borrow().values().find(|buddy|buddy.room_id==room_id).map(presence_line);
            {
                let mut slot=chat.borrow_mut();
                let view=slot.get_or_insert_with(||chat_ui::ChatWindow::new(&app,commands.clone()));
                if !hooked.replace(true){
                    let preferences=preferences.clone();let conversation_views=conversation_views.clone();let security_views=security_views.clone();let recovery_views=recovery_views.clone();let registration_views=registration_views.clone();
                    let selected=selected.clone();
                    view.on_hide(move||{
                        // Closing a conversation dismisses it; the next open starts fresh.
                        *selected.borrow_mut()=None;
                        if let Some(view)=preferences.borrow().as_ref(){view.release_to_main();}
                        if let Some(view)=conversation_views.borrow().as_ref(){view.release_to_main();}
                        if let Some(view)=security_views.borrow().as_ref(){view.release_to_main();}
                        if let Some(view)=recovery_views.borrow().as_ref(){view.release_to_main();}
                        if let Some(view)=registration_views.borrow().as_ref(){view.release_to_main();}
                    });
                }
                view.open(&room_id,&name);
                if let Some(line)=buddy{view.set_peer_status(&line);}
            }
            *selected.borrow_mut()=Some(room_id.clone());
            loaded.borrow_mut().remove(&room_id);last_ids.borrow_mut().remove(&room_id);
            let _=commands.try_send(Command::OpenRoom(room_id));
        })
    };
    let notification_action=gtk::gio::SimpleAction::new("open-room",Some(glib::VariantTy::STRING));
    {
        let open=open_chat.clone();let rooms=rooms.clone();
        notification_action.connect_activate(move|_,parameter|{
            let Some(room_id)=parameter.and_then(|value|value.str()) else{return};
            let name=rooms.borrow().iter().find(|room|room.room_id==room_id).map(|room|room.name.clone()).unwrap_or_else(||room_id.to_owned());
            (open)(room_id.to_owned(),name);
        });
    }
    app.add_action(&notification_action);
    let open_conversations:Rc<dyn Fn()> = {
        let views=conversation_views.clone();let window=window.clone();let tx=commands.clone();let prefs=preferences.clone();let chat=chat.clone();
        Rc::new(move||{
            let mut views=views.borrow_mut();
            let view=views.get_or_insert_with(||conversations_ui::ConversationsView::new(&window,tx.clone()));
            let parent=raise_target(&window,&prefs,&chat);
            view.present_above(Some(&parent));let _=tx.try_send(Command::Invitations);
        })
    };
    let open_security:Rc<dyn Fn()> = {
        let views=security_views.clone();let window=window.clone();let tx=commands.clone();let prefs=preferences.clone();let chat=chat.clone();
        Rc::new(move||{
            let mut views=views.borrow_mut();
            let view=views.get_or_insert_with(||security_ui::SecurityView::new(&window,tx.clone()));
            let parent=raise_target(&window,&prefs,&chat);
            view.present_above(Some(&parent));let _=tx.try_send(Command::Devices);
        })
    };
    let open_recovery:Rc<dyn Fn()> = {
        let views=recovery_views.clone();let window=window.clone();let tx=commands.clone();let prefs=preferences.clone();let chat=chat.clone();
        Rc::new(move||{
            let mut views=views.borrow_mut();
            let view=views.get_or_insert_with(||recovery_ui::RecoveryView::new(&window,tx.clone()));
            let parent=raise_target(&window,&prefs,&chat);
            view.present_above(Some(&parent));let _=tx.try_send(Command::RecoveryStatus);
        })
    };
    let open_away:Rc<dyn Fn()> = {
        let window=window.clone();let prefs=preferences.clone();let chat=chat.clone();let tx=commands.clone();
        Rc::new(move||{let parent=raise_target(&window,&prefs,&chat);shell::away_dialog(&parent,&tx);})
    };
    let login=login_page(&commands);
    let open_registration:Rc<dyn Fn()> = {
        let views=registration_views.clone();let window=window.clone();let tx=commands.clone();let prefs=preferences.clone();let chat=chat.clone();let server=login.server.clone();
        Rc::new(move||{
            let mut views=views.borrow_mut();
            let view=views.get_or_insert_with(||registration_ui::RegistrationView::new(&window,tx.clone(),server.text().as_str()));
            view.set_homeserver(server.text().as_str());
            let parent=raise_target(&window,&prefs,&chat);
            view.present_above(Some(&parent));
        })
    };
    {let action=open_registration.clone();login.create_account.connect_clicked(move|_|action());}
    {let window=window.clone();let prefs=preferences.clone();let chat=chat.clone();login.help.connect_clicked(move|_|{let parent=raise_target(&window,&prefs,&chat);how_it_works(&parent);});}
    let logout:Rc<dyn Fn()> = {
        let tx=commands.clone();let views=recovery_views.clone();let status=login.status.clone();
        Rc::new(move||{
            if let Some(view)=views.borrow().as_ref(){if view.has_unsaved_key(){view.present();status.set_text("Save and confirm your recovery key before signing out.");return;}}
            let _=tx.try_send(Command::Logout);
        })
    };
    let open_preferences:Rc<dyn Fn()> = {
        let prefs=preferences.clone();let parent=window.clone();let chat=chat.clone();let security=open_security.clone();let recovery=open_recovery.clone();let logout=logout.clone();let app=app.clone();let account=account_label.clone();
        let test_notification:Rc<dyn Fn()>=Rc::new(move||{notify(&app,"test","Shadow Messenger","Notifications are working.",false);});
        let test_sound:Rc<dyn Fn()>=Rc::new(||sound::play("message"));
        Rc::new(move||{
            let mut slot=prefs.borrow_mut();
            let view=slot.get_or_insert_with(||preferences_ui::Preferences::new(&parent,preferences_ui::Actions{security:security.clone(),recovery:recovery.clone(),logout:logout.clone(),test_notification:test_notification.clone(),test_sound:test_sound.clone()}));
            let chat_window=chat_in_front(&chat);
            view.set_account(account.borrow().as_str());view.present_above(chat_window.as_ref(),"general");
        })
    };
    let open_avatar:Rc<dyn Fn()> = {
        let window=window.clone();let commands=commands.clone();
        Rc::new(move||{
            let chooser=gtk::FileChooserNative::new(Some("Choose a display picture"),Some(&window),gtk::FileChooserAction::Open,Some("Use picture"),Some("Cancel"));
            let filter=gtk::FileFilter::new();filter.set_name(Some("Pictures"));
            for mime in ["image/png","image/jpeg","image/webp","image/gif"]{filter.add_mime_type(mime);}
            chooser.add_filter(&filter);
            let commands=commands.clone();
            chooser.connect_response(move|chooser,response|{
                if response==gtk::ResponseType::Accept{
                    if let Some(path)=chooser.file().and_then(|file|file.path()){let _=commands.try_send(Command::SetAvatar{path:path.to_string_lossy().into_owned()});}
                }
                chooser.destroy();
            });
            chooser.show();
        })
    };
    let shell_actions=shell::Actions{open_chat:open_chat.clone(),conversations:open_conversations.clone(),security:open_security.clone(),recovery:open_recovery.clone(),preferences:open_preferences.clone(),away:open_away.clone(),logout:logout.clone(),avatar:open_avatar.clone()};
    let shell=shell::Shell::new(&commands,rooms.clone(),buddies.clone(),shell_actions);
    let login_logout=login.logout.clone();let logout_copy=logout.clone();login_logout.connect_clicked(move|_|logout_copy());
    let shell_logout=shell.logout.clone();let logout_copy=logout.clone();shell_logout.connect_clicked(move|_|logout_copy());

    let stack=gtk::Stack::new();stack.set_vexpand(true);stack.set_transition_type(gtk::StackTransitionType::Crossfade);
    stack.add_named(&login.root,Some("login"));stack.add_named(&shell.root,Some("shell"));stack.set_visible_child_name("login");
    let menu=gtk::gio::Menu::new();
    let file=gtk::gio::Menu::new();file.append(Some("Sign out"),Some("win.sign-out"));file.append(Some("Quit"),Some("win.quit"));menu.append_submenu(Some("File"),&file);
    let view=gtk::gio::Menu::new();view.append(Some("Preferences"),Some("win.preferences"));view.append(Some("Reload theme"),Some("win.reload-theme"));menu.append_submenu(Some("View"),&view);
    let connections=gtk::gio::Menu::new();connections.append(Some("New conversation"),Some("win.new-conversation"));connections.append(Some("Invitations"),Some("win.invitations"));menu.append_submenu(Some("Connections"),&connections);
    let tools=gtk::gio::Menu::new();tools.append(Some("Devices & security"),Some("win.security"));tools.append(Some("Account recovery"),Some("win.recovery"));menu.append_submenu(Some("Tools"),&tools);
    let help=gtk::gio::Menu::new();help.append(Some("How Shadow Messenger Works"),Some("win.how-it-works"));help.append(Some("About Shadow Messenger"),Some("win.about"));menu.append_submenu(Some("Help"),&help);
    let menubar=gtk::PopoverMenuBar::from_model(Some(&menu));menubar.add_css_class("messenger-menubar");
    let content=gtk::Box::new(gtk::Orientation::Vertical,0);content.append(&menubar);content.append(&stack);window.set_child(Some(&content));

    add_action(&window,"quit",{let window=window.clone();move||window.close()});
    add_action(&window,"reload-theme",||appearance::refresh_now());
    add_action(&window,"preferences",{let action=open_preferences.clone();move||action()});
    add_action(&window,"new-conversation",{let action=open_conversations.clone();move||action()});
    add_action(&window,"invitations",{let action=open_conversations.clone();move||action()});
    add_action(&window,"security",{let action=open_security.clone();move||action()});
    add_action(&window,"recovery",{let action=open_recovery.clone();move||action()});
    add_action(&window,"how-it-works",{let window=window.clone();let prefs=preferences.clone();let chat=chat.clone();move||{let parent=raise_target(&window,&prefs,&chat);how_it_works(&parent)}});
    add_action(&window,"about",{let window=window.clone();let prefs=preferences.clone();let chat=chat.clone();move||{let parent=raise_target(&window,&prefs,&chat);about(&parent)}});
    add_action(&window,"sign-out",{let action=logout.clone();move||action()});

    {let views=recovery_views.clone();window.connect_close_request(move|_|{if let Some(view)=views.borrow().as_ref(){if view.has_unsaved_key(){view.present();return glib::Propagation::Stop;}}glib::Propagation::Proceed});}
    let commands_close=commands.clone();let updates_close=updates.clone();window.connect_destroy(move|_|{commands_close.close();updates_close.close();});
    window.present();

    if settings::get("auto_restore",false){let _=commands.try_send(Command::Restore);}
    let timer_signed_in=signed_in.clone();let timer_commands=commands.clone();
    glib::timeout_add_seconds_local(30,move||{if timer_signed_in.get(){let _=timer_commands.try_send(Command::Buddies);}glib::ControlFlow::Continue});

    let stack_ui=stack;let login_ui=login;let shell_ui=shell;
    let chat_ui_state=chat;let selected_ui=selected;let rooms_ui=rooms;let buddies_ui=buddies;
    let own_user_ui=own_user;let own_name_ui=own_name;let own_presence_ui=own_presence;
    let signed_in_ui=signed_in;let loaded_ui=loaded;let last_ids_ui=last_ids;let account_label_ui=account_label;
    let preferences_ui_state=preferences;let registration_ui_state=registration_views;let conversation_views_ui=conversation_views;let security_views_ui=security_views;let recovery_views_ui=recovery_views;
    let open_chat_ui=open_chat;let commands_ui=commands.clone();let app_ui=app.clone();let window_ui=window.clone();
    glib::MainContext::default().spawn_local(async move {
        while let Ok(event)=updates.recv().await{
            match event{
                Event::Connected{user_id,display_name}=>{
                    signed_in_ui.set(true);*own_user_ui.borrow_mut()=user_id.clone();*own_name_ui.borrow_mut()=display_name.clone();
                    shell_ui.set_identity(&display_name,&user_id);shell_ui.set_notice("Connected. Choose a conversation or set a status.");
                    shell_ui.set_presence(Presence::Online,"");own_presence_ui.set(Presence::Online);
                    login_ui.status.set_text("");stack_ui.set_visible_child_name("shell");
                    if let Some(view)=registration_ui_state.borrow().as_ref(){view.succeeded();}
                    let label=if display_name.trim().is_empty(){user_id.clone()}else{format!("{display_name} ({user_id})")};
                    *account_label_ui.borrow_mut()=label.clone();if let Some(view)=preferences_ui_state.borrow().as_ref(){view.set_account(&label);}
                    let _=commands_ui.try_send(Command::Buddies);
                    if settings::get("presence_sounds",true){sound::play("sign-on");}
                }
                Event::Status{presence,message}=>{
                    own_presence_ui.set(presence);shell_ui.set_presence(presence,&message);
                }
                Event::Buddies{own_user,own_presence,own_message,buddies}=>{
                    own_presence_ui.set(own_presence);shell_ui.set_presence(own_presence,&own_message);shell_ui.set_buddies(buddies);
                    if let (Some(room),Some(view))=(selected_ui.borrow().clone(),chat_ui_state.borrow().as_ref()){
                        if let Some(buddy)=buddies_ui.borrow().values().find(|buddy|buddy.room_id==room){view.set_peer_status(&presence_line(buddy));}
                    }
                    if !own_user.is_empty(){*own_user_ui.borrow_mut()=own_user;}
                }
                Event::Rooms(rooms)=>{
                    shell_ui.set_rooms(rooms);let selected=selected_ui.borrow().clone();
                    if let Some(id)=selected{shell_ui.select(&id);}
                }
                Event::Invitations(invites)=>{
                    shell_ui.set_invitations(invites.len());
                    if let Some(view)=conversation_views_ui.borrow().as_ref(){view.invitations(invites);}
                }
                Event::ConversationAction(message)=>{
                    if let Some(view)=conversation_views_ui.borrow().as_ref(){view.action(&message);}
                    if let Some(view)=chat_ui_state.borrow().as_ref(){view.notice(&message);}
                    shell_ui.set_notice(&message);
                }
                Event::Avatar{bytes}=>{shell_ui.set_avatar(&bytes);}
                Event::ConversationCreated{room_id,message}=>{
                    if let Some(view)=conversation_views_ui.borrow().as_ref(){view.created(&message);}shell_ui.set_notice(&message);
                    if let Some(room)=rooms_ui.borrow().iter().find(|room|room.room_id==room_id).cloned(){(open_chat_ui)(room.room_id,room.name);}
                }
                Event::RecoveryStatus{message,can_create}=>{if let Some(view)=recovery_views_ui.borrow().as_ref(){view.status(&message,can_create);}}
                Event::RecoveryKey(key)=>{if let Some(view)=recovery_views_ui.borrow().as_ref(){view.created(key);}}
                Event::RecoveryRestored=>{if let Some(view)=recovery_views_ui.borrow().as_ref(){view.restored();}}
                Event::Devices{user_id,devices}=>{if let Some(view)=security_views_ui.borrow().as_ref(){view.devices(&user_id,devices);}}
                Event::Verification{flow_id,state}=>{
                    let mut views=security_views_ui.borrow_mut();
                    if views.is_none()&&matches!(state,verification::State::Requested{..}){
                        let view=security_ui::SecurityView::new(&window_ui,commands_ui.clone());
                        let parent=raise_target(&window_ui,&preferences_ui_state,&chat_ui_state);
                        view.present_above(Some(&parent));*views=Some(view);
                    }
                    if let Some(view)=views.as_ref(){view.verification(flow_id,state);}
                }
                Event::Typing{room_id,users}=>{
                    let own=own_user_ui.borrow().clone();let users=users.into_iter().filter(|user|user!=&own).collect::<Vec<_>>();
                    if let Some(view)=chat_ui_state.borrow().as_ref(){view.typing(&room_id,&users);}
                }
                Event::Timeline{room_id,messages}=>{
                    if selected_ui.borrow().as_deref()==Some(room_id.as_str()){if let Some(view)=chat_ui_state.borrow().as_ref(){view.messages(&room_id,&messages);}}
                    let Some(last)=messages.last() else{continue};
                    let first=loaded_ui.borrow_mut().insert(room_id.clone());
                    if first{continue;}
                    if last.own||!last.state.is_empty()||last.timestamp_ms<=0{continue;}
                    let previous=last_ids_ui.borrow_mut().insert(room_id.clone(),last.id.clone());
                    if previous.as_deref()==Some(last.id.as_str()){continue;}
                    let room_name=rooms_ui.borrow().iter().find(|room|room.room_id==room_id).map(|room|room.name.clone()).unwrap_or_else(||room_id.clone());
                    let sender=shadow_messenger_core::display_name(&last.sender);
                    let own_user_value=own_user_ui.borrow().clone();let own_name_value=own_name_ui.borrow().clone();
                    let mention=shadow_messenger_core::mentions(&last.body,&own_user_value,&own_name_value);
                    shell_ui.push_activity(&room_id,&room_name,&last.sender,&shadow_messenger_core::notification_body(&last.body),mention,&time_now());
                    if matches!(own_presence_ui.get(),Presence::DoNotDisturb|Presence::Invisible){continue;}
                    let focused=chat_ui_state.borrow().as_ref().is_some_and(|view|view.is_active()&&view.room_id().as_deref()==Some(room_id.as_str()));
                    if focused{continue;}
                    if settings::get("notifications",true){
                        let preview=if settings::get("notification_previews",true){format!("{}: {}",sender,shadow_messenger_core::notification_body(&last.body))}else{"New message".to_owned()};
                        let title=if mention{format!("{room_name} — mention")}else{room_name};
                        notify(&app_ui,&room_id,&title,&preview,mention);
                    }
                    if settings::get("notification_sounds",true){sound::play(if mention{"mention"}else{"message"});}
                }
                Event::RoomSecurity{room_id,encrypted}=>{if let Some(view)=chat_ui_state.borrow().as_ref(){view.security(&room_id,encrypted);}}
                Event::Queued{room_id,body}=>{if let Some(view)=chat_ui_state.borrow().as_ref(){view.queued(&room_id,&body);}}
                Event::SignedOut=>{
                    let was_signed_in=signed_in_ui.replace(false);
                    if was_signed_in&&settings::get("presence_sounds",true){sound::play("sign-off");}
                    stack_ui.set_visible_child_name("login");login_ui.status.set_text("No account connected. Choose a test account to continue development checks.");
                    login_ui.login.set_sensitive(login_ui.consent.is_active());login_ui.logout.set_sensitive(false);
                    if let Some(view)=registration_ui_state.borrow().as_ref(){view.signed_out();}
                    shell_ui.signed_out();shell_ui.set_notice("No account connected.");
                    if let Some(view)=chat_ui_state.borrow().as_ref(){view.signed_out();}*selected_ui.borrow_mut()=None;
                    if let Some(view)=conversation_views_ui.borrow().as_ref(){view.signed_out();}
                    if let Some(view)=security_views_ui.borrow().as_ref(){view.signed_out();}
                    if let Some(view)=recovery_views_ui.borrow().as_ref(){view.signed_out();}
                    if let Some(view)=preferences_ui_state.borrow().as_ref(){view.set_account("Not signed in");}
                    *account_label_ui.borrow_mut()="Not signed in".to_owned();loaded_ui.borrow_mut().clear();last_ids_ui.borrow_mut().clear();
                    own_user_ui.borrow_mut().clear();own_name_ui.borrow_mut().clear();own_presence_ui.set(Presence::Offline);
                }
                Event::Error(message)=>{
                    shell_ui.set_notice(&message);
                    if let Some(view)=chat_ui_state.borrow().as_ref(){view.error(&message);}
                    if let Some(view)=conversation_views_ui.borrow().as_ref(){view.error(&message);}
                    if let Some(view)=recovery_views_ui.borrow().as_ref(){view.error(&message);}
                    if let Some(view)=security_views_ui.borrow().as_ref(){view.error(&message);}
                    if stack_ui.visible_child_name().as_deref()==Some("login"){
                        login_ui.status.set_text(&message);login_ui.login.set_sensitive(login_ui.consent.is_active());
                        if let Some(view)=registration_ui_state.borrow().as_ref(){view.failed(&message);}
                    }
                }
            }
        }
    });
}
