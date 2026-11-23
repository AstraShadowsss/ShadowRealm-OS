mod matrix;
mod vault;
mod persistence;
mod worker;
use gtk::{glib,prelude::*};

fn main() -> glib::ExitCode {
    let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.Development").build();
    app.connect_activate(build);
    app.run()
}

fn build(app:&gtk::Application) {
    let (commands,updates)=worker::start();
    let window=gtk::ApplicationWindow::builder().application(app).title("Shadow Messenger — Development")
        .default_width(980).default_height(650).build();
    let shell=gtk::Box::new(gtk::Orientation::Vertical,18);
    shell.set_margin_top(24);shell.set_margin_bottom(24);shell.set_margin_start(24);shell.set_margin_end(24);
    let title=gtk::Label::new(Some("Shadow Messenger"));title.add_css_class("title-1");title.set_xalign(0.0);shell.append(&title);
    let notice=gtk::Label::new(Some("Development build. Secure account storage, device verification and recovery must be completed before personal conversations."));
    notice.set_wrap(true);notice.set_xalign(0.0);shell.append(&notice);
    let split=gtk::Paned::new(gtk::Orientation::Horizontal);split.set_vexpand(true);split.set_position(270);
    let sidebar=gtk::Box::new(gtk::Orientation::Vertical,12);
    let label=gtk::Label::new(Some("Connections"));label.set_xalign(0.0);label.add_css_class("heading");sidebar.append(&label);
    let search=gtk::SearchEntry::new();search.set_placeholder_text(Some("Search connections"));sidebar.append(&search);
    let list=gtk::ListBox::new();list.set_vexpand(true);sidebar.append(&list);split.set_start_child(Some(&sidebar));
    let content=gtk::Box::new(gtk::Orientation::Vertical,12);content.set_margin_start(18);
    let empty=gtk::Label::new(Some("No account connected"));empty.set_vexpand(true);content.append(&empty);
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
        let tx=commands.clone();let status_copy=status.clone();button.connect_clicked(move |_|{
            let command=match kind{0=>worker::Command::Restore,1=>worker::Command::Refresh,_=>worker::Command::Logout};
            if tx.try_send(command).is_ok(){status_copy.set_text("Working...");}else{status_copy.set_text("An account request is already pending.");}
        });
    }
    gtk::glib::MainContext::default().spawn_local(async move {
        while let Ok(event)=updates.recv().await{
            match event{
                worker::Event::Connected=>{empty.set_text("Connected. Conversation timelines are being implemented.");refresh.set_sensitive(true);logout.set_sensitive(true);consent.set_sensitive(false);login.set_sensitive(false);status.set_text("Connected. Loading joined conversations...");}
                worker::Event::Rooms(rooms)=>{
                    while let Some(child)=list.first_child(){list.remove(&child);}
                    let count=rooms.len();for room in rooms{let label=gtk::Label::new(Some(&room.name));label.set_xalign(0.0);label.set_margin_top(8);label.set_margin_bottom(8);list.append(&label);}
                    status.set_text(&format!("{count} joined conversations. Timeline, verification and recovery work remains unfinished."));
                }
                worker::Event::SignedOut=>{while let Some(child)=list.first_child(){list.remove(&child);}empty.set_text("No account connected");refresh.set_sensitive(false);logout.set_sensitive(false);consent.set_sensitive(true);login.set_sensitive(consent.is_active());status.set_text("No account connected. Choose a test account to continue development checks.");}
                worker::Event::Error(message)=>{status.set_text(&message);if consent.is_sensitive(){login.set_sensitive(consent.is_active());}}
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
        let window=app.windows().into_iter().next().unwrap();let mut widgets=Vec::new();descendants(window.upcast_ref(),&mut widgets);
        let server=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Entry>())
            .find(|e|e.placeholder_text().as_deref()==Some("HTTPS homeserver")).unwrap();
        server.set_text("http://invalid.example");
        let button=widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Button>())
            .find(|b|b.label().as_deref()==Some("Check server address")).unwrap();
        button.emit_clicked();
        assert!(widgets.iter().filter_map(|w|w.downcast_ref::<gtk::Label>())
            .any(|label|label.text().contains("Use an HTTPS homeserver address.")));
        window.close();
    }
}
