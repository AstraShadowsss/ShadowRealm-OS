mod matrix;
use gtk::{glib,prelude::*};

fn main() -> glib::ExitCode {
    let app=gtk::Application::builder().application_id("org.shadowrealm_os.Messenger.Development").build();
    app.connect_activate(build);
    app.run()
}

fn build(app:&gtk::Application) {
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
    let status=gtk::Label::new(Some("Account sign-in is not enabled in this shell until the secure-storage and live-account tests pass."));status.set_wrap(true);status.set_xalign(0.0);content.append(&status);
    let validate=gtk::Button::with_label("Check server address");
    let status_copy=status.clone();validate.connect_clicked(move |_| {
        status_copy.set_text(match shadow_messenger_core::validate_homeserver(server.text().as_str()) {Ok(_)=>"Server address accepted. No connection was made.",Err(message)=>message});
    });content.append(&validate);
    split.set_end_child(Some(&content));shell.append(&split);window.set_child(Some(&shell));window.present();
}
